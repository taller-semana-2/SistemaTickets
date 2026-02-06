from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ticket
from .serializer import TicketSerializer
from .messaging.events import publish_ticket_created


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().order_by("-created_at")
    serializer_class = TicketSerializer

    def perform_create(self, serializer):
        ticket = serializer.save()
        publish_ticket_created(ticket.id)

    @action(detail=True, methods=["patch"], url_path="status")
    def change_status(self, request, pk=None):
        ticket = self.get_object()

        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"error": "El campo 'status' es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ticket.status = new_status
        ticket.save(update_fields=["status"])

        return Response(
            TicketSerializer(ticket).data,
            status=status.HTTP_200_OK,
        )
