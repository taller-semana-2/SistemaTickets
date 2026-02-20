"""
Excepciones de dominio - Errores que representan violaciones de reglas de negocio.
"""


class DomainException(Exception):
    """Clase base para todas las excepciones de dominio."""
    pass


class NotificationAlreadyRead(DomainException):
    """Se intentó marcar como leída una notificación que ya estaba leída."""
    
    def __init__(self, notification_id: int):
        self.notification_id = notification_id
        super().__init__(f"La notificación {notification_id} ya está marcada como leída")


class NotificationNotFound(DomainException):
    """La notificación solicitada no existe."""
    
    def __init__(self, notification_id: int):
        self.notification_id = notification_id
        super().__init__(f"Notificación {notification_id} no encontrada")


class InvalidEventSchema(DomainException):
    """El evento recibido no contiene todos los campos obligatorios."""

    def __init__(self, missing_fields: list):
        self.missing_fields = missing_fields
        fields_str = ", ".join(missing_fields)
        super().__init__(f"Campos obligatorios faltantes en el evento: {fields_str}")
