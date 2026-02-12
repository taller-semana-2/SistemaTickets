"""
RabbitMQ Event Publisher - Implementación del publicador de eventos usando RabbitMQ.
Adaptador que traduce eventos de dominio a mensajes RabbitMQ.
"""

import json
import os
from typing import Dict, Any

import pika

from ..domain.event_publisher import EventPublisher
from ..domain.events import DomainEvent, NotificationMarkedAsRead


class RabbitMQEventPublisher(EventPublisher):
    """
    Implementación del publicador de eventos usando RabbitMQ.
    Traduce eventos de dominio a mensajes y los publica en un exchange.
    """
    
    def __init__(self):
        """Inicializa el publicador con configuración de RabbitMQ."""
        self.host = os.environ.get('RABBITMQ_HOST', 'localhost')
        self.exchange_name = os.environ.get('RABBITMQ_EXCHANGE_NAME', 'notifications')
    
    def publish(self, event: DomainEvent) -> None:
        """
        Publica un evento de dominio en RabbitMQ.
        
        Args:
            event: Evento de dominio a publicar
        """
        # Traducir evento de dominio a mensaje
        message = self._translate_event(event)
        
        # Publicar en RabbitMQ
        self._publish_to_rabbitmq(message)
    
    def _translate_event(self, event: DomainEvent) -> Dict[str, Any]:
        """
        Traduce un evento de dominio a un diccionario JSON serializable.
        
        Args:
            event: Evento de dominio
            
        Returns:
            Diccionario con los datos del evento
        """
        if isinstance(event, NotificationMarkedAsRead):
            return {
                "event_type": "notification.marked_as_read",
                "occurred_at": event.occurred_at.isoformat(),
                "data": {
                    "notification_id": event.notification_id,
                    "ticket_id": event.ticket_id
                }
            }
        
        # Evento genérico
        return {
            "event_type": "domain.event",
            "occurred_at": event.occurred_at.isoformat(),
            "data": {}
        }
    
    def _publish_to_rabbitmq(self, message: Dict[str, Any]) -> None:
        """
        Publica un mensaje en RabbitMQ.
        
        Args:
            message: Diccionario con los datos del mensaje
        """
        try:
            # Conexión a RabbitMQ
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            channel = connection.channel()
            
            # Declarar exchange (topic)
            channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='topic',
                durable=True
            )
            
            # Publicar mensaje
            routing_key = message.get('event_type', 'notification.event')
            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Mensaje persistente
                    content_type='application/json'
                )
            )
            
            connection.close()
            
        except Exception as e:
            # Log error (en producción usar logging apropiado)
            print(f"Error publicando evento: {e}")
