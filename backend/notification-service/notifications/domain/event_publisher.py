"""
Event Publisher - Interfaz (Puerto) para publicación de eventos de dominio.
Define el contrato que deben cumplir las implementaciones concretas.
Aplicando Dependency Inversion Principle (DIP).
"""

from abc import ABC, abstractmethod

from .events import DomainEvent


class EventPublisher(ABC):
    """
    Interfaz del publicador de eventos.
    Esta es una abstracción (puerto) que será implementada por adaptadores.
    """
    
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """
        Publica un evento de dominio.
        
        Args:
            event: Evento de dominio a publicar
        """
        pass
