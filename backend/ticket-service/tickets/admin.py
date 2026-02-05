from django.contrib import admin

# Register your models here.
from .models import Ticket

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description")