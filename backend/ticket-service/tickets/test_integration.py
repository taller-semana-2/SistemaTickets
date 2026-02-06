import json
import time

import pika
from django.test import TestCase

from .messaging.events import publish_ticket_created

QUEUE_NAME = 'ticket_created'
RABBIT_HOST = 'rabbitmq'


class TicketServiceIntegrationTests(TestCase):
    def publish_and_get_message(self, ticket_id):
        # purge queue first to avoid leftover messages from other tests
        conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
        ch = conn.channel()
        ch.queue_declare(queue=QUEUE_NAME, durable=True)
        ch.queue_purge(queue=QUEUE_NAME)
        conn.close()

        # publish
        publish_ticket_created(ticket_id)

        # read from queue
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        method_frame, header_frame, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=False)
        retries = 5
        while method_frame is None and retries > 0:
            time.sleep(0.2)
            method_frame, header_frame, body = channel.basic_get(queue=QUEUE_NAME, auto_ack=False)
            retries -= 1

        connection.close()
        return method_frame, header_frame, body

    def test_publish_ticket_created_puts_message_on_queue(self):
        ticket_id = 9999
        method_frame, header_frame, body = self.publish_and_get_message(ticket_id)
        self.assertIsNotNone(method_frame)
        data = json.loads(body)
        self.assertEqual(data.get('ticket_id'), ticket_id)