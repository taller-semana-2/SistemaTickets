from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'sent_at')
    search_fields = ('ticket_id',)
