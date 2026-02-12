"""
Caso de uso: Reasignar Ticket.

Responsabilidad única: cambiar la prioridad de una asignación existente.
"""
from datetime import datetime

from assignments.domain.entities import Assignment
from assignments.domain.repository import AssignmentRepository
from assignments.domain.events import AssignmentReassigned
from assignments.application.event_publisher import EventPublisher


class ReassignTicket:
    """
    Caso de uso para reasignar un ticket (cambiar su prioridad).
    
    Aplica la regla: solo se puede reasignar un ticket que ya tiene asignación.
    """
    
    def __init__(
        self, 
        repository: AssignmentRepository,
        event_publisher: EventPublisher
    ):
        self.repository = repository
        self.event_publisher = event_publisher
    
    def execute(self, ticket_id: str, new_priority: str) -> Assignment:
        """
        Reasigna un ticket cambiando su prioridad.
        
        Args:
            ticket_id: ID del ticket
            new_priority: Nueva prioridad (high, medium, low)
        
        Returns:
            Assignment actualizada
        
        Raises:
            ValueError: si el ticket no tiene asignación o la prioridad es inválida
        """
        assignment = self.repository.find_by_ticket_id(ticket_id)
        
        if not assignment:
            raise ValueError(f"No existe asignación para el ticket {ticket_id}")
        
        old_priority = assignment.priority
        
        if old_priority == new_priority:
            return assignment
        
        assignment.change_priority(new_priority)
        updated_assignment = self.repository.save(assignment)
        
        event = AssignmentReassigned(
            occurred_at=datetime.utcnow(),
            assignment_id=updated_assignment.id,
            ticket_id=updated_assignment.ticket_id,
            old_priority=old_priority,
            new_priority=new_priority
        )
        self.event_publisher.publish(event)
        
        return updated_assignment
