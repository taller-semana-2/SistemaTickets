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

    @staticmethod
    def _domain_to_fields(notification: DomainNotification) -> dict:
        """
        Extrae los campos persistibles de una entidad de dominio.

        Args:
            notification: Entidad de dominio

        Returns:
            Diccionario con los campos y sus valores para persistencia.
        """
        return {
            "ticket_id": notification.ticket_id,
            "message": notification.message,
            "read": notification.read,
            "user_id": notification.user_id,
            "response_id": notification.response_id,
        }

    def save(self, notification: DomainNotification) -> DomainNotification:
        """
        Persiste una notificación en la base de datos (crear o actualizar).
        
        Args:
            notification: Entidad de dominio
            
        Returns:
            La entidad con el ID asignado
        """
        fields = self._domain_to_fields(notification)

        if notification.id:
            # Actualizar notificación existente
            django_notification = DjangoNotification.objects.get(pk=notification.id)
            for attr, value in fields.items():
                setattr(django_notification, attr, value)
            django_notification.save(update_fields=list(fields.keys()))
        else:
            # Crear nueva notificación
            django_notification = DjangoNotification.objects.create(**fields)
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
        fields = self._domain_to_fields(domain_notification)

        if domain_notification.id:
            try:
                django_notification = DjangoNotification.objects.get(pk=domain_notification.id)
                for attr, value in fields.items():
                    setattr(django_notification, attr, value)
                return django_notification
            except DjangoNotification.DoesNotExist:
                pass
        
        # Crear instancia sin guardar (para serialización)
        return DjangoNotification(
            id=domain_notification.id,
            sent_at=domain_notification.sent_at,
            **fields,
        )
    
    def find_by_response_id(self, response_id: int) -> Optional[DomainNotification]:
        """
        Busca una notificación por response_id.

        Args:
            response_id: ID de la respuesta asociada

        Returns:
            Entidad de dominio o None si no existe
        """
        django_notification = DjangoNotification.objects.filter(response_id=response_id).first()
        if django_notification is None:
            return None
        return self._to_domain(django_notification)

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
