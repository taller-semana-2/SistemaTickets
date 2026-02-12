"""
users/admin.py

📋 ADMIN DE DJANGO

🎯 PROPÓSITO:
Configurar la interfaz de administración de Django para gestionar usuarios.

💡 El admin de Django es útil para operaciones manuales y debugging en desarrollo.
"""

from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('username', 'email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'username', 'email')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
