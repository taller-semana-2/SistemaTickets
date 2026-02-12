"""
Consumidor RabbitMQ refactorizado.
Usa el adaptador de eventos en lugar de lógica acoplada.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assessment_service.settings")
django.setup()

import pika
import json
from assignments.tasks import process_ticket_event

RABBIT_HOST = os.environ.get('RABBITMQ_HOST')
EXCHANGE_NAME = os.environ.get('RABBITMQ_EXCHANGE_NAME')
QUEUE_NAME = os.environ.get('RABBITMQ_QUEUE_ASSIGNMENT')


def callback(ch, method, properties, body):
    """
    Callback cuando llega un mensaje.
    Delega el procesamiento a Celery.
    """
    try:
        event_data = json.loads(body)
        process_ticket_event.delay(event_data)
        
        print(f"[ASSIGNMENT] Evento recibido y enviado a Celery: {event_data}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[ASSIGNMENT] Error procesando mensaje: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consuming():
    """Inicia el consumidor de RabbitMQ"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST)
    )
    channel = connection.channel()
    
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print(f"[ASSIGNMENT] Esperando eventos en cola '{QUEUE_NAME}'...")
    channel.start_consuming()


if __name__ == "__main__":
    start_consuming()
