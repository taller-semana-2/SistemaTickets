
import os
import sys
import django

# Agregar directorio base al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assessment_service.settings")
django.setup()

import pika
import json
from assignments.tasks import process_ticket  # Celery task

# Configuración RabbitMQ
RABBIT_HOST = 'rabbitmq'
EXCHANGE_NAME = 'ticket_events'
QUEUE_NAME = 'assignment_queue'  # Cola exclusiva para este servicio

def callback(ch, method, properties, body):
    """Se llama cada vez que llega un mensaje a la cola"""
    data = json.loads(body)
    ticket_id = data.get("ticket_id")
    
    # Procesar en segundo plano con Celery
    process_ticket.delay(ticket_id)
    
    print(f"[ASSIGNMENT] Mensaje recibido y enviado a Celery: {ticket_id}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consuming():
    """Función que inicia el consumidor de RabbitMQ"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST)
    )
    channel = connection.channel()
    
    # Declarar exchange
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)
    
    # Crear cola exclusiva para este servicio
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Vincular cola al exchange
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    print("[ASSIGNMENT] Esperando eventos ticket.created...")
    channel.start_consuming()

if __name__ == "__main__":
    start_consuming()

