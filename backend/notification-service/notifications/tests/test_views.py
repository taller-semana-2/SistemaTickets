"""
Tests del ViewSet refactorizado (capa de presentación).
Prueban que las vistas deleguen correctamente a casos de uso.
"""

from unittest.mock import Mock, patch
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from datetime import datetime

from notifications.api import NotificationViewSet
from notifications.domain.entities import Notification as DomainNotification
from notifications.domain.exceptions import NotificationNotFound
from notifications.models import Notification as DjangoNotification


class TestNotificationViewSet(TestCase):
    """Tests del NotificationViewSet refactorizado."""
    
    def setUp(self):
        """Setup común para todos los tests."""
        self.factory = APIRequestFactory()
        self.viewset = NotificationViewSet()
    
    @patch('notifications.api.MarkNotificationAsReadUseCase')
    @patch('notifications.api.DjangoNotificationRepository')
    @patch('notifications.api.RabbitMQEventPublisher')
    def test_read_action_success(self, mock_publisher, mock_repository, mock_use_case):
        """Marcar como leída una notificación existente retorna 204."""
        # Arrange
        notification_id = 1
        domain_notification = DomainNotification(
            id=notification_id,
            ticket_id="T-123",
            message="Test",
            sent_at=datetime.now(),
            read=True
        )
        
        # Mock del caso de uso
        mock_use_case_instance = Mock()
        mock_use_case_instance.execute.return_value = domain_notification
        mock_use_case.return_value = mock_use_case_instance
        
        # Crear viewset con mocks
        viewset = NotificationViewSet()
        viewset.mark_as_read_use_case = mock_use_case_instance
        
        # Act
        request = self.factory.patch(f'/api/notifications/{notification_id}/read/')
        response = viewset.read(request, pk=notification_id)
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_use_case_instance.execute.assert_called_once()
    
    @patch('notifications.api.MarkNotificationAsReadUseCase')
    @patch('notifications.api.DjangoNotificationRepository')
    @patch('notifications.api.RabbitMQEventPublisher')
    def test_read_action_not_found(self, mock_publisher, mock_repository, mock_use_case):
        """Marcar como leída una notificación inexistente retorna 404."""
        # Arrange
        notification_id = 999
        
        # Mock del caso de uso que lanza excepción
        mock_use_case_instance = Mock()
        mock_use_case_instance.execute.side_effect = NotificationNotFound(notification_id)
        mock_use_case.return_value = mock_use_case_instance
        
        # Crear viewset con mocks
        viewset = NotificationViewSet()
        viewset.mark_as_read_use_case = mock_use_case_instance
        
        # Act
        request = self.factory.patch(f'/api/notifications/{notification_id}/read/')
        response = viewset.read(request, pk=notification_id)
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'error' in response.data
