"""
Domain Events - Eventos que representan hechos importantes en el dominio.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class DomainEvent:
    """Clase base para todos los eventos de dominio"""
    occurred_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario para serialización"""
        raise NotImplementedError


@dataclass
class AssignmentCreated(DomainEvent):
    """
    Evento emitido cuando se crea una nueva asignación.
    """
    assignment_id: int
    ticket_id: str
    priority: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "assignment.created",
            "assignment_id": self.assignment_id,
            "ticket_id": self.ticket_id,
            "priority": self.priority,
            "occurred_at": self.occurred_at.isoformat()
        }


@dataclass
class AssignmentReassigned(DomainEvent):
    """
    Evento emitido cuando se reasigna un ticket (cambia la prioridad).
    """
    assignment_id: int
    ticket_id: str
    old_priority: str
    new_priority: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "assignment.reassigned",
            "assignment_id": self.assignment_id,
            "ticket_id": self.ticket_id,
            "old_priority": self.old_priority,
            "new_priority": self.new_priority,
            "occurred_at": self.occurred_at.isoformat()
        }
