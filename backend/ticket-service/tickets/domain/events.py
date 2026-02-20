"""
Domain Events - Eventos que representan hechos importantes del dominio.
Los eventos son inmutables y representan algo que ya ocurrió.
"""

from dataclasses import dataclass
from datetime import datetime


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
    user_id: str


@dataclass(frozen=True)
class TicketStatusChanged(DomainEvent):
    """Evento: El estado de un ticket ha cambiado."""
    ticket_id: int
    old_status: str
    new_status: str


@dataclass(frozen=True)
class TicketPriorityChanged(DomainEvent):
    """Evento: La prioridad de un ticket ha cambiado."""
    ticket_id: int
    old_priority: str
    new_priority: str
<<<<<<< feature/sistema_de_notificaciones


@dataclass(frozen=True)
class TicketResponseAdded(DomainEvent):
    """Evento: Se ha agregado una respuesta de admin a un ticket."""
    ticket_id: int
    response_id: int
    admin_id: str
    response_text: str
    user_id: str
=======
    justification: Optional[str] = None
>>>>>>> develop
