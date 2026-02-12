"""
users/urls.py

📋 CAPA DE PRESENTACIÓN - Routing

🎯 PROPÓSITO:
Define las rutas de la API REST.

✅ EJEMPLO de lo que DEBE ir aquí:
    from django.urls import path, include
    from rest_framework.routers import DefaultRouter
    from .views import UserViewSet
    
    # Configurar router de DRF
    router = DefaultRouter()
    router.register(r'users', UserViewSet, basename='user')
    
    urlpatterns = [
        path('api/', include(router.urls)),
    ]
    
    # Esto genera automáticamente las rutas:
    # POST   /api/users/                    → create()
    # GET    /api/users/                    → list()
    # GET    /api/users/{id}/               → retrieve()
    # PUT    /api/users/{id}/               → update()
    # PATCH  /api/users/{id}/               → partial_update()
    # DELETE /api/users/{id}/               → destroy()
    # POST   /api/users/{id}/deactivate/   → deactivate() [custom action]

💡 Los routers de DRF generan las URLs automáticamente siguiendo convenciones REST.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('api/', include(router.urls)),
]
