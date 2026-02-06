from assignments.models import TicketAssignment
from django.utils import timezone
import random

def handle_ticket_created(ticket_id):
    """Procesa un ticket y guarda la asignación en la DB"""
    priority = random.choice(["high", "medium", "low"])
    
    TicketAssignment.objects.create(
        ticket_id=ticket_id,
        priority=priority,
        assigned_at=timezone.now()
    )
