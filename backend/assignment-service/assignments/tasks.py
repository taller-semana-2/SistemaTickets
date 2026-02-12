"""
Celery tasks refactorizadas para usar handlers actualizados.
"""
from celery import shared_task
from typing import Dict, Any


@shared_task
def process_ticket_event(event_data: Dict[str, Any]):
    """
    Celery task que procesa eventos de ticket en segundo plano.
    
    Args:
        event_data: Diccionario con los datos del evento
    """
    from messaging.handlers import handle_ticket_event
    handle_ticket_event(event_data)
