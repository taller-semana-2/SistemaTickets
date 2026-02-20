"""
Django Repository - Implementación del repositorio usando Django ORM.
Adaptador que traduce entre el dominio y la persistencia.
"""

from typing import Optional, List

from ..domain.entities import Notification as DomainNotification
from ..domain.repositories import NotificationRepository
from ..models import Notification as DjangoNotification


class DjangoNotificationRepository(NotificationRepository):
    """
    Implementación del repositorio usando Django ORM.
    Traduce entre entidades de dominio y modelos de Django.
    """
    
    def save(self, notification: DomainNotification) -> DomainNotification:
        """
        Persiste una notificación en la base de datos (crear o actualizar).
        
        Args:
            notification: Entidad de dominio
            
        Returns:
            La entidad con el ID asignado
        """
        if notification.id:
            # Actualizar notificación existente
            django_notification = DjangoNotification.objects.get(pk=notification.id)
            django_notification.ticket_id = notification.ticket_id
            django_notification.message = notification.message
            django_notification.read = notification.read
            django_notification.save(update_fields=['ticket_id', 'message', 'read'])
        else:
            # Crear nueva notificación
            django_notification = DjangoNotification.objects.create(
                ticket_id=notification.ticket_id,
                message=notification.message,
                read=notification.read
            )
            notification.id = django_notification.id
        
        return notification
    
    def find_by_id(self, notification_id: int) -> Optional[DomainNotification]:
        """
        Busca una notificación por ID y la convierte a entidad de dominio.
        
        Args:
            notification_id: ID de la notificación
            
        Returns:
            Entidad de dominio o None si no existe
        """
        try:
            django_notification = DjangoNotification.objects.get(pk=notification_id)
            return self._to_domain(django_notification)
        except DjangoNotification.DoesNotExist:
            return None
    
    def find_all(self) -> List[DomainNotification]:
        """
        Obtiene todas las notificaciones ordenadas por fecha de envío.
        
        Returns:
            Lista de entidades de dominio
        """
        django_notifications = DjangoNotification.objects.all().order_by('-sent_at')
        return [self._to_domain(dn) for dn in django_notifications]
    
    def to_django_model(self, domain_notification: DomainNotification) -> DjangoNotification:
        """
        Convierte una entidad de dominio a modelo Django para serialización.
        
        Args:
            domain_notification: Entidad de dominio
            
        Returns:
            Modelo Django
        """
        if domain_notification.id:
            try:
                django_notification = DjangoNotification.objects.get(pk=domain_notification.id)
                django_notification.ticket_id = domain_notification.ticket_id
                django_notification.message = domain_notification.message
                django_notification.read = domain_notification.read
                return django_notification
            except DjangoNotification.DoesNotExist:
                pass
        
        # Crear instancia sin guardar (para serialización)
        return DjangoNotification(
            id=domain_notification.id,
            ticket_id=domain_notification.ticket_id,
            message=domain_notification.message,
            sent_at=domain_notification.sent_at,
            read=domain_notification.read
        )
    
    def _to_domain(self, django_notification: DjangoNotification) -> DomainNotification:
        """
        Convierte un modelo Django a entidad de dominio.
        
        Args:
            django_notification: Modelo Django
            
        Returns:
            Entidad de dominio
        """
        return DomainNotification(
            id=django_notification.id,
            ticket_id=django_notification.ticket_id,
            message=django_notification.message,
            sent_at=django_notification.sent_at,
            read=django_notification.read,
            user_id=django_notification.user_id,
            response_id=django_notification.response_id,
        )
