"""
Excepciones de dominio - Representan violaciones de reglas de negocio del dominio User.
Estas excepciones son parte del lenguaje ubicuo del dominio (Domain Exception).
"""


class DomainException(Exception):
    """Excepción base para todos los errores de dominio."""
    pass


class InvalidEmail(DomainException):
    """Se lanza cuando el email proporcionado no es válido."""
    
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email inválido: {email}")


class InvalidUsername(DomainException):
    """Se lanza cuando el username no cumple con las reglas de negocio."""
    
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"Username inválido: {username}. Debe tener al menos 3 caracteres.")


class UserAlreadyExists(DomainException):
    """Se lanza cuando se intenta crear un usuario con un email ya registrado."""
    
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Ya existe un usuario con el email: {email}")


class UserAlreadyInactive(DomainException):
    """Se lanza cuando se intenta desactivar un usuario ya inactivo (violación de idempotencia)."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"El usuario {user_id} ya está inactivo")


class UserNotFound(DomainException):
    """Se lanza cuando no se encuentra un usuario por su ID."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"Usuario {user_id} no encontrado")


class InvalidUserData(DomainException):
    """Se lanza cuando los datos del usuario son inválidos."""
    pass
