"""
Domain Events - Eventos que representan hechos importantes del dominio User.
Los eventos son inmutables (frozen=True) y representan algo que ya ocurrió.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class DomainEvent:
    """Clase base para todos los eventos de dominio."""
    occurred_at: datetime


@dataclass(frozen=True)
class UserCreated(DomainEvent):
    """
    Evento: Se ha creado un nuevo usuario.
    Se emite después de persistir el usuario en la base de datos.
    """
    user_id: str
    email: str
    username: str


@dataclass(frozen=True)
class UserDeactivated(DomainEvent):
    """
    Evento: Un usuario ha sido desactivado.
    Se emite cuando un usuario activo es desactivado.
    """
    user_id: str
    reason: Optional[str] = None


@dataclass(frozen=True)
class UserEmailChanged(DomainEvent):
    """
    Evento: El email de un usuario ha cambiado.
    Se emite cuando un usuario actualiza su dirección de correo.
    """
    user_id: str
    old_email: str
    new_email: str
