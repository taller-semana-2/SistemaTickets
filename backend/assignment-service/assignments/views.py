from rest_framework import viewsets
from .models import TicketAssignment
from .serializers import TicketAssignmentSerializer

class TicketAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TicketAssignment.objects.all().order_by('-assigned_at')
    serializer_class = TicketAssignmentSerializer
