"""
Repository - Interfaz (Puerto) para persistencia de tickets.
Define el contrato que deben cumplir las implementaciones concretas.
Aplicando Dependency Inversion Principle (DIP).
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from .entities import Ticket


class TicketRepository(ABC):
    """
    Interfaz del repositorio de tickets.
    Esta es una abstracción (puerto) que será implementada por adaptadores.
    """
    
    @abstractmethod
    def save(self, ticket: Ticket) -> Ticket:
        """
        Persiste un ticket (crear o actualizar).
        
        Args:
            ticket: Entidad de dominio a persistir
            
        Returns:
            El ticket persistido con su ID asignado
        """
        pass
    
    @abstractmethod
    def find_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """
        Busca un ticket por su ID.
        
        Args:
            ticket_id: ID del ticket a buscar
            
        Returns:
            La entidad de dominio Ticket o None si no existe
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[Ticket]:
        """
        Obtiene todos los tickets.
        
        Returns:
            Lista de entidades de dominio Ticket
        """
        pass
    
    @abstractmethod
    def delete(self, ticket_id: int) -> None:
        """
        Elimina un ticket por su ID.
        
        Args:
            ticket_id: ID del ticket a eliminar
        """
        pass
