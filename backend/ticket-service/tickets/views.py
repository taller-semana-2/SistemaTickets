"""
ViewSet refactorizado para usar DDD/EDA.
Las vistas ahora son thin controllers que delegan a casos de uso.
NO contienen lógica de negocio, NO acceden directamente al ORM.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ticket, TicketResponse
from .serializer import TicketSerializer, TicketResponseSerializer
from .application.use_cases import (
    CreateTicketUseCase,
    CreateTicketCommand,
    ChangeTicketStatusUseCase,
    ChangeTicketStatusCommand,
<<<<<<< feature/sistema_de_notificaciones
    AddTicketResponseUseCase,
    AddTicketResponseCommand,
=======
    ChangeTicketPriorityUseCase,
    ChangeTicketPriorityCommand
>>>>>>> develop
)
from .infrastructure.repository import DjangoTicketRepository
from .infrastructure.event_publisher import RabbitMQEventPublisher
from .domain.exceptions import (
    DomainException,
    TicketAlreadyClosed,
    InvalidTicketData,
<<<<<<< feature/sistema_de_notificaciones
    EmptyResponseError,
=======
    InvalidPriorityTransition
>>>>>>> develop
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
<<<<<<< feature/sistema_de_notificaciones
        self.add_response_use_case = AddTicketResponseUseCase(
=======
        self.change_priority_use_case = ChangeTicketPriorityUseCase(
>>>>>>> develop
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
                description=serializer.validated_data['description'],
                user_id=serializer.validated_data['user_id']
            )
            
            # Ejecutar caso de uso (maneja dominio, persistencia y eventos)
            domain_ticket = self.create_ticket_use_case.execute(command)
            
            # Convertir entidad de dominio a modelo Django para serialización
            # (DRF espera una instancia del modelo Django)
            django_ticket = self.repository.to_django_model(domain_ticket)
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
            
            # Convertir entidad de dominio a modelo Django para serialización
            django_ticket = self.repository.to_django_model(domain_ticket)
            
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
    
    @action(detail=True, methods=["patch"], url_path="priority")
    def change_priority(self, request, pk=None):
        """
        Cambia la prioridad de un ticket ejecutando el caso de uso.
        Aplica reglas de negocio del dominio (transiciones válidas, permisos).

        PATCH /api/tickets/{id}/priority/

        Body params:
            - priority (str, requerido): Nueva prioridad del ticket.
            - justification (str, opcional): Justificación del cambio.
            - user_role (str, opcional): Rol del usuario que solicita el cambio.

        Errores:
            - 400: Campo 'priority' ausente, ticket cerrado, transición inválida.
            - 403: Permiso denegado (excepción de dominio).
        """
        new_priority = request.data.get("priority")
        justification = request.data.get("justification")
        user_role = request.data.get("user_role")

        # Validación de entrada HTTP
        if not new_priority:
            return Response(
                {"error": "El campo 'priority' es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Crear comando
            command = ChangeTicketPriorityCommand(
                ticket_id=int(pk),
                new_priority=new_priority
            )
            command.justification = justification
            command.user_role = user_role

            # Ejecutar caso de uso
            domain_ticket = self.change_priority_use_case.execute(command)

            # Convertir entidad de dominio a modelo Django para serialización
            django_ticket = self.repository.to_django_model(domain_ticket)

            return Response(
                TicketSerializer(django_ticket).data,
                status=status.HTTP_200_OK,
            )

        except (TicketAlreadyClosed, InvalidPriorityTransition) as e:
            # Regla de negocio violada: ticket cerrado o transición de prioridad inválida
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as e:
            # Valor inválido o ticket no encontrado
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except DomainException as e:
            # Otras excepciones de dominio (ej. permiso denegado)
            return Response(
                {"error": str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )

    @action(detail=False, methods=["get"], url_path="my-tickets/(?P<user_id>[^/.]+)")
    def my_tickets(self, request, user_id=None):
        """
        Obtiene todos los tickets de un usuario específico.
        
        GET /api/tickets/my-tickets/{user_id}/
        
        Args:
            user_id: ID del usuario cuyos tickets se quieren obtener
            
        Returns:
            Lista de tickets del usuario
        """
        try:
            # Filtrar tickets por user_id
            tickets = Ticket.objects.filter(user_id=user_id).order_by("-created_at")
            
            # Serializar y retornar
            serializer = TicketSerializer(tickets, many=True)
            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
            
        except Exception as e:
            return Response(
                {"error": f"Error al obtener tickets: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get", "post"], url_path="responses")
    def responses(self, request, pk: str | None = None) -> Response:
        """Punto de entrada para respuestas de administrador en un ticket.

        GET  /api/tickets/{id}/responses/ — Lista respuestas (HU-1.2).
        POST /api/tickets/{id}/responses/ — Crea respuesta de admin (HU-1.1).

        Args:
            request: Objeto HTTP de DRF.
            pk: ID del ticket.

        Returns:
            Response con lista de respuestas o la respuesta creada.
        """
        if request.method == "GET":
            return self._list_responses(pk)
        return self._create_response(request, pk)

    def _list_responses(self, ticket_id: str | None) -> Response:
        """Lista respuestas de un ticket en orden cronológico ascendente.

        Accede directamente al ORM para lecturas simples, siguiendo el
        patrón ya establecido en ``my_tickets``.

        Args:
            ticket_id: ID del ticket cuyas respuestas se listan.

        Returns:
            Response 200 con lista serializada de respuestas.
        """
        responses = TicketResponse.objects.filter(
            ticket_id=ticket_id,
        ).order_by("created_at")
        serializer = TicketResponseSerializer(responses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _create_response(self, request, ticket_id: str | None) -> Response:
        """Crea una respuesta de administrador delegando al caso de uso.

        Flujo:
        1. Valida entrada con ``TicketResponseSerializer``.
        2. Ejecuta ``AddTicketResponseUseCase`` (reglas de dominio + evento).
        3. Persiste ``TicketResponse`` en el modelo Django.
        4. Retorna la respuesta creada.

        Note:
            El evento ``TicketResponseAdded`` se publica dentro del caso de
            uso con ``response_id=0`` porque el ID real solo existe tras la
            persistencia del modelo Django.  Esto es una limitación conocida:
            el dominio no debe depender de infraestructura, por lo que el
            response_id real no puede inyectarse sin refactorizar el caso de
            uso.  Se registra como deuda técnica para resolución futura.

        Args:
            request: Objeto HTTP de DRF con ``text`` y ``admin_id``.
            ticket_id: ID del ticket al que se agrega la respuesta.

        Returns:
            Response 201 con la respuesta creada, o 400 ante error de dominio.

        Raises:
            No lanza excepciones; todas se traducen a respuestas HTTP.
        """
        serializer = TicketResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        admin_id: str = serializer.validated_data["admin_id"]
        text: str = serializer.validated_data["text"]

        try:
            command = AddTicketResponseCommand(
                ticket_id=int(ticket_id),
                text=text,
                admin_id=admin_id,
            )
            self.add_response_use_case.execute(command)

            # Persistir en modelo Django (el caso de uso opera sobre entidades
            # de dominio; la capa de infraestructura ORM vive aquí).
            ticket = Ticket.objects.get(pk=ticket_id)
            response_obj = TicketResponse.objects.create(
                ticket=ticket,
                admin_id=admin_id,
                text=text,
            )

            output_serializer = TicketResponseSerializer(response_obj)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except Ticket.DoesNotExist:
            return Response(
                {"error": f"Ticket {ticket_id} no encontrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TicketAlreadyClosed as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except EmptyResponseError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except DomainException as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
