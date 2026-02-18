"""Consumidor RabbitMQ para el servicio de notificaciones.

Este módulo implementa un consumidor standalone que escucha eventos
publicados en un exchange fanout de RabbitMQ y crea registros de
notificación en la base de datos del notification-service.

Variables de entorno requeridas:
    RABBITMQ_HOST: Hostname del servidor RabbitMQ (ej. 'localhost', 'rabbitmq').
    RABBITMQ_EXCHANGE_NAME: Nombre del exchange fanout donde se publican eventos.
    RABBITMQ_QUEUE_NOTIFICATION: Nombre de la cola exclusiva para este consumidor.

Ejemplo de uso::

    $ python -m notifications.messaging.consumer

Formato esperado del mensaje JSON::

    {
        "ticket_id": "<id_del_ticket>"
    }
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
from notifications.models import Notification

# Configuración RabbitMQ desde variables de entorno
RABBIT_HOST = os.environ.get('RABBITMQ_HOST')
EXCHANGE_NAME = os.environ.get('RABBITMQ_EXCHANGE_NAME')
QUEUE_NAME = os.environ.get('RABBITMQ_QUEUE_NOTIFICATION')


def callback(ch, method, properties, body):
    """Procesa un mensaje entrante de RabbitMQ y crea una notificación.

    Deserializa el cuerpo del mensaje como JSON, extrae el ``ticket_id``
    y persiste un nuevo registro :class:`~notifications.models.Notification`
    en la base de datos. Una vez procesado, envía un ACK al broker para
    confirmar la recepción exitosa del mensaje.

    Args:
        ch (pika.channel.Channel): Canal de comunicación con RabbitMQ.
        method (pika.spec.Basic.Deliver): Metadatos de entrega del mensaje,
            incluyendo ``delivery_tag`` necesario para el ACK.
        properties (pika.spec.BasicProperties): Propiedades AMQP del mensaje
            (content_type, headers, etc.).
        body (bytes): Cuerpo del mensaje en formato JSON. Debe contener
            la clave ``ticket_id`` con el identificador del ticket.

    Note:
        No implementa manejo de errores para mensajes malformados ni
        fallos de escritura en BD. Un error no capturado impedirá el ACK
        y el mensaje quedará pendiente en la cola.
    """
    data = json.loads(body)
    ticket_id = data.get('ticket_id')
    # Crear una notificación básica en la BD
    Notification.objects.create(ticket_id=str(ticket_id), message=f"Ticket {ticket_id} creado")
    print(f"[NOTIFICATION] Notification created for ticket {ticket_id}")
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