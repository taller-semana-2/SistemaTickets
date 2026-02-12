"""
users/models.py

📋 CAPA DE PERSISTENCIA - Modelos Django ORM

🎯 PROPÓSITO:
Define SOLO la estructura de persistencia en base de datos.

⚠️ IMPORTANTE:
- Este modelo es SOLO para persistencia
- La entidad de dominio (domain/entities.py) contiene la lógica de negocio
- El repositorio (infrastructure/repository.py) traduce entre ambos

📐 ESTRUCTURA:
- Hereda de django.db.models.Model
- Define campos y tipos de datos
- Define restricciones de base de datos (unique, indexes)
- NO contiene lógica de negocio

❌ NO debe:
- Contener métodos de negocio (como .deactivate())
- Tener validaciones de negocio
- Publicar eventos

💡 El modelo Django es un "recipiente" para datos. La lógica vive en el dominio.
"""

from django.db import models
import uuid


class User(models.Model):
    """Modelo Django para persistir usuarios en la base de datos"""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(
        unique=True,
        max_length=255,
        db_index=True
    )
    username = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )
    password_hash = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.email})"
