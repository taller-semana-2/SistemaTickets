"""
ViewSet refactorizado para usar DDD/EDA.
Las vistas ahora son thin controllers que delegan a casos de uso.
NO contienen lógica de negocio, NO acceden directamente al ORM.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ticket
from .serializer import TicketSerializer
from .application.use_cases import (
    CreateTicketUseCase,
    CreateTicketCommand,
    ChangeTicketStatusUseCase,
    ChangeTicketStatusCommand
)
from .infrastructure.repository import DjangoTicketRepository
from .infrastructure.event_publisher import RabbitMQEventPublisher
from .domain.exceptions import (
    DomainException,
    TicketAlreadyClosed,
    InvalidTicketData
)


class TicketViewSet(viewsets.ModelViewSet):
    """
    ViewSet refactorizado siguiendo principios DDD/EDA.
    
    Responsabilidades:
    - Validar entrada HTTP
    - Ejecutar casos de uso
    - Traducir respuestas de dominio a HTTP
    - Manejar excepciones de dominio
    
    NO responsable de:
    - Lógica de negocio (en entidades y casos de uso)
    - Persistencia directa (delegada al repositorio)
    - Publicación de eventos (delegada al event publisher)
    """
    
    queryset = Ticket.objects.all().order_by("-created_at")
    serializer_class = TicketSerializer
    
    def __init__(self, *args, **kwargs):
        """Inicializa las dependencias (repositorio, event publisher, use cases)."""
        super().__init__(*args, **kwargs)
        
        # Inyección de dependencias
        self.repository = DjangoTicketRepository()
        self.event_publisher = RabbitMQEventPublisher()
        
        # Casos de uso
        self.create_ticket_use_case = CreateTicketUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        self.change_status_use_case = ChangeTicketStatusUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
    
    def perform_create(self, serializer):
        """
        Crea un ticket ejecutando el caso de uso correspondiente.
        NO guarda directamente, delega al caso de uso.
        """
        try:
            # Crear comando desde los datos validados
            command = CreateTicketCommand(
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description']
            )
            
            # Ejecutar caso de uso (maneja dominio, persistencia y eventos)
            domain_ticket = self.create_ticket_use_case.execute(command)
            
            # Actualizar el serializer con la instancia Django para la respuesta
            # (DRF espera una instancia del modelo Django)
            django_ticket = Ticket.objects.get(pk=domain_ticket.id)
            serializer.instance = django_ticket
            
        except InvalidTicketData as e:
            # Convertir excepción de dominio a error de validación DRF
            from rest_framework.exceptions import ValidationError
            raise ValidationError(str(e))
    
    @action(detail=True, methods=["patch"], url_path="status")
    def change_status(self, request, pk=None):
        """
        Cambia el estado de un ticket ejecutando el caso de uso.
        Aplica reglas de negocio del dominio.
        """
        new_status = request.data.get("status")
        
        # Validación de entrada HTTP
        if not new_status:
            return Response(
                {"error": "El campo 'status' es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            # Crear comando
            command = ChangeTicketStatusCommand(
                ticket_id=int(pk),
                new_status=new_status
            )
            
            # Ejecutar caso de uso
            domain_ticket = self.change_status_use_case.execute(command)
            
            # Obtener instancia Django para serializar
            django_ticket = Ticket.objects.get(pk=domain_ticket.id)
            
            return Response(
                TicketSerializer(django_ticket).data,
                status=status.HTTP_200_OK,
            )
            
        except TicketAlreadyClosed as e:
            # Ticket cerrado: regla de negocio violada
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as e:
            # Estado inválido o ticket no encontrado
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DomainException as e:
            # Otras excepciones de dominio
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
