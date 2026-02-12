"""
Repository - Interfaz (Puerto) para persistencia de notificaciones.
Define el contrato que deben cumplir las implementaciones concretas.
Aplicando Dependency Inversion Principle (DIP).
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from .entities import Notification


class NotificationRepository(ABC):
    """
    Interfaz del repositorio de notificaciones.
    Esta es una abstracción (puerto) que será implementada por adaptadores.
    """
    
    @abstractmethod
    def save(self, notification: Notification) -> Notification:
        """
        Persiste una notificación (crear o actualizar).
        
        Args:
            notification: Entidad de dominio a persistir
            
        Returns:
            La notificación persistida con su ID asignado
        """
        pass
    
    @abstractmethod
    def find_by_id(self, notification_id: int) -> Optional[Notification]:
        """
        Busca una notificación por su ID.
        
        Args:
            notification_id: ID de la notificación a buscar
            
        Returns:
            La entidad de dominio Notification o None si no existe
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[Notification]:
        """
        Obtiene todas las notificaciones.
        
        Returns:
            Lista de entidades de dominio
        """
        pass
    
    @abstractmethod
    def to_django_model(self, notification: Notification):
        """
        Convierte una entidad de dominio a modelo Django para serialización.
        
        Args:
            notification: Entidad de dominio
            
        Returns:
            Modelo Django
        """
        pass
