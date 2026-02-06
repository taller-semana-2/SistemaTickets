from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notifications.api import NotificationViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]

