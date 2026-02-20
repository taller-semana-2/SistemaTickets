"""Modelos del dominio para el servicio de notificaciones.

Define la entidad ``Notification`` que registra eventos de notificación
asociados a tickets del sistema.
"""

from django.db import models


class Notification(models.Model):
    """Modelo que representa una notificación generada por un evento de ticket.

    Cada notificación está vinculada a un ticket mediante ``ticket_id``
    (referencia lógica al ticket-service, no una FK de Django). Se crea
    automáticamente cuando el consumidor RabbitMQ recibe un evento de
    creación de ticket.

    Attributes:
        ticket_id (CharField): Identificador del ticket asociado. Indexado
            para consultas frecuentes de notificaciones por ticket.
        message (TextField): Contenido descriptivo de la notificación.
            Puede estar vacío.
        sent_at (DateTimeField): Fecha y hora de creación (auto-generada).
        read (BooleanField): Indica si la notificación fue leída por el
            usuario. Indexado para filtrar rápidamente no-leídas.
            Por defecto ``False``.
    """

    ticket_id = models.CharField(max_length=128, db_index=True)
    message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False, db_index=True)
    user_id = models.CharField(max_length=128, db_index=True, default='')
    response_id = models.IntegerField(null=True, blank=True, db_index=True)

    def __str__(self):
        """Retorna representación legible de la notificación.

        Returns:
            str: Cadena con formato 'Notification for <ticket_id> at <ISO timestamp>'.
        """
        return f"Notification for {self.ticket_id} at {self.sent_at.isoformat()}"
