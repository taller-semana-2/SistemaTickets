from django.db import models

class TicketAssignment(models.Model):
    ticket_id = models.CharField(max_length=255, unique=True)
    priority = models.CharField(max_length=50)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.ticket_id} -> Priority {self.priority}"
