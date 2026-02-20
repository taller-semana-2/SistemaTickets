"""
Use Cases (Comandos) - Casos de uso que orquestan operaciones de dominio.
Cada caso de uso representa una operación de negocio completa.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

from ..domain.entities import Notification
from ..domain.repositories import NotificationRepository
from ..domain.event_publisher import EventPublisher
from ..domain.exceptions import NotificationNotFound, InvalidEventSchema


logger = logging.getLogger(__name__)


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


@dataclass
class CreateNotificationFromResponseCommand:
    """Comando: Crear notificación a partir de un evento ticket.response_added."""
    event_type: Optional[str]
    ticket_id: Optional[int]
    response_id: Optional[int]
    admin_id: Optional[int]
    response_text: Optional[str]
    user_id: Optional[int]
    timestamp: Optional[str]


class CreateNotificationFromResponseUseCase:
    """
    Caso de uso: Crear notificación cuando un admin responde un ticket.

    Responsabilidades:
    1. Validar el schema del evento (campos obligatorios)
    2. Garantizar idempotencia mediante response_id (evita duplicados)
    3. Crear la entidad Notification de dominio
    4. Persistir la notificación mediante el repositorio
    """

    REQUIRED_FIELDS = ["ticket_id", "response_id", "admin_id", "response_text", "user_id", "timestamp"]

    def __init__(self, repository: NotificationRepository):
        """
        Inyección de dependencias (DIP).

        Args:
            repository: Repositorio para persistencia de notificaciones
        """
        self.repository = repository

    def _validate_schema(self, command: CreateNotificationFromResponseCommand) -> None:
        """
        Valida que el comando contenga todos los campos obligatorios.

        Args:
            command: Comando con los datos del evento

        Raises:
            InvalidEventSchema: Si faltan campos obligatorios en el evento
        """
        missing = [
            field for field in self.REQUIRED_FIELDS
            if getattr(command, field, None) is None
        ]
        if missing:
            logger.warning("Schema inválido en evento ticket.response_added: campos faltantes=%s", missing)
            raise InvalidEventSchema(missing_fields=missing)

    def execute(self, command: CreateNotificationFromResponseCommand) -> Notification:
        """
        Ejecuta la creación de notificación desde un evento de respuesta.

        Args:
            command: Comando con los datos del evento

        Returns:
            La notificación creada y persistida

        Raises:
            InvalidEventSchema: Si faltan campos obligatorios en el evento
        """
        # 1. Validar schema del evento
        self._validate_schema(command)

        # 2. Idempotencia: verificar si ya existe notificación para este response_id
        existing = self.repository.find_by_response_id(command.response_id)
        if existing is not None:
            logger.info("Idempotencia: notificación ya existe para response_id=%s, omitiendo creación", command.response_id)
            return existing

        # 3. Crear entidad de dominio
        notification = Notification(
            id=None,
            ticket_id=str(command.ticket_id),
            message=f"Nueva respuesta en Ticket #{command.ticket_id}",
            sent_at=datetime.now(),
            read=False,
            user_id=str(command.user_id),
            response_id=command.response_id,
        )

        # 4. Persistir
        notification = self.repository.save(notification)
        logger.info("Notificación creada para ticket_id=%s, response_id=%s", command.ticket_id, command.response_id)

        return notification


@dataclass
class DeleteNotificationCommand:
    """Comando: Eliminar una notificación por ID."""
    notification_id: int

class DeleteNotificationUseCase:
    """Caso de uso: Eliminar una notificación de forma permanente."""
    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    def execute(self, command: DeleteNotificationCommand) -> None:
        if not self.repository.delete(command.notification_id):
            raise NotificationNotFound(command.notification_id)
        logger.info("Notificación %s eliminada.", command.notification_id)


@dataclass
class ClearAllNotificationsCommand:
    """Comando: Eliminar todas las notificaciones."""
    user_id: Optional[str] = None

class ClearAllNotificationsUseCase:
    """Caso de uso: Limpiar todas las notificaciones pertenecientes a un usuario visible, o todas."""
    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    def execute(self, command: ClearAllNotificationsCommand) -> None:
        self.repository.delete_all(command.user_id)
        logger.info("Todas las notificaciones %shan sido eliminadas.", f"para el usuario {command.user_id} " if command.user_id else "")
