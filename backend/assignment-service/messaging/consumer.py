
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assessment_service.settings")
django.setup()

import pika
import json
from assignments.tasks import process_ticket  # Celery task

# Configuración RabbitMQ
RABBIT_HOST = 'rabbitmq'  # nombre del servicio en docker-compose
QUEUE_NAME = 'ticket_created'

def callback(ch, method, properties, body):
    """Se llama cada vez que llega un mensaje a la cola"""
    data = json.loads(body)
    ticket_id = data.get("ticket_id")
    
    # Procesar en segundo plano con Celery
    process_ticket.delay(ticket_id)
    
    print(f"Mensaje recibido y enviado a Celery: {ticket_id}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consuming():
    """Función que inicia el consumidor de RabbitMQ"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST)
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print("Esperando eventos ticket.created...")
    channel.start_consuming()

if __name__ == "__main__":
    start_consuming()

