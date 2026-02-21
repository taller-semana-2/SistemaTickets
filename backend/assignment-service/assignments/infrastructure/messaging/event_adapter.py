"""
Adaptador de eventos entrantes.
Traduce eventos externos a acciones en el dominio.
"""
import random
from typing import Dict, Any

from assignments.domain.repository import AssignmentRepository
from assignments.application.event_publisher import EventPublisher
from assignments.application.use_cases.create_assignment import CreateAssignment
from assignments.application.use_cases.change_assignment_priority import ChangeAssignmentPriority


class TicketEventAdapter:
    """
    Adaptador que traduce eventos externos (TicketCreated) 
    a operaciones del dominio Assignment.
    
    Responsabilidad: decidir qué hacer cuando llega un evento de Ticket.
    """
    
    def __init__(
        self,
        repository: AssignmentRepository,
        event_publisher: EventPublisher
    ):
        self.repository = repository
        self.event_publisher = event_publisher
    
    def handle_ticket_created(self, event_data: Dict[str, Any]) -> None:
        """
        Maneja el evento TicketCreated.
        
        Lógica de negocio: 
        - Asigna una prioridad automáticamente al nuevo ticket
        - La prioridad se determina de forma aleatoria (simplificado)
        
        Args:
            event_data: Diccionario con los datos del evento
        """
        ticket_id = event_data.get('ticket_id')
        
        if not ticket_id:
            print("[ASSIGNMENT] Evento sin ticket_id, ignorando")
            return
        
        # Convertir ticket_id a string (puede venir como int desde el evento)
        ticket_id = str(ticket_id)
        
        priority = self._determine_priority(event_data)
        
        use_case = CreateAssignment(self.repository, self.event_publisher)
        
        try:
            assignment = use_case.execute(ticket_id=ticket_id, priority=priority)
            print(
                f"[ASSIGNMENT] Ticket {ticket_id} asignado con prioridad "
                f"{assignment.priority}"
            )
        except Exception as e:
            print(f"[ASSIGNMENT] Error procesando ticket {ticket_id}: {e}")
            raise
            
    def handle_ticket_priority_changed(self, event_data: Dict[str, Any]) -> None:
        """
        Maneja el evento ticket.priority_changed.
        
        Args:
            event_data: Diccionario con los datos del evento
        """
        ticket_id = event_data.get('ticket_id')
        new_priority = event_data.get('new_priority')
        
        if not ticket_id or not new_priority:
            print("[ASSIGNMENT] Evento de cambio de prioridad sin ticket_id o new_priority, ignorando")
            return
            
        ticket_id = str(ticket_id)
        new_priority = new_priority.lower()
        
        use_case = ChangeAssignmentPriority(self.repository, self.event_publisher)
        
        try:
            assignment = use_case.execute(ticket_id=ticket_id, new_priority=new_priority)
            if assignment:
                print(
                    f"[ASSIGNMENT] Prioridad del ticket {ticket_id} "
                    f"actualizada a {assignment.priority}"
                )
            else:
                print(f"[ASSIGNMENT] No se encontró asignación para el ticket {ticket_id}")
        except Exception as e:
            print(f"[ASSIGNMENT] Error actualizando prioridad del ticket {ticket_id}: {e}")
            raise
    
    def _determine_priority(self, event_data: Dict[str, Any]) -> str:
        """
        Determina la prioridad de la asignación.
        
        Extrae la prioridad del evento creado, o asigna 'unassigned' por defecto.
        """
        # Extraer del evento si viene provisto
        priority = event_data.get('priority')
        if priority:
            return priority.lower()
            
        # Al crearse un ticket sin prioridad, debe ser 'unassigned' 
        # (ya no inferimos basado en el tipo de incidencia)
        return 'unassigned'
