"""
Entidades de dominio - Representan conceptos del negocio con identidad única.
Contienen las reglas de negocio y son independientes del framework.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum
import re

from .events import DomainEvent, UserDeactivated, UserEmailChanged
from .exceptions import InvalidEmail, UserAlreadyInactive


class UserRole(str, Enum):
    """
    Enum para los roles de usuario en el dominio.
    Define los tipos de usuario permitidos en el sistema.
    """
    ADMIN = "ADMIN"
    USER = "USER"


@dataclass
class User:
    """
    Entidad de dominio User.
    Representa un usuario del sistema con sus reglas de negocio encapsuladas.
    
    Reglas de negocio:
    - Un usuario tiene un ID único (UUID)
    - El email debe ser válido y único en el sistema
    - El username debe tener al menos 3 caracteres
    - Un usuario puede estar activo o inactivo
    - Un usuario tiene un rol (ADMIN o USER)
    - Solo se puede desactivar un usuario activo (idempotencia)
    """
    
    # Atributos de la entidad
    id: Optional[str]  # UUID como string, None hasta persistir
    email: str
    username: str
    password_hash: str  # Hash del password, NUNCA el password en texto plano
    is_active: bool
    role: UserRole  # Rol del usuario
    created_at: datetime
    
    # Lista de eventos de dominio generados por cambios en la entidad
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False, repr=False)
    
    def __post_init__(self):
        """Validación de estado inicial de la entidad."""
        # Validar email
        if not self._is_valid_email(self.email):
            raise InvalidEmail(self.email)
        
        # Validar username (mínimo 3 caracteres)
        if len(self.username.strip()) < 3:
            from .exceptions import InvalidUsername
            raise InvalidUsername(self.username)
    
    def deactivate(self, reason: Optional[str] = None) -> None:
        """
        Desactiva el usuario aplicando reglas de negocio.
        
        Reglas:
        - Solo se puede desactivar un usuario activo
        - La operación es idempotente: si ya está inactivo, lanza excepción
        - Genera un evento UserDeactivated
        
        Args:
            reason: Razón opcional de la desactivación
            
        Raises:
            UserAlreadyInactive: Si el usuario ya está inactivo
        """
        # Regla: No se puede desactivar un usuario ya inactivo
        if not self.is_active:
            raise UserAlreadyInactive(self.id)
        
        # Cambiar estado
        self.is_active = False
        
        # Generar evento de dominio
        event = UserDeactivated(
            occurred_at=datetime.now(),
            user_id=self.id,
            reason=reason
        )
        self._domain_events.append(event)
    
    def change_email(self, new_email: str) -> None:
        """
        Cambia el email del usuario aplicando validaciones.
        
        Reglas:
        - El nuevo email debe ser válido
        - El cambio es idempotente: si es el mismo email, no hace nada
        - Genera un evento UserEmailChanged
        
        Args:
            new_email: Nuevo email del usuario
            
        Raises:
            InvalidEmail: Si el nuevo email no es válido
        """
        # Validar que el nuevo email sea válido
        if not self._is_valid_email(new_email):
            raise InvalidEmail(new_email)
        
        # Normalizar emails para comparación
        new_email_normalized = new_email.lower().strip()
        current_email_normalized = self.email.lower().strip()
        
        # Idempotencia: Si el email es el mismo, no hacer nada
        if new_email_normalized == current_email_normalized:
            return
        
        # Cambiar email
        old_email = self.email
        self.email = new_email_normalized
        
        # Generar evento de dominio
        event = UserEmailChanged(
            occurred_at=datetime.now(),
            user_id=self.id,
            old_email=old_email,
            new_email=new_email_normalized
        )
        self._domain_events.append(event)
    
    def is_admin(self) -> bool:
        """
        Verifica si el usuario tiene rol de administrador.
        
        Returns:
            True si el usuario es ADMIN
        """
        return self.role == UserRole.ADMIN
    
    def is_normal_user(self) -> bool:
        """
        Verifica si el usuario tiene rol de usuario normal.
        
        Returns:
            True si el usuario es USER
        """
        return self.role == UserRole.USER
    
    def collect_domain_events(self) -> List[DomainEvent]:
        """
        Recolecta y limpia los eventos de dominio generados.
        Se usa para publicar eventos después de persistir cambios.
        
        Returns:
            Lista de eventos de dominio
        """
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """
        Valida formato básico de email.
        
        Args:
            email: Email a validar
            
        Returns:
            True si el email tiene formato válido
        """
        if not email or not email.strip():
            return False
        
        # Regex simple para validar formato básico de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
    
    @staticmethod
    def create(email: str, username: str, password_hash: str, role: UserRole = UserRole.USER) -> "User":
        """
        Crea un nuevo usuario en estado activo (método factory).
        
        Args:
            email: Email del usuario
            username: Nombre de usuario
            password_hash: Hash del password (NO el password en texto plano)
            role: Rol del usuario (default: USER)
            
        Returns:
            Nueva instancia de User
            
        Note:
            El evento UserCreated se genera al persistir porque necesitamos
            el ID asignadopor la BD
        """
        user = User(
            id=None,  # El ID se asigna al persistir
            email=email.lower().strip(),
            username=username.strip(),
            password_hash=password_hash,
            is_active=True,role=role,
            created_at=datetime.now()
        )
        
        return user
