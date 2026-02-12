"""
Domain Events - Eventos que representan hechos importantes del dominio.
Los eventos son inmutables y representan algo que ya ocurrió.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class DomainEvent:
    """Clase base para todos los eventos de dominio."""
    occurred_at: datetime


@dataclass(frozen=True)
class NotificationMarkedAsRead(DomainEvent):
    """Evento: Una notificación ha sido marcada como leída."""
    notification_id: int
    ticket_id: str
