"""
Handlers refactorizados para usar el adaptador de eventos.
"""
from typing import Dict, Any

from assignments.infrastructure.repository import DjangoAssignmentRepository
from assignments.infrastructure.messaging.event_publisher import RabbitMQEventPublisher
from assignments.infrastructure.messaging.event_adapter import TicketEventAdapter


def handle_ticket_event(event_data: Dict[str, Any]) -> None:
    """
    Procesa eventos de ticket usando el adaptador.
    
    Args:
        event_data: Diccionario con los datos del evento
    """
    repository = DjangoAssignmentRepository()
    event_publisher = RabbitMQEventPublisher()
    adapter = TicketEventAdapter(repository, event_publisher)
    
    event_type = event_data.get('event_type', 'ticket.created')
    
    if event_type == 'ticket.created':
        adapter.handle_ticket_created(event_data)
    elif event_type == 'ticket.priority_changed':
        adapter.handle_ticket_priority_changed(event_data)
    else:
        print(f"[ASSIGNMENT] Tipo de evento no manejado: {event_type}")
