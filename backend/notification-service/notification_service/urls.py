from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notifications.api import NotificationViewSet
from notifications.infrastructure.sse_view import sse_notifications_view

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/notifications/sse/<str:user_id>/', sse_notifications_view, name='sse-notifications'),
]

