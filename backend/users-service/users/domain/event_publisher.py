"""
Interfaz EventPublisher - Define el contrato para publicar eventos de dominio.

⚠️ IMPORTANTE: Este archivo contiene SOLO la interfaz abstracta.
La IMPLEMENTACIÓN (RabbitMQ, Kafka, etc.) va en infrastructure/event_publisher.py

El dominio solo sabe que puede "publicar eventos", no sabe CÓMO se publican.
"""

from abc import ABC, abstractmethod
from typing import Any


class EventPublisher(ABC):
    """
    Contrato abstracto para publicar eventos de dominio.
    
    El dominio depende de esta INTERFAZ, no de la implementación concreta.
    La infraestructura implementa esta interfaz usando RabbitMQ, Kafka, etc.
    """
    
    @abstractmethod
    def publish(self, event: Any, routing_key: str) -> None:
        """
        Publica un evento de dominio al bus de mensajes.
        
        Args:
            event: Evento de dominio a publicar (UserCreated, UserDeactivated, etc.)
            routing_key: Clave de enrutamiento para el mensaje (ej: 'user.created')
        """
        pass
