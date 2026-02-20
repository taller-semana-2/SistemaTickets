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

    PRIORITY_UNASSIGNED = "Unassigned"
    PRIORITY_LOW = "Low"
    PRIORITY_MEDIUM = "Medium"
    PRIORITY_HIGH = "High"

    PRIORITY_CHOICES = [
        (PRIORITY_UNASSIGNED, "Unassigned"),
        (PRIORITY_LOW, "Low"),
        (PRIORITY_MEDIUM, "Medium"),
        (PRIORITY_HIGH, "High"),
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
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_UNASSIGNED,
    )
    priority_justification = models.TextField(
        blank=True,
        null=True,
    )