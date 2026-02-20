"""Modelos del dominio para el servicio de tickets.

Define la entidad principal ``Ticket`` que representa una solicitud
o incidencia dentro del sistema de gestión de tickets.
"""

from django.db import models


class Ticket(models.Model):
    """Modelo que representa un ticket de soporte o incidencia.

    Un ticket atraviesa un ciclo de vida definido por tres estados:
    ``OPEN`` → ``IN_PROGRESS`` → ``CLOSED``. Cada ticket pertenece
    a un usuario identificado por ``user_id``, que es una referencia
    lógica al users-service (no una clave foránea de Django), lo que
    permite el desacoplamiento entre microservicios.

    Attributes:
        OPEN (str): Constante de estado — ticket abierto y pendiente.
        IN_PROGRESS (str): Constante de estado — ticket en proceso de resolución.
        CLOSED (str): Constante de estado — ticket cerrado/resuelto.
        STATUS_CHOICES (list): Opciones válidas para el campo ``status``.
        title (CharField): Título descriptivo del ticket (máx. 255 caracteres).
        description (TextField): Descripción detallada del problema o solicitud.
        status (CharField): Estado actual del ticket; por defecto ``OPEN``.
        user_id (CharField): Identificador del usuario creador. Referencia
            lógica al servicio de usuarios (no FK), permitiendo independencia
            entre bases de datos de microservicios.
        created_at (DateTimeField): Fecha y hora de creación (auto-generada).
    """

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


class TicketResponse(models.Model):
    """Respuesta de administrador a un ticket.

    Persiste las respuestas creadas a través del AddTicketResponseUseCase.
    El PK autogenerado se usa como response_id en el evento TicketResponseAdded.
    """

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    admin_id = models.CharField(max_length=255)
    text = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Response #{self.pk} on Ticket #{self.ticket_id}"