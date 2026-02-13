from rest_framework import serializers
from .models import TicketAssignment


class TicketAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketAssignment
        fields = ['id', 'ticket_id', 'priority', 'assigned_at', 'assigned_to']
        read_only_fields = ['id', 'assigned_at']
