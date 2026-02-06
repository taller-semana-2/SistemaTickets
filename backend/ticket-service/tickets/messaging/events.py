# backend/ticket-service/messaging/events.py
import pika
import json

RABBIT_HOST = "rabbitmq"
EXCHANGE_NAME = "ticket_events"

def publish_ticket_created(ticket_id):
    """Publica un evento ticket.created en RabbitMQ usando exchange fanout"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()
    
    # Crear exchange fanout (broadcast a todas las colas suscritas)
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='fanout', durable=True)
    
    # Mensaje JSON con los datos del ticket
    message = json.dumps({"ticket_id": ticket_id})
    
    # Publicar al exchange (no a una cola específica)
    channel.basic_publish(
        exchange=EXCHANGE_NAME,
        routing_key='',  # Ignorado en fanout
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    connection.close()
    print(f"Evento ticket.created publicado al exchange: {ticket_id}")
