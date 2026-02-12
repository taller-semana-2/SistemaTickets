"""
Implementación del EventPublisher usando RabbitMQ.
"""
import json
import os
import pika
from typing import Optional

from assignments.domain.events import DomainEvent
from assignments.application.event_publisher import EventPublisher


class RabbitMQEventPublisher(EventPublisher):
    """
    Implementación concreta del EventPublisher usando RabbitMQ.
    
    Publica eventos de dominio a un exchange de RabbitMQ.
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        exchange: Optional[str] = None
    ):
        self.host = host or os.environ.get('RABBITMQ_HOST', 'rabbitmq')
        self.exchange = exchange or os.environ.get(
            'RABBITMQ_EXCHANGE_ASSIGNMENT', 
            'assignment_events'
        )
    
    def publish(self, event: DomainEvent) -> None:
        """
        Publica un evento de dominio a RabbitMQ.
        
        Args:
            event: Evento a publicar
        """
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            channel = connection.channel()
            
            channel.exchange_declare(
                exchange=self.exchange,
                exchange_type='fanout',
                durable=True
            )
            
            message = json.dumps(event.to_dict())
            
            channel.basic_publish(
                exchange=self.exchange,
                routing_key='',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent
                    content_type='application/json'
                )
            )
            
            connection.close()
            
            print(f"[ASSIGNMENT] Evento publicado: {event.to_dict()['event_type']}")
            
        except Exception as e:
            print(f"[ASSIGNMENT] Error publicando evento: {e}")
            raise
