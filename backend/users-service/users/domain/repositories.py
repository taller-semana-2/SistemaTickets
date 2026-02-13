"""
Interfaces de Repositorio - Define el contrato para persistir y recuperar usuarios.

⚠️ IMPORTANTE: Este archivo contiene SOLO interfaces (clases abstractas).
Las IMPLEMENTACIONES van en infrastructure/repository.py

Esto permite inyección de dependencias y desacopla el dominio de la infraestructura.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from .entities import User, UserRole


class UserRepository(ABC):
    """
    Contrato abstracto para persistir y recuperar usuarios del dominio.
    
    El dominio depende de esta INTERFAZ, no de la implementación concreta.
    La infraestructura implementa esta interfaz usando Django ORM, SQLAlchemy, etc.
    """
    
    @abstractmethod
    def save(self, user: User) -> User:
        """
        Persiste un usuario (create o update).
        
        Args:
            user: Entidad User a persistir
            
        Returns:
            Usuario persistido con el ID asignado (si es nuevo)
        """
        pass
    
    @abstractmethod
    def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Busca un usuario por su ID único.
        
        Args:
            user_id: ID del usuario (UUID como string)
            
        Returns:
            Entidad User si existe, None si no se encuentra
        """
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Busca un usuario por su email.
        
        Args:
            email: Email del usuario
            
        Returns:
            Entidad User si existe, None si no se encuentra
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[User]:
        """
        Obtiene todos los usuarios del sistema.
        
        Returns:
            Lista de entidades User
        """
        pass
    
    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado.
        
        Args:
            email: Email a verificar
            
        Returns:
            True si existe un usuario con ese email, False en caso contrario
        """
        pass
    
    @abstractmethod
    def delete(self, user_id: str) -> None:
        """
        Elimina un usuario por su ID.
        
        Args:
            user_id: ID del usuario a eliminar
        """
        pass
    
    @abstractmethod
    def find_by_role(self, role: UserRole) -> List[User]:
        """
        Busca usuarios por rol.
        
        Args:
            role: Rol a filtrar (UserRole enum)
            
        Returns:
            Lista de entidades User con ese rol
        """
        pass
