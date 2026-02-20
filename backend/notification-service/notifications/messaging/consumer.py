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

# Agregar directorio base al path
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, base_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notification_service.settings")
django.setup()

import pika
import json
import logging
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
    """Procesa un evento ``ticket.created`` creando la notificación vía ORM.

    Ruta backward-compatible que persiste directamente a través del modelo
    Django. Se utiliza para ``ticket.created`` y cualquier evento que no
    tenga un handler dedicado.

    Args:
        data: Payload del evento ya deserializado como diccionario.
    """
    ticket_id = data.get('ticket_id')
    Notification.objects.create(
        ticket_id=str(ticket_id),
        message=f"Ticket {ticket_id} creado",
    )
    logger.info("Notification created for ticket %s", ticket_id)


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


def start_consuming():
    """Inicia el consumidor RabbitMQ para el servicio de notificaciones.

    Establece una conexión bloqueante con RabbitMQ, declara el exchange
    de tipo fanout y la cola durable para notificaciones, vincula la cola
    al exchange y comienza a consumir mensajes de forma indefinida.

    La función es bloqueante: una vez invocada, el proceso permanece
    escuchando mensajes hasta que se interrumpa manualmente o se pierda
    la conexión.

    Raises:
        pika.exceptions.AMQPConnectionError: Si no se puede conectar
            al servidor RabbitMQ en ``RABBITMQ_HOST``.

    Note:
        No implementa lógica de reconexión automática. Si la conexión
        se pierde, el proceso terminará con una excepción.
    """
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    
    # Declarar exchange
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)
    
    # Crear cola exclusiva para notificaciones
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Vincular cola al exchange
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print(f'[NOTIFICATION] Consumer started, waiting messages on queue "{QUEUE_NAME}"...')
    channel.start_consuming()


if __name__ == '__main__':
    start_consuming()