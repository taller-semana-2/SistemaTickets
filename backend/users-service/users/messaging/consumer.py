"""
messaging/consumer.py

🎯 PROPÓSITO:
Consume eventos de RabbitMQ publicados por otros microservicios.

Consumer implementado siguiendo el patrón de notification-service y assessment-service.
Escucha eventos del exchange ticket_events y procesa notificaciones relevantes para usuarios.
"""
import os
import sys
import django

# Agregar directorio base al path
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, base_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "user_service.settings")
django.setup()

import pika
import json

# Configuración RabbitMQ desde variables de entorno
RABBIT_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
EXCHANGE_NAME = os.environ.get('RABBITMQ_EXCHANGE_NAME', 'ticket_events')
QUEUE_NAME = os.environ.get('RABBITMQ_QUEUE_USERS', 'users_queue')


def callback(ch, method, properties, body):
    """
    Procesa eventos recibidos de RabbitMQ.
    
    Por ahora solo imprime los eventos. Cuando se implementen los casos de uso,
    aquí se llamarán los handlers correspondientes.
    """
    try:
        data = json.loads(body)
        ticket_id = data.get('ticket_id')
        event_type = data.get('event_type', 'unknown')
        
        print(f"[USERS] Evento recibido: {event_type} para ticket {ticket_id}")
        print(f"[USERS] Datos: {data}")
        
        # TODO: Implementar handlers cuando se completen los casos de uso
        # Ejemplo: actualizar estadísticas de usuario, notificar cambios, etc.
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        print(f"[USERS ERROR] Error procesando evento: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consuming():
    """Inicia el consumidor de RabbitMQ"""
    print(f"[USERS] Conectando a RabbitMQ en {RABBIT_HOST}...")
    
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBIT_HOST)
    )
    channel = connection.channel()
    
    # Declarar exchange (debe coincidir con el de ticket-service)
    channel.exchange_declare(
        exchange=EXCHANGE_NAME, 
        exchange_type='fanout', 
        durable=True
    )
    
    # Crear cola exclusiva para users-service
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    # Vincular cola al exchange
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
    
    print(f'[USERS] Consumer iniciado, esperando mensajes en cola "{QUEUE_NAME}"...')
    print(f'[USERS] Exchange: {EXCHANGE_NAME}')
    
    channel.start_consuming()


if __name__ == '__main__':
    start_consuming()
