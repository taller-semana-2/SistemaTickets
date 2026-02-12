"""
domain/entities.py

🎯 PROPÓSITO:
Contiene las entidades del dominio con sus reglas de negocio.

📐 ESTRUCTURA:
- Entidades = Objetos con identidad única y ciclo de vida
- Contienen comportamiento, NO son simples contenedores de datos
- Implementan validaciones y reglas de negocio

✅ EJEMPLO de lo que DEBE ir aquí:
    class User:
        def __init__(self, id, email, username, is_active=True):
            self._validate_email(email)
            self._validate_username(username)
            self.id = id
            self.email = email
            self.username = username
            self.is_active = is_active
        
        def deactivate(self):
            '''Regla de negocio: un usuario puede ser desactivado'''
            if not self.is_active:
                raise UserAlreadyInactive()
            self.is_active = False
        
        def _validate_email(self, email):
            if '@' not in email:
                raise InvalidEmail()

❌ NO debe:
- Heredar de django.db.models.Model
- Tener decoradores de Django
- Contener lógica de persistencia

💡 Las entidades son independientes del framework.
"""
