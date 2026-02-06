from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketAssignmentViewSet

router = DefaultRouter()
router.register(r'assignments', TicketAssignmentViewSet, basename='assignment')

urlpatterns = [
    path('', include(router.urls)),
]
