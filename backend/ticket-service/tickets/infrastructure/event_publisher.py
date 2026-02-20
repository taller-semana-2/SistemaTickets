"""
RabbitMQ Event Publisher - Implementación del publicador de eventos usando RabbitMQ.
Adaptador que traduce eventos de dominio a mensajes RabbitMQ.
"""

import json
import os
from typing import Dict, Any

import pika

from ..domain.event_publisher import EventPublisher
from ..domain.events import DomainEvent, TicketCreated, TicketPriorityChanged, TicketStatusChanged


class RabbitMQEventPublisher(EventPublisher):
    """
    Implementación del publicador de eventos usando RabbitMQ.
    Traduce eventos de dominio a mensajes y los publica en un exchange.
    """
    
    def __init__(self):
        """Inicializa el publicador con configuración de RabbitMQ."""
        self.host = os.environ.get('RABBITMQ_HOST', 'localhost')
        self.exchange_name = os.environ.get('RABBITMQ_EXCHANGE_NAME', 'tickets')
    
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
        if isinstance(event, TicketCreated):
            return {
                "event_type": "ticket.created",
                "ticket_id": event.ticket_id,
                "title": event.title,
                "description": event.description,
                "status": event.status,
                "occurred_at": event.occurred_at.isoformat()
            }
        elif isinstance(event, TicketStatusChanged):
            return {
                "event_type": "ticket.status_changed",
                "ticket_id": event.ticket_id,
                "old_status": event.old_status,
                "new_status": event.new_status,
                "occurred_at": event.occurred_at.isoformat()
            }
        elif isinstance(event, TicketPriorityChanged):
            return {
                "event_type": "ticket.priority_changed",
                "ticket_id": event.ticket_id,
                "old_priority": event.old_priority,
                "new_priority": event.new_priority,
                "justification": event.justification,
                "occurred_at": event.occurred_at.isoformat()
            }
        else:
            # Evento genérico
            return {
                "event_type": event.__class__.__name__,
                "occurred_at": event.occurred_at.isoformat()
            }
    
    def _publish_to_rabbitmq(self, message: Dict[str, Any]) -> None:
        """
        Publica un mensaje en RabbitMQ usando exchange fanout.
        
        Args:
            message: Diccionario con los datos del mensaje
        """
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host)
        )
        channel = connection.channel()
        
        # Declarar exchange fanout (broadcast)
        channel.exchange_declare(
            exchange=self.exchange_name,
            exchange_type='fanout',
            durable=True
        )
        
        # Serializar mensaje a JSON
        body = json.dumps(message)
        
        # Publicar al exchange
        channel.basic_publish(
            exchange=self.exchange_name,
            routing_key='',  # Ignorado en fanout
            body=body,
            properties=pika.BasicProperties(delivery_mode=2)  # Mensaje persistente
        )
        
        connection.close()
        
        print(f"Evento {message['event_type']} publicado: ticket_id={message.get('ticket_id')}")
