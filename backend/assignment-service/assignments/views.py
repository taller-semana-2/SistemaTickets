from rest_framework import viewsets
from .models import TicketAssignment
from .serializers import TicketAssignmentSerializer


class TicketAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """API de solo lectura para ver asignaciones de tickets"""
    queryset = TicketAssignment.objects.all().order_by('-assigned_at')
    serializer_class = TicketAssignmentSerializer
