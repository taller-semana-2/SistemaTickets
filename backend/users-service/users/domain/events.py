"""
domain/events.py

🎯 PROPÓSITO:
Define los eventos de dominio que representan hechos relevantes del negocio.

📐 ESTRUCTURA:
- Eventos = Notificaciones de que algo importante ocurrió en el dominio
- Son inmutables (datos que no cambian)
- Tienen nombres en pasado (UserCreated, UserDeactivated)
- Contienen solo la información necesaria

✅ EJEMPLO de lo que DEBE ir aquí:
    from dataclasses import dataclass
    from datetime import datetime
    
    @dataclass(frozen=True)  # frozen=True hace el objeto inmutable
    class UserCreated:
        user_id: str
        email: str
        username: str
        occurred_at: datetime
    
    @dataclass(frozen=True)
    class UserDeactivated:
        user_id: str
        reason: str
        occurred_at: datetime

💡 Los eventos se publican después de operaciones exitosas para notificar a otros servicios.
"""
