# backend/ticket-service/messaging/events.py
import pika
import json

RABBIT_HOST = "rabbitmq"  # Nombre del servicio RabbitMQ en docker-compose
QUEUE_NAME = "ticket_created"

def publish_ticket_created(ticket_id):
    """Publica un evento ticket.created en RabbitMQ"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    
    # Crear la cola si no existe
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Mensaje JSON con los datos mínimos del ticket
    message = json.dumps({"ticket_id": ticket_id})
    
    # Publicar mensaje persistente
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)  # Hace que el mensaje sea persistente
    )
    
    connection.close()
    print(f"Evento ticket.created publicado: {ticket_id}")
