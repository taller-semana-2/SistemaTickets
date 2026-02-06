import json
import time

import pika
from django.test import TestCase, override_settings

from assignments.models import TicketAssignment
from assessment_service import settings as project_settings


QUEUE_NAME = 'ticket_created'
RABBIT_HOST = 'rabbitmq'


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AssignmentIntegrationTests(TestCase):
    def setUp(self):
        # Ensure Celery runs tasks eagerly in this test
        try:
            from celery import current_app
            current_app.conf.task_always_eager = True
            current_app.conf.task_eager_propagates = True
        except Exception:
            pass

    def publish_message(self, ticket_id):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        body = json.dumps({"ticket_id": ticket_id})
        channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=body)
        connection.close()

    def test_end_to_end_rabbitmq_to_db(self):
        """
        Prueba de integración E2E (broker real, ejecución controlada):

        Flujo que prueba:
        1) Publica un mensaje en RabbitMQ con un ticket_id.
        2) Consume el mensaje desde la cola y llama al callback del consumidor (ack).
        3) Invoca la tarea Celery de forma síncrona para asegurar procesamiento en el test.
        4) Comprueba que se creó un `TicketAssignment` en la base de datos.

        Observaciones:
        - Se usa RabbitMQ real para comprobar la integración con el broker.
        - Para evitar depender de un worker externo, después de ackear se ejecuta
          la tarea localmente con `process_ticket.run`.
        """

        ticket_id = 'INTEG-1'

        # 1) Publicar mensaje en RabbitMQ
        self.publish_message(ticket_id)

        # 2) Conectar y consumir el mensaje de la cola
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # Intento de lectura con reintentos (maneja pequeñas latencias)
        method_frame, header_frame, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=False)
        retries = 5
        while method_frame is None and retries > 0:
            time.sleep(0.5)
            method_frame, header_frame, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=False)
            retries -= 1

        # Aserto: debe haberse recibido el mensaje
        self.assertIsNotNone(method_frame, "No se recibió el mensaje de RabbitMQ")

        # 3) Llamar al callback del consumidor para ackear y encolar la tarea
        import messaging.consumer as consumer
        consumer.callback(channel, method_frame, header_frame, body)

        # 4) Como `consumer.callback` en este entorno de pruebas llama a
        # `process_ticket.delay()` y las pruebas configuran Celery en modo eager,
        # la tarea ya se habrá ejecutado de forma síncrona. Evitamos volver a
        # ejecutar la tarea para no provocar inserciones duplicadas.
        # Pequeña espera para tolerar latencias mínimas si fuese necesario.
        time.sleep(0.1)

        # Aserto final: existe registro en DB para el ticket procesado
        self.assertTrue(TicketAssignment.objects.filter(ticket_id=ticket_id).exists())

        connection.close()
