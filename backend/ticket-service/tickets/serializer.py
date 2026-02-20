"""Serializadores REST para el servicio de tickets.

Provee la capa de serialización/deserialización entre las instancias
del modelo :class:`~tickets.models.Ticket` y las representaciones
JSON expuestas por la API REST.
"""

from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    """Serializador para el modelo Ticket.

    Convierte instancias de :class:`~tickets.models.Ticket` a/desde
    representaciones JSON. Expone **todos** los campos del modelo:
    ``id``, ``title``, ``description``, ``status``, ``user_id``,
    ``created_at``, ``priority`` y ``priority_justification``.

    Los campos ``priority`` y ``priority_justification`` son de **solo
    lectura**: se incluyen en las respuestas pero se ignoran en
    operaciones de creación/actualización convencionales.  Solo pueden
    modificarse a través del endpoint dedicado de priorización.

    Note:
        Utiliza ``fields = "__all__"`` para exponer la totalidad de los
        campos. Si se agregan campos sensibles al modelo en el futuro,
        se debe migrar a una lista explícita de campos.
    """

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = ("priority", "priority_justification")