"""
Adaptador de eventos entrantes.
Traduce eventos externos a acciones en el dominio.
"""
import random
from typing import Dict, Any

from assignments.domain.repository import AssignmentRepository
from assignments.application.event_publisher import EventPublisher
from assignments.application.use_cases.create_assignment import CreateAssignment


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
    
    def _determine_priority(self, event_data: Dict[str, Any]) -> str:
        """
        Determina la prioridad de la asignación.
        
        Actualmente usa lógica aleatoria, pero podría expandirse para:
        - Analizar el tipo de ticket
        - Usar ML para predecir prioridad
        - Aplicar reglas de negocio complejas
        """
        return random.choice(['high', 'medium', 'low'])
