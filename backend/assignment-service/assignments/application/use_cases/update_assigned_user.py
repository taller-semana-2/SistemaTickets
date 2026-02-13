"""
Caso de uso: Actualizar usuario asignado.

Responsabilidad única: cambiar el usuario asignado a una asignación existente.
"""
from datetime import datetime
from typing import Optional

from assignments.domain.entities import Assignment
from assignments.domain.repository import AssignmentRepository
from assignments.application.event_publisher import EventPublisher


class UpdateAssignedUser:
    """
    Caso de uso para actualizar el usuario asignado a un ticket.
    
    Aplica la regla: solo se puede actualizar una asignación que ya existe.
    """
    
    def __init__(
        self, 
        repository: AssignmentRepository,
        event_publisher: EventPublisher
    ):
        self.repository = repository
        self.event_publisher = event_publisher
    
    def execute(self, assignment_id: int, assigned_to: Optional[str]) -> Assignment:
        """
        Actualiza el usuario asignado a una asignación.
        
        Args:
            assignment_id: ID de la asignación
            assigned_to: ID del usuario al que se asigna (puede ser None para desasignar)
        
        Returns:
            Assignment actualizada
        
        Raises:
            ValueError: si la asignación no existe
        """
        assignment = self.repository.find_by_id(assignment_id)
        
        if not assignment:
            raise ValueError(f"No existe asignación con ID {assignment_id}")
        
        # Actualizar el usuario asignado
        assignment.assigned_to = assigned_to
        updated_assignment = self.repository.save(assignment)
        
        return updated_assignment
