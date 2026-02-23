"""Consumidor RabbitMQ para el servicio de notificaciones.

Este módulo implementa un consumidor standalone que escucha eventos
publicados en un exchange fanout de RabbitMQ y crea registros de
notificación en la base de datos del notification-service.

Eventos soportados:
    - ``ticket.response_added``: Delegado a
      :class:`~notifications.application.use_cases.CreateNotificationFromResponseUseCase`.
    - ``ticket.created`` (y cualquier otro): Creación directa vía ORM
      (backward-compatible).

Variables de entorno requeridas:
    RABBITMQ_HOST: Hostname del servidor RabbitMQ (ej. 'localhost', 'rabbitmq').
    RABBITMQ_EXCHANGE_NAME: Nombre del exchange fanout donde se publican eventos.
    RABBITMQ_QUEUE_NOTIFICATION: Nombre de la cola exclusiva para este consumidor.

Ejemplo de uso::

    $ python -m notifications.messaging.consumer
"""

import os
import sys
import django
import logging
import time

# Agregar directorio base al path
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, base_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notification_service.settings")
django.setup()

import pika
import json
from notifications.models import Notification
from notifications.application.use_cases import (
    CreateNotificationFromResponseUseCase,
    CreateNotificationFromResponseCommand,
)
from notifications.infrastructure.repository import DjangoNotificationRepository
from notifications.domain.exceptions import InvalidEventSchema

logger = logging.getLogger(__name__)

# Configuración RabbitMQ desde variables de entorno
RABBIT_HOST = os.environ.get('RABBITMQ_HOST')
EXCHANGE_NAME = os.environ.get('RABBITMQ_EXCHANGE_NAME')
QUEUE_NAME = os.environ.get('RABBITMQ_QUEUE_NOTIFICATION')

# Reconnection configuration
INITIAL_RETRY_DELAY: int = int(os.environ.get('RABBITMQ_INITIAL_RETRY_DELAY', '1'))
MAX_RETRY_DELAY: int = int(os.environ.get('RABBITMQ_MAX_RETRY_DELAY', '60'))
RETRY_BACKOFF_FACTOR: int = int(os.environ.get('RABBITMQ_RETRY_BACKOFF_FACTOR', '2'))
MAX_RETRIES: int = int(os.environ.get('RABBITMQ_MAX_RETRIES', '0'))  # 0 = infinite

def _handle_response_added(data: dict) -> None:
    """Procesa un evento ``ticket.response_added`` mediante el caso de uso.

    Crea un :class:`CreateNotificationFromResponseCommand` a partir del
    payload del evento y lo ejecuta a través del
    :class:`CreateNotificationFromResponseUseCase`, que valida el schema,
    garantiza idempotencia y persiste la notificación.

    Args:
        data: Payload del evento ya deserializado como diccionario.

    Raises:
        InvalidEventSchema: Si el evento carece de campos obligatorios.
        Exception: Cualquier error inesperado durante la ejecución.
    """
    repository = DjangoNotificationRepository()
    use_case = CreateNotificationFromResponseUseCase(repository=repository)
    command = CreateNotificationFromResponseCommand(
        event_type=data.get('event_type'),
        ticket_id=data.get('ticket_id'),
        response_id=data.get('response_id'),
        admin_id=data.get('admin_id'),
        response_text=data.get('response_text'),
        user_id=data.get('user_id'),
        timestamp=data.get('timestamp'),
    )
    use_case.execute(command)
    logger.info("Notification created for response on ticket %s", data.get('ticket_id'))


def _handle_ticket_created(data: dict) -> None:
    """Procesa un evento o fallback creando la notificación vía ORM.

    Interpreta el tipo de evento y construye un mensaje amigable.
    """
    ticket_id = data.get('ticket_id')
    event_type = data.get('event_type', '')
    
    if event_type == 'ticket.status_changed':
        message = f"El estado del Ticket #{ticket_id} cambió a {data.get('new_status', 'desconocido')}"
    elif event_type == 'ticket.priority_changed':
        message = f"La prioridad del Ticket #{ticket_id} cambió a {data.get('new_priority', 'desconocida')}"
    elif event_type == 'ticket.created':
        title = data.get('title', '')
        message = f"Nuevo Ticket #{ticket_id} creado: {title}"
    else:
        # Fallback genérico para eventos futuros o desconocidos
        message = f"Ticket #{ticket_id} actualizado ({event_type})"

    Notification.objects.create(
        ticket_id=str(ticket_id),
        message=message,
    )
    logger.info("Notification created for ticket %s: %s", ticket_id, message)


def callback(ch, method, properties, body):
    """Dispatcher principal: enruta mensajes RabbitMQ al handler correcto.

    Deserializa el cuerpo del mensaje como JSON, inspecciona el campo
    ``event_type`` y delega al handler correspondiente. Siempre envía
    ACK al broker para confirmar la recepción, incluso si el procesamiento
    falla (evita redelivery infinito de mensajes inválidos).

    Args:
        ch (pika.channel.Channel): Canal de comunicación con RabbitMQ.
        method (pika.spec.Basic.Deliver): Metadatos de entrega del mensaje,
            incluyendo ``delivery_tag`` necesario para el ACK.
        properties (pika.spec.BasicProperties): Propiedades AMQP del mensaje
            (content_type, headers, etc.).
        body (bytes): Cuerpo del mensaje en formato JSON.
    """
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.error("Failed to decode message body: %s", exc)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    event_type = data.get('event_type', '')

    try:
        if event_type == 'ticket.response_added':
            _handle_response_added(data)
        else:
            _handle_ticket_created(data)
    except InvalidEventSchema as exc:
        logger.error("Invalid event schema for %s: %s", event_type, exc)
    except Exception as exc:
        logger.error("Error processing event %s: %s", event_type, exc)
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def _safe_close(connection: pika.BlockingConnection) -> None:
    """Attempt to close the RabbitMQ connection gracefully.

    Silently handles any exception during close to avoid masking
    the original error that triggered the reconnection.

    Args:
        connection: The pika BlockingConnection to close.
    """
    try:
        if connection and connection.is_open:
            connection.close()
    except Exception:
        pass

def start_consuming() -> None:
    """Start the RabbitMQ consumer for the notification service with auto-reconnection.

    Establishes a blocking connection to RabbitMQ, declares the fanout
    exchange and durable queue, and begins consuming messages indefinitely.

    If the connection is lost, the consumer automatically retries with
    exponential backoff. The delay between retries follows the formula:

        delay = min(INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** attempt), MAX_RETRY_DELAY)

    Configuration is read from environment variables:
        - RABBITMQ_INITIAL_RETRY_DELAY (default: 1)
        - RABBITMQ_MAX_RETRY_DELAY (default: 60)
        - RABBITMQ_RETRY_BACKOFF_FACTOR (default: 2)
        - RABBITMQ_MAX_RETRIES (default: 0, meaning infinite)

    Raises:
        SystemExit: If MAX_RETRIES > 0 and all retries are exhausted.
    """
    connection = None
    attempt = 0

    while True:
        try:
            logger.info("Connecting to RabbitMQ at %s...", RABBIT_HOST)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST)
            )
            channel = connection.channel()

            # Declare exchange
            channel.exchange_declare(
                exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True
            )

            # Create durable queue for notifications
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            # Bind queue to exchange
            channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)

            channel.basic_consume(
                queue=QUEUE_NAME, on_message_callback=callback
            )

            if attempt > 0:
                logger.info(
                    "Successfully reconnected to RabbitMQ after %d attempt(s).",
                    attempt,
                )
            logger.info(
                'Consumer started, waiting for messages on queue "%s"...',
                QUEUE_NAME,
            )
            attempt = 0  # Reset on successful connection
            channel.start_consuming()

        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.StreamLostError,
            pika.exceptions.ConnectionClosedByBroker,
            ConnectionResetError,
        ) as exc:
            attempt += 1
            delay = min(
                INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** attempt),
                MAX_RETRY_DELAY,
            )
            logger.warning(
                "Connection lost (%s). Reconnection attempt %d in %.1fs...",
                exc,
                attempt,
                delay,
            )
            _safe_close(connection)
            time.sleep(delay)

            if MAX_RETRIES > 0 and attempt >= MAX_RETRIES:
                logger.critical(
                    "Max reconnection attempts (%d) reached. Shutting down.",
                    MAX_RETRIES,
                )
                sys.exit(1)

        except KeyboardInterrupt:
            logger.info("Consumer stopped by user.")
            _safe_close(connection)
            break

        except Exception as exc:
            attempt += 1
            delay = min(
                INITIAL_RETRY_DELAY * (RETRY_BACKOFF_FACTOR ** attempt),
                MAX_RETRY_DELAY,
            )
            logger.error(
                "Unexpected error (%s). Reconnection attempt %d in %.1fs...",
                exc,
                attempt,
                delay,
            )
            _safe_close(connection)
            time.sleep(delay)

            if MAX_RETRIES > 0 and attempt >= MAX_RETRIES:
                logger.critical(
                    "Max reconnection attempts (%d) reached. Shutting down.",
                    MAX_RETRIES,
                )
                sys.exit(1)

if __name__ == '__main__':
    start_consuming()