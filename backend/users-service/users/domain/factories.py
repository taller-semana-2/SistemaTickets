"""
Factory - Crea instancias de entidades de dominio asegurando validez.
Encapsula la lógica compleja de creación y validación.
"""

import uuid
import hashlib

from .entities import User, UserRole
from .exceptions import InvalidUserData, InvalidEmail, InvalidUsername


class UserFactory:
    """
    Factory para crear usuarios válidos.
    Aplica validaciones y reglas de creación del dominio.
    """
    
    @staticmethod
    def create(email: str, username: str, password: str, role: UserRole = UserRole.USER) -> User:
        """
        Crea un nuevo usuario validando todos los datos de entrada.
        
        Reglas de validación:
        - Email no puede estar vacío y debe tener formato válido
        - Username debe tener al menos 3 caracteres
        - Password debe tener al menos 8 caracteres
        - Email se normaliza a minúsculas
        - Username se limpia de espacios
        - Role por defecto es USER
        
        Args:
            email: Email del usuario
            username: Nombre de usuario
            password: Password en texto plano (se hasheará)
            role: Rol del usuario (default: USER)
            
        Returns:
            Nueva instancia de User totalmente válida
            
        Raises:
            InvalidEmail: Si el email no es válido
            InvalidUsername: Si el username no cumple requisitos
            InvalidUserData: Si el password es muy corto
        """
        # Validación: Email no vacío
        if not email or not email.strip():
            raise InvalidEmail(email or "")
        
        # Validación: Username mínimo 3 caracteres
        if not username or len(username.strip()) < 3:
            raise InvalidUsername(username or "")
        
        # Validación: Password mínimo 8 caracteres
        if not password or len(password) < 8:
            raise InvalidUserData("El password debe tener al menos 8 caracteres")
        
        # Hashear el password (simple hash para desarrollo, usar bcrypt en producción)
        password_hash = UserFactory._hash_password(password)
        
        # Crear usuario usando el método factory de la entidad
        # Esto aplicará las validaciones adicionales del __post_init__
        return User.create(
            email=email,
            username=username,
            password_hash=password_hash,
            role=role
        )
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Genera un hash del password.
        
        NOTA: En producción usar bcrypt, argon2 o similar.
        Este es un hash simple solo para desarrollo/ejemplo.
        
        Args:
            password: Password en texto plano
            
        Returns:
            Hash SHA-256 del password
        """
        return hashlib.sha256(password.encode()).hexdigest()
