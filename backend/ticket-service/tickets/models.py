from django.db import models

# Create your models here.
class Ticket(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(default="OPEN", max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
