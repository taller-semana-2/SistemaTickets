from django.db import models

# Create your models here.
class Ticket(models.Model):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"

    STATUS_CHOICES = [
        (OPEN, "Open"),
        (IN_PROGRESS, "In Progress"),
        (CLOSED, "Closed"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=OPEN,
    )
    user_id = models.CharField(
        max_length=255,
        help_text="ID del usuario que creó el ticket (referencia lógica, no FK)"
    )
    created_at = models.DateTimeField(auto_now_add=True)