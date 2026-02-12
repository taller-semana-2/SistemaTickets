"""
domain/exceptions.py

🎯 PROPÓSITO:
Define las excepciones específicas del dominio que representan reglas de negocio violadas.

📐 ESTRUCTURA:
- Excepciones personalizadas que heredan de Exception
- Tienen nombres descriptivos del problema de negocio
- Pueden incluir información contextual

✅ EJEMPLO de lo que DEBE ir aquí:
    class DomainException(Exception):
        '''Excepción base para errores de dominio'''
        pass
    
    class InvalidEmail(DomainException):
        def __init__(self, email: str):
            super().__init__(f"Email inválido: {email}")
            self.email = email
    
    class UserAlreadyExists(DomainException):
        def __init__(self, email: str):
            super().__init__(f"Ya existe un usuario con el email: {email}")
            self.email = email
    
    class UserAlreadyInactive(DomainException):
        def __init__(self):
            super().__init__("El usuario ya está inactivo")

💡 Las excepciones de dominio representan violaciones de reglas de negocio, NO errores técnicos.
"""
