from django.db import models


class Notification(models.Model):
    ticket_id = models.CharField(max_length=128, db_index=True)
    message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"Notification for {self.ticket_id} at {self.sent_at.isoformat()}"
