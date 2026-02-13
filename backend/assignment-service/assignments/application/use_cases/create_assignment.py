"""
Caso de uso: Crear Assignment.

Responsabilidad única: crear una nueva asignación y emitir el evento correspondiente.
"""
from datetime import datetime
from typing import Optional

from assignments.domain.entities import Assignment
from assignments.domain.repository import AssignmentRepository
from assignments.domain.events import AssignmentCreated
from assignments.application.event_publisher import EventPublisher


class CreateAssignment:
    """
    Caso de uso para crear una nueva asignación de ticket.
    
    Aplica la regla: un ticket solo puede tener una asignación activa.
    Si ya existe, la operación es idempotente.
    """
    
    def __init__(
        self, 
        repository: AssignmentRepository,
        event_publisher: EventPublisher
    ):
        self.repository = repository
        self.event_publisher = event_publisher
    
    def execute(self, ticket_id: str, priority: str, assigned_to: Optional[str] = None) -> Assignment:
        """
        Crea una nueva asignación.
        Si ya existe una asignación para el ticket, la retorna sin modificar (idempotente).
        
        Args:
            ticket_id: ID del ticket
            priority: Prioridad de la asignación (high, medium, low)
            assigned_to: ID del usuario al que se asigna (opcional, referencia lógica)
        
        Returns:
            Assignment creada o existente
        
        Raises:
            ValueError: si los datos son inválidos
        """
        existing = self.repository.find_by_ticket_id(ticket_id)
        if existing:
            return existing
        
        assignment = Assignment(
            ticket_id=ticket_id,
            priority=priority,
            assigned_at=datetime.utcnow(),
            assigned_to=assigned_to
        )
        
        saved_assignment = self.repository.save(assignment)
        
        event = AssignmentCreated(
            occurred_at=datetime.utcnow(),
            assignment_id=saved_assignment.id,
            ticket_id=saved_assignment.ticket_id,
            priority=saved_assignment.priority,
            assigned_to=saved_assignment.assigned_to
        )
        self.event_publisher.publish(event)
        
        return saved_assignment
