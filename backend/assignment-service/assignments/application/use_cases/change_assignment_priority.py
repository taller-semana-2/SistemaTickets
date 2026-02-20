"""
Caso de uso para cambiar la prioridad de una asignación existente.
"""
from typing import Optional

from assignments.domain.entities import Assignment
from assignments.domain.repository import AssignmentRepository
from assignments.application.event_publisher import EventPublisher


class ChangeAssignmentPriority:
    """
    Caso de uso: Cambiar la prioridad de una asignación.
    
    Se dispara cuando cambia la prioridad del ticket base
    o si un supervisor cambia la prioridad directamente en la asignación.
    """
    
    def __init__(
        self,
        repository: AssignmentRepository,
        event_publisher: EventPublisher
    ):
        self.repository = repository
        self.event_publisher = event_publisher
        
    def execute(self, ticket_id: str, new_priority: str) -> Optional[Assignment]:
        """
        Ejecuta el cambio de prioridad de la asignación.
        
        Args:
            ticket_id: ID del ticket asociado
            new_priority: Nueva prioridad a asignar
            
        Returns:
            Assignment modificada, o None si no existe asignación para el ticket
            
        Raises:
            ValueError: Si la nueva autoridad es invalida
        """
        # 1. Buscar asignación por ticket_id
        assignment = self.repository.find_by_ticket_id(ticket_id)
        
        if not assignment:
            return None
            
        # 2. Cambiar prioridad (valida reglas de dominio)
        assignment.change_priority(new_priority)
        
        # 3. Persistir cambios
        updated_assignment = self.repository.save(assignment)
        
        return updated_assignment
