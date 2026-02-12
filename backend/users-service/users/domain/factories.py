"""
domain/factories.py

🎯 PROPÓSITO:
Factories que encapsulan la lógica compleja de creación de entidades del dominio.

📐 ESTRUCTURA:
- Validan datos de entrada
- Aplican reglas de negocio de creación
- Devuelven entidades completamente válidas
- Lanzan excepciones de dominio si algo está mal

✅ EJEMPLO de lo que DEBE ir aquí:
    from typing import Optional
    from .entities import User
    from .exceptions import InvalidEmail, InvalidUsername
    import uuid
    
    class UserFactory:
        @staticmethod
        def create(email: str, username: str, password: str) -> User:
            '''Crea un nuevo usuario validando todas las reglas de negocio'''
            
            # Validaciones de negocio
            if not email or '@' not in email:
                raise InvalidEmail(email)
            
            if not username or len(username) < 3:
                raise InvalidUsername(username)
            
            if len(password) < 8:
                raise WeakPassword()
            
            # Generar ID único
            user_id = str(uuid.uuid4())
            
            # Crear entidad válida
            return User(
                id=user_id,
                email=email.lower(),  # Normalización
                username=username.strip(),
                is_active=True  # Estado inicial
            )

💡 Las factories garantizan que nunca se creen entidades en estado inválido.
"""
