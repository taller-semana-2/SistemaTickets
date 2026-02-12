"""
URL configuration for user_service project.

La configuración de URLs del proyecto incluye:
- /admin/: Interfaz de administración de Django
- /api/: Rutas de la API REST de la aplicación users

Para microservicios, todas las rutas de API deben estar bajo /api/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API de la aplicación users
    # Las rutas de users se configuran en users/urls.py
    path('', include('users.urls')),  # incluye las rutas /api/users/
]
