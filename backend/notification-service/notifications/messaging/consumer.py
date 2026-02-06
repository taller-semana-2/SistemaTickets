import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notification_service.settings")
django.setup()

import pika
import json
from notifications.models import Notification

RABBIT_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
QUEUE_NAME = 'ticket_created'


def callback(ch, method, properties, body):
    data = json.loads(body)
    ticket_id = data.get('ticket_id')
    # Crear una notificación básica en la BD
    Notification.objects.create(ticket_id=str(ticket_id), message=f"Ticket {ticket_id} creado")
    print(f"Notification created for ticket {ticket_id}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consuming():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print('Notification consumer started, waiting messages...')
    channel.start_consuming()


if __name__ == '__main__':
    start_consuming()
