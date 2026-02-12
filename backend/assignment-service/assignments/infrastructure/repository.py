"""
Implementación del repositorio usando Django ORM.
Adaptador entre el dominio y la base de datos.
"""
from typing import Optional, List

from assignments.domain.entities import Assignment
from assignments.domain.repository import AssignmentRepository
from .django_models import TicketAssignmentModel


class DjangoAssignmentRepository(AssignmentRepository):
    """
    Implementación concreta del repositorio usando Django ORM.
    
    Responsabilidad: traducir entre entidades de dominio y modelos Django.
    """
    
    def save(self, assignment: Assignment) -> Assignment:
        """Persiste una asignación"""
        if assignment.id:
            model = TicketAssignmentModel.objects.get(id=assignment.id)
            model.priority = assignment.priority
            model.save()
        else:
            model = TicketAssignmentModel.objects.create(
                ticket_id=assignment.ticket_id,
                priority=assignment.priority,
                assigned_at=assignment.assigned_at
            )
        
        return self._to_entity(model)
    
    def find_by_ticket_id(self, ticket_id: str) -> Optional[Assignment]:
        """Busca por ticket_id"""
        try:
            model = TicketAssignmentModel.objects.get(ticket_id=ticket_id)
            return self._to_entity(model)
        except TicketAssignmentModel.DoesNotExist:
            return None
    
    def find_by_id(self, assignment_id: int) -> Optional[Assignment]:
        """Busca por id"""
        try:
            model = TicketAssignmentModel.objects.get(id=assignment_id)
            return self._to_entity(model)
        except TicketAssignmentModel.DoesNotExist:
            return None
    
    def find_all(self) -> List[Assignment]:
        """Retorna todas las asignaciones"""
        models = TicketAssignmentModel.objects.all()
        return [self._to_entity(model) for model in models]
    
    def delete(self, assignment_id: int) -> bool:
        """Elimina una asignación"""
        deleted, _ = TicketAssignmentModel.objects.filter(id=assignment_id).delete()
        return deleted > 0
    
    @staticmethod
    def _to_entity(model: TicketAssignmentModel) -> Assignment:
        """Convierte un modelo Django a entidad de dominio"""
        return Assignment(
            id=model.id,
            ticket_id=model.ticket_id,
            priority=model.priority,
            assigned_at=model.assigned_at
        )
