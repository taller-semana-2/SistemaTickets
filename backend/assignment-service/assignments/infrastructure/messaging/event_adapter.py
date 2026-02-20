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
    
    def _determine_priority(self, event_data: Dict[str, Any]) -> str:
        """
        Determina la prioridad de la asignación.
        
        Extrae la prioridad del evento creado. Si no viene explícita, 
        se podría inferir en base al tipo de problema.
        """
        # Extraer del evento si viene provisto
        priority = event_data.get('priority')
        if priority:
            return priority.lower()
            
        # Si no viene, intentar inferirla del tipo de incidencia o usar medium por defecto
        incident_type = event_data.get('type') or event_data.get('incidentType', '')
        if incident_type in ['software', 'hardware']:
            return 'high'
        elif incident_type in ['network', 'access']:
            return 'medium'
            
        return 'low'
