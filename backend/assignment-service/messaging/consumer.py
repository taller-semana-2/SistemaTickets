"""Consumidor RabbitMQ para el servicio de asignaciones.

Escucha eventos publicados en un exchange fanout de RabbitMQ y delega
el procesamiento a Celery.  Incluye:

- **Dead Letter Queue (DLQ):** Los mensajes que fallan en el procesamiento
  son rechazados (``basic_nack(requeue=False)``) y enrutados automáticamente
  a una cola de dead-letter vía un Dead Letter Exchange (DLX) para
  inspección o reprocesamiento posterior.
- **Reconexión automática:** Backoff exponencial configurable ante pérdida
  de conexión con el broker.

Variables de entorno requeridas:
    RABBITMQ_HOST, RABBITMQ_EXCHANGE_NAME, RABBITMQ_QUEUE_ASSIGNMENT
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assessment_service.settings")
django.setup()

import pika
import json

from typing import Any

from assignments.tasks import process_ticket_event
import time
import logging

logger = logging.getLogger(__name__)


RABBIT_HOST = os.environ.get('RABBITMQ_HOST')
EXCHANGE_NAME = os.environ.get('RABBITMQ_EXCHANGE_NAME')
QUEUE_NAME = os.environ.get('RABBITMQ_QUEUE_ASSIGNMENT')

# Reconnection configuration
INITIAL_RETRY_DELAY: int = int(os.environ.get('RABBITMQ_INITIAL_RETRY_DELAY', '1'))
MAX_RETRY_DELAY: int = int(os.environ.get('RABBITMQ_MAX_RETRY_DELAY', '60'))
RETRY_BACKOFF_FACTOR: int = int(os.environ.get('RABBITMQ_RETRY_BACKOFF_FACTOR', '2'))
MAX_RETRIES: int = int(os.environ.get('RABBITMQ_MAX_RETRIES', '0'))  # 0 = infinite

# Dead Letter Queue naming suffixes
DLX_SUFFIX: str = ".dlx"
DLQ_SUFFIX: str = ".dlq"
DLQ_ROUTING_KEY_SUFFIX: str = ".dead"



def callback(ch, method, properties, body):
    """
    Callback cuando llega un mensaje.
    Delega el procesamiento a Celery.
    """
    try:
        event_data = json.loads(body)
        process_ticket_event.delay(event_data)
        logger.info("Event received and sent to Celery: %s", event_data)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error("Error processing message: %s", e)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)



def _setup_dead_letter_queue(channel: Any, queue_name: str) -> dict[str, str]:
    """Declare the Dead Letter Exchange (DLX) and Dead Letter Queue (DLQ).

    Creates a direct DLX exchange, a durable DLQ, and binds them together.
    Returns the ``arguments`` dict to pass to the main queue's
    ``queue_declare`` so that rejected messages are routed to the DLQ.

    Args:
        channel: The pika channel to declare resources on.
        queue_name: Name of the main queue (used to derive DLQ names).

    Returns:
        Dict with ``x-dead-letter-exchange`` and ``x-dead-letter-routing-key``
        keys, ready to be passed as ``arguments`` to ``queue_declare``.
    """
    dlx_name: str = f"{queue_name}{DLX_SUFFIX}"
    dlq_name: str = f"{queue_name}{DLQ_SUFFIX}"
    dlq_routing_key: str = f"{queue_name}{DLQ_ROUTING_KEY_SUFFIX}"

    channel.exchange_declare(
        exchange=dlx_name, exchange_type='direct', durable=True,
    )
    logger.info("Dead Letter Exchange declared: %s", dlx_name)

    channel.queue_declare(queue=dlq_name, durable=True)
    logger.info("Dead Letter Queue declared: %s", dlq_name)

    channel.queue_bind(
        queue=dlq_name, exchange=dlx_name, routing_key=dlq_routing_key,
    )
    logger.info(
        "DLQ bound to DLX: %s -> %s (routing_key=%s)",
        dlq_name, dlx_name, dlq_routing_key,
    )

    return {
        'x-dead-letter-exchange': dlx_name,
        'x-dead-letter-routing-key': dlq_routing_key,
    }


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
    """Start the RabbitMQ consumer for the assignment service with auto-reconnection.

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

            channel.exchange_declare(
                exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True,
            )

            # Dead Letter Exchange / Queue setup
            dlq_args = _setup_dead_letter_queue(channel, QUEUE_NAME)

            channel.queue_declare(
                queue=QUEUE_NAME,
                durable=True,
                arguments=dlq_args,
            )
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
                "Consumer started, waiting for messages on queue '%s'...",
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


if __name__ == "__main__":
    start_consuming()
