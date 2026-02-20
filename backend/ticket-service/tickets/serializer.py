"""Serializadores REST para el servicio de tickets.

Provee la capa de serialización/deserialización entre las instancias
del modelo :class:`~tickets.models.Ticket` y las representaciones
JSON expuestas por la API REST.
"""

from rest_framework import serializers
from .models import Ticket, TicketResponse


class TicketSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Ticket.

    Convierte instancias de :class:`~tickets.models.Ticket` a/desde
    representaciones JSON. Expone **todos** los campos del modelo:
    ``id``, ``title``, ``description``, ``status``, ``user_id`` y
    ``created_at``.

    Note:
        Utiliza ``fields = "__all__"`` para exponer la totalidad de los
        campos. Si se agregan campos sensibles al modelo en el futuro,
        se debe migrar a una lista explícita de campos.
    """

    class Meta:
        model = Ticket
        fields = "__all__"


class TicketResponseSerializer(serializers.ModelSerializer):
    """Serializer para respuestas de admin en tickets.

    Valida: texto obligatorio, máximo 2000 caracteres, admin_id obligatorio.
    Los campos ticket, id, created_at son de solo lectura.
    """

    class Meta:
        model = TicketResponse
        fields = ["id", "ticket", "admin_id", "text", "created_at"]
        read_only_fields = ["id", "ticket", "created_at"]