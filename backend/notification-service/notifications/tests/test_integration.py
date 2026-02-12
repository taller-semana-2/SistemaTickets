"""
Tests de integración.
Prueban la integración con RabbitMQ y el flujo completo del sistema.
"""

import json
import pika
import time
from django.test import TestCase
from notifications.models import Notification

RABBIT_HOST = 'rabbitmq'
QUEUE_NAME = 'ticket_created'


class NotificationIntegrationTests(TestCase):
    """Tests de integración con RabbitMQ."""
    
    def publish_message(self, ticket_id):
        """Helper para publicar un mensaje en RabbitMQ."""
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        # Asegurar cola limpia para evitar mensajes residuales de otras pruebas
        channel.queue_purge(queue=QUEUE_NAME)
        body = json.dumps({'ticket_id': ticket_id})
        channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=body)
        connection.close()

    def test_consumer_creates_notification(self):
        """El consumer crea una notificación al recibir un mensaje."""
        ticket_id = 'NOTIF-1'
        # publicar mensaje
        self.publish_message(ticket_id)

        # consumir manualmente con el callback importado para evitar depender del worker
        from notifications.messaging import consumer
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        method_frame, header_frame, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=False)
        retries = 5
        while method_frame is None and retries > 0:
            time.sleep(0.5)
            method_frame, header_frame, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=False)
            retries -= 1

        self.assertIsNotNone(method_frame)
        consumer.callback(channel, method_frame, header_frame, body)
        time.sleep(0.1)
        self.assertTrue(Notification.objects.filter(ticket_id=ticket_id).exists())
        connection.close()


class NotificationModelTests(TestCase):
    """Tests del modelo Django básico."""
    
    def test_notification_model(self):
        """Crear una notificación y verificar su representación."""
        n = Notification.objects.create(ticket_id='T-1', message='Hola')
        self.assertEqual(str(n).startswith('Notification for T-1'), True)
