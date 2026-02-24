"""Serializadores REST para el servicio de tickets.

Provee la capa de serialización/deserialización entre las instancias
del modelo :class:`~tickets.models.Ticket` y las representaciones
JSON expuestas por la API REST.
"""

from rest_framework import serializers
from .models import Ticket, TicketResponse
from .domain.factories import _contains_dangerous_html


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

    def validate_title(self, value: str) -> str:
        """
        Valida que el título no contenga HTML o scripts peligrosos.
        
        Esta validación es una capa defensiva adicional. La validación principal
        ocurre en la capa de dominio (TicketFactory).
        
        Args:
            value: Título a validar
            
        Returns:
            El valor validado
            
        Raises:
            serializers.ValidationError: Si el título contiene caracteres peligrosos
        """
        if _contains_dangerous_html(value):
            raise serializers.ValidationError(
                "El título contiene caracteres HTML o scripts no permitidos"
            )
        return value
    
    def validate_description(self, value: str) -> str:
        """
        Valida que la descripción no contenga HTML o scripts peligrosos.
        
        Esta validación es una capa defensiva adicional. La validación principal
        ocurre en la capa de dominio (TicketFactory).
        
        Args:
            value: Descripción a validar
            
        Returns:
            El valor validado
            
        Raises:
            serializers.ValidationError: Si la descripción contiene caracteres peligrosos
        """
        if _contains_dangerous_html(value):
            raise serializers.ValidationError(
                "La descripción contiene caracteres HTML o scripts no permitidos"
            )
        return value

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = ("priority", "priority_justification")


class TicketResponseSerializer(serializers.ModelSerializer):
    """Serializer para respuestas de administrador en tickets.

    Validaciones explícitas:
    - ``text``: obligatorio, no vacío, máximo 2000 caracteres.
    - ``admin_id``: obligatorio, no vacío.
    - ``id``, ``ticket``, ``created_at``: solo lectura (asignados por el sistema).
    """

    text: serializers.CharField = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=2000,
        help_text="Texto de la respuesta del administrador (máx. 2000 caracteres).",
    )
    admin_id: serializers.CharField = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=255,
        help_text="Identificador del administrador que responde.",
    )

    class Meta:
        model = TicketResponse
        fields: list[str] = ["id", "ticket", "admin_id", "text", "created_at"]
        read_only_fields: list[str] = ["id", "ticket", "created_at"]
