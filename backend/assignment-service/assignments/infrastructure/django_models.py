"""
Modelo Django para persistencia de Assignment.
Este es un detalle de implementación de infraestructura, no parte del dominio.
"""
from django.db import models


class TicketAssignmentModel(models.Model):
    """
    Modelo Django que persiste la entidad Assignment.
    
    Separado del dominio para mantener independencia del framework.
    """
    ticket_id = models.CharField(max_length=255, unique=True, db_index=True)
    priority = models.CharField(max_length=50)
    assigned_at = models.DateTimeField()
    
    class Meta:
        db_table = 'assignments_ticketassignment'
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"Ticket {self.ticket_id} -> Priority {self.priority}"
