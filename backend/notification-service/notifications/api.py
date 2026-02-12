"""
ViewSet refactorizado para usar DDD/EDA.
Las vistas ahora son thin controllers que delegan a casos de uso.
NO contienen lógica de negocio, NO acceden directamente al ORM.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer
from .application.use_cases import (
    MarkNotificationAsReadUseCase,
    MarkNotificationAsReadCommand
)
from .infrastructure.repository import DjangoNotificationRepository
from .infrastructure.event_publisher import RabbitMQEventPublisher
from .domain.exceptions import (
    DomainException,
    NotificationNotFound
)


class NotificationViewSet(viewsets.ModelViewSet):
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
    
    queryset = Notification.objects.all().order_by('-sent_at')
    serializer_class = NotificationSerializer
    
    def __init__(self, *args, **kwargs):
        """Inicializa las dependencias (repositorio, event publisher, use cases)."""
        super().__init__(*args, **kwargs)
        
        # Inyección de dependencias
        self.repository = DjangoNotificationRepository()
        self.event_publisher = RabbitMQEventPublisher()
        
        # Casos de uso
        self.mark_as_read_use_case = MarkNotificationAsReadUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )

    @action(detail=True, methods=['patch'], url_path='read')
    def read(self, request, pk=None):
        """
        Marca una notificación como leída ejecutando el caso de uso.
        Aplica reglas de negocio del dominio.
        """
        try:
            # Crear comando
            command = MarkNotificationAsReadCommand(
                notification_id=int(pk)
            )
            
            # Ejecutar caso de uso
            domain_notification = self.mark_as_read_use_case.execute(command)
            
            # Convertir entidad de dominio a modelo Django para respuesta (sin contenido)
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except NotificationNotFound as e:
            # Notificación no encontrada
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except DomainException as e:
            # Otras excepciones de dominio
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
