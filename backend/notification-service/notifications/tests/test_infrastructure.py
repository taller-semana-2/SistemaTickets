"""
Tests de la capa de infraestructura (Django ORM Repository).
Prueban la traducción entre entidades de dominio y modelos Django.
"""

import pytest
from datetime import datetime
from django.test import TestCase

from notifications.models import Notification as DjangoNotification
from notifications.domain.entities import Notification as DomainNotification
from notifications.infrastructure.repository import DjangoNotificationRepository


class TestDjangoNotificationRepository(TestCase):
    """Tests del repositorio Django."""
    
    def setUp(self):
        """Setup común para todos los tests."""
        self.repository = DjangoNotificationRepository()
    
    def test_save_new_notification(self):
        """Guardar una nueva notificación asigna ID."""
        # Arrange
        domain_notification = DomainNotification(
            id=None,
            ticket_id="T-123",
            message="Test notification",
            sent_at=datetime.now(),
            read=False
        )
        
        # Act
        result = self.repository.save(domain_notification)
        
        # Assert
        assert result.id is not None
        assert DjangoNotification.objects.filter(id=result.id).exists()
    
    def test_save_existing_notification(self):
        """Actualizar una notificación existente."""
        # Arrange: Crear notificación en BD
        django_notif = DjangoNotification.objects.create(
            ticket_id="T-123",
            message="Original",
            read=False
        )
        
        domain_notification = DomainNotification(
            id=django_notif.id,
            ticket_id="T-123",
            message="Updated",
            sent_at=django_notif.sent_at,
            read=True
        )
        
        # Act
        result = self.repository.save(domain_notification)
        
        # Assert
        django_notif.refresh_from_db()
        assert django_notif.message == "Updated"
        assert django_notif.read is True
    
    def test_find_by_id_existing(self):
        """Buscar por ID una notificación existente."""
        # Arrange
        django_notif = DjangoNotification.objects.create(
            ticket_id="T-456",
            message="Test",
            read=False
        )
        
        # Act
        result = self.repository.find_by_id(django_notif.id)
        
        # Assert
        assert result is not None
        assert result.id == django_notif.id
        assert result.ticket_id == "T-456"
        assert result.message == "Test"
        assert result.read is False
    
    def test_find_by_id_not_found(self):
        """Buscar por ID una notificación que no existe retorna None."""
        # Act
        result = self.repository.find_by_id(999)
        
        # Assert
        assert result is None
    
    def test_find_all(self):
        """Obtener todas las notificaciones."""
        # Arrange
        DjangoNotification.objects.create(ticket_id="T-1", message="First")
        DjangoNotification.objects.create(ticket_id="T-2", message="Second")
        DjangoNotification.objects.create(ticket_id="T-3", message="Third")
        
        # Act
        results = self.repository.find_all()
        
        # Assert
        assert len(results) >= 3
        assert all(isinstance(n, DomainNotification) for n in results)
    
    def test_to_django_model(self):
        """Convertir entidad de dominio a modelo Django."""
        # Arrange
        domain_notification = DomainNotification(
            id=1,
            ticket_id="T-789",
            message="Test",
            sent_at=datetime.now(),
            read=True
        )
        
        # Act
        django_model = self.repository.to_django_model(domain_notification)
        
        # Assert
        assert isinstance(django_model, DjangoNotification)
        assert django_model.ticket_id == "T-789"
        assert django_model.message == "Test"
        assert django_model.read is True

    def test_find_by_response_id_returns_notification_when_exists(self):
        """Buscar por response_id retorna la notificación cuando existe."""
        # Arrange
        django_notif = DjangoNotification.objects.create(
            ticket_id="T-700",
            message="Response notification",
            read=False,
            user_id="user-abc",
            response_id=7,
        )

        # Act
        result = self.repository.find_by_response_id(7)

        # Assert
        assert result is not None
        assert result.id == django_notif.id
        assert result.response_id == 7
        assert result.ticket_id == "T-700"

    def test_find_by_response_id_returns_none_when_not_exists(self):
        """Buscar por response_id retorna None cuando no existe."""
        # Act
        result = self.repository.find_by_response_id(99)

        # Assert
        assert result is None

    def test_save_persists_user_id_and_response_id(self):
        """Guardar una notificación persiste user_id y response_id."""
        # Arrange
        domain_notification = DomainNotification(
            id=None,
            ticket_id="T-800",
            message="Notification with user and response",
            sent_at=datetime.now(),
            read=False,
            user_id="user-123",
            response_id=7,
        )

        # Act
        result = self.repository.save(domain_notification)

        # Assert
        django_notif = DjangoNotification.objects.get(pk=result.id)
        assert django_notif.user_id == "user-123"
        assert django_notif.response_id == 7

    def test_save_updates_user_id_and_response_id(self):
        """Actualizar una notificación persiste cambios en user_id y response_id."""
        # Arrange: Crear notificación inicial
        django_notif = DjangoNotification.objects.create(
            ticket_id="T-900",
            message="Initial",
            read=False,
            user_id="old-user",
            response_id=1,
        )

        domain_notification = DomainNotification(
            id=django_notif.id,
            ticket_id="T-900",
            message="Initial",
            sent_at=django_notif.sent_at,
            read=False,
            user_id="new-user",
            response_id=42,
        )

        # Act
        self.repository.save(domain_notification)

        # Assert
        django_notif.refresh_from_db()
        assert django_notif.user_id == "new-user"
        assert django_notif.response_id == 42
