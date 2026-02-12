"""
Use Cases (Comandos) - Casos de uso que orquestan operaciones de dominio.
Cada caso de uso representa una operación de negocio completa.
"""

from dataclasses import dataclass

from ..domain.entities import Notification
from ..domain.repositories import NotificationRepository
from ..domain.event_publisher import EventPublisher
from ..domain.exceptions import NotificationNotFound


@dataclass
class MarkNotificationAsReadCommand:
    """Comando: Marcar una notificación como leída."""
    notification_id: int


class MarkNotificationAsReadUseCase:
    """
    Caso de uso: Marcar una notificación como leída.
    
    Responsabilidades:
    1. Obtener la notificación del repositorio
    2. Aplicar el cambio de estado (reglas de negocio)
    3. Persistir el cambio
    4. Publicar eventos de dominio generados
    """
    
    def __init__(
        self,
        repository: NotificationRepository,
        event_publisher: EventPublisher
    ):
        """
        Inyección de dependencias (DIP).
        
        Args:
            repository: Repositorio para persistencia
            event_publisher: Publicador de eventos
        """
        self.repository = repository
        self.event_publisher = event_publisher
    
    def execute(self, command: MarkNotificationAsReadCommand) -> Notification:
        """
        Ejecuta el caso de uso de marcar como leída.
        
        Args:
            command: Comando con el ID de la notificación
            
        Returns:
            La notificación actualizada
            
        Raises:
            NotificationNotFound: Si la notificación no existe
        """
        # 1. Obtener la notificación
        notification = self.repository.find_by_id(command.notification_id)
        
        if not notification:
            raise NotificationNotFound(command.notification_id)
        
        # 2. Aplicar cambio de estado (reglas de negocio en la entidad)
        notification.mark_as_read()
        
        # 3. Persistir el cambio
        notification = self.repository.save(notification)
        
        # 4. Recolectar y publicar eventos de dominio generados
        events = notification.collect_domain_events()
        for event in events:
            self.event_publisher.publish(event)
        
        return notification
