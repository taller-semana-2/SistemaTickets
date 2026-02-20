"""
users/urls.py — Presentation Layer (Routing)

Defines REST API routes for the users-service.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import HealthCheckView, AuthViewSet, CookieTokenRefreshView

# Router for ViewSets
router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),

    # Auth endpoints (router-generated)
    path('', include(router.urls)),

    # Custom login route (action mapping)
    path('auth/login/', AuthViewSet.as_view({'post': 'login'}), name='auth-login'),

    # Me endpoint — requires authentication (cookie-based)
    path('auth/me/', AuthViewSet.as_view({'get': 'me'}), name='auth-me'),

    # Logout endpoint — clears cookies
    path('auth/logout/', AuthViewSet.as_view({'post': 'logout'}), name='auth-logout'),

    # Token refresh — reads refresh_token from cookie
    path('auth/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
]

