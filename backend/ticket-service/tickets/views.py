from rest_framework import viewsets
from .models import Ticket
from .serializer import TicketSerializer
from .messaging.events import publish_ticket_created  # Importa la función que creamos

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().order_by("-created_at")
    serializer_class = TicketSerializer

    def perform_create(self, serializer):
        # Guardar ticket en DB
        ticket = serializer.save()
        
        # Publicar evento ticket.created en RabbitMQ
        publish_ticket_created(ticket.id)
