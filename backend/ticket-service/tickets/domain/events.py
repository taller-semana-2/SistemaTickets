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
class TicketCreated(DomainEvent):
    """Evento: Se ha creado un nuevo ticket."""
    ticket_id: int
    title: str
    description: str
    status: str


@dataclass(frozen=True)
class TicketStatusChanged(DomainEvent):
    """Evento: El estado de un ticket ha cambiado."""
    ticket_id: int
    old_status: str
    new_status: str
