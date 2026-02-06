# assignment_service/admin.py
from django.contrib import admin
from .models import TicketAssignment  # o el modelo que quieres ver

@admin.register(TicketAssignment)
class TicketAssignmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket_id', 'priority', 'assigned_at']
