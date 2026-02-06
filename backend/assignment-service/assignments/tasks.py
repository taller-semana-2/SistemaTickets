from celery import shared_task
from messaging.handlers import handle_ticket_created

@shared_task
def process_ticket(ticket_id):
    """Celery task que procesa el ticket en segundo plano"""
    handle_ticket_created(ticket_id)
