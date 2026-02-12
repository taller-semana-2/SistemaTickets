"""
Interfaz del repositorio de Assignment (Puerto).
Define el contrato que debe cumplir cualquier implementación de persistencia.
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from .entities import Assignment


class AssignmentRepository(ABC):
    """
    Puerto (interface) que define las operaciones de persistencia
    para la entidad Assignment.
    
    El dominio depende de esta abstracción, no de la implementación concreta.
    """
    
    @abstractmethod
    def save(self, assignment: Assignment) -> Assignment:
        """
        Persiste una asignación.
        Si ya existe (tiene id), la actualiza.
        Si no existe, la crea.
        
        Returns:
            Assignment con id asignado
        """
        pass
    
    @abstractmethod
    def find_by_ticket_id(self, ticket_id: str) -> Optional[Assignment]:
        """
        Busca una asignación por ticket_id.
        
        Returns:
            Assignment si existe, None si no existe
        """
        pass
    
    @abstractmethod
    def find_by_id(self, assignment_id: int) -> Optional[Assignment]:
        """
        Busca una asignación por su id.
        
        Returns:
            Assignment si existe, None si no existe
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[Assignment]:
        """
        Retorna todas las asignaciones ordenadas por fecha (más reciente primero).
        
        Returns:
            Lista de Assignment
        """
        pass
    
    @abstractmethod
    def delete(self, assignment_id: int) -> bool:
        """
        Elimina una asignación por su id.
        
        Returns:
            True si se eliminó, False si no existía
        """
        pass
