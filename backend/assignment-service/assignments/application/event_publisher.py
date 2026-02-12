"""
Interfaz para publicar eventos de dominio.
Permite desacoplar la aplicación del mecanismo de mensajería específico.
"""
from abc import ABC, abstractmethod
from assignments.domain.events import DomainEvent


class EventPublisher(ABC):
    """
    Puerto (interface) para publicar eventos de dominio.
    
    La implementación concreta estará en la capa de infraestructura.
    """
    
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """
        Publica un evento de dominio.
        
        Args:
            event: Evento a publicar
        """
        pass
