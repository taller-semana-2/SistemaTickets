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
from notifications.models import Notification

# Configuración RabbitMQ desde variables de entorno
RABBIT_HOST = os.environ.get('RABBITMQ_HOST')
EXCHANGE_NAME = os.environ.get('RABBITMQ_EXCHANGE_NAME')
QUEUE_NAME = os.environ.get('RABBITMQ_QUEUE_NOTIFICATION')


def callback(ch, method, properties, body):
    data = json.loads(body)
    ticket_id = data.get('ticket_id')
    # Crear una notificación básica en la BD
    Notification.objects.create(ticket_id=str(ticket_id), message=f"Ticket {ticket_id} creado")
    print(f"[NOTIFICATION] Notification created for ticket {ticket_id}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consuming():
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