"""
Excepciones de dominio - Representan violaciones de reglas de negocio.
"""


class DomainException(Exception):
    """Excepción base para errores de dominio."""
    pass


class InvalidTicketStateTransition(DomainException):
    """Se lanza cuando se intenta una transición de estado inválida."""
    
    def __init__(self, current_status: str, new_status: str):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(
            f"No se puede cambiar el estado de un ticket {current_status} a {new_status}"
        )


class TicketAlreadyClosed(DomainException):
    """Se lanza cuando se intenta modificar un ticket cerrado."""
    
    def __init__(self, ticket_id: int):
        self.ticket_id = ticket_id
        super().__init__(
            f"El ticket {ticket_id} está cerrado y no puede ser modificado"
        )


class InvalidTicketData(DomainException):
    """Se lanza cuando los datos del ticket son inválidos."""
    pass


class InvalidPriorityTransition(DomainException):
    """Se lanza cuando se intenta una transición de prioridad inválida."""
    
    def __init__(self, current_priority: str, new_priority: str, reason: str):
        self.current_priority = current_priority
        self.new_priority = new_priority
        super().__init__(
            f"No se puede cambiar la prioridad de '{current_priority}' a '{new_priority}': {reason}"
        )


class EmptyResponseError(DomainException):
    """Se lanza cuando se intenta crear una respuesta con texto vacío."""
    
    def __init__(self):
        super().__init__("El texto de la respuesta es obligatorio")


class ResponseTooLongError(DomainException):
    """Se lanza cuando el texto de a respuesta excede el límite de caracteres."""
    
    def __init__(self, max_length: int = 2000):
        self.max_length = max_length
        super().__init__(f"El texto de la respuesta no puede exceder {max_length} caracteres")
