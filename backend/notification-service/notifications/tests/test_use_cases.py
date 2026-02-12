"""
Tests de casos de uso (Application layer).
Prueban la orquestación de dominio, repositorio y eventos.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from notifications.domain.entities import Notification
from notifications.domain.exceptions import NotificationNotFound
from notifications.application.use_cases import (
    MarkNotificationAsReadUseCase,
    MarkNotificationAsReadCommand
)


class TestMarkNotificationAsReadUseCase:
    """Tests del caso de uso de marcar notificación como leída."""
    
    def test_mark_as_read_success(self):
        """Ejecutar el caso de uso marca la notificación como leída."""
        # Arrange: Mock del repositorio y event publisher
        repository = Mock()
        event_publisher = Mock()
        
        notification = Notification(
            id=1,
            ticket_id="T-123",
            message="Test",
            sent_at=datetime.now(),
            read=False
        )
        repository.find_by_id.return_value = notification
        repository.save.return_value = notification
        
        use_case = MarkNotificationAsReadUseCase(repository, event_publisher)
        command = MarkNotificationAsReadCommand(notification_id=1)
        
        # Act
        result = use_case.execute(command)
        
        # Assert
        assert result.read is True
        repository.find_by_id.assert_called_once_with(1)
        repository.save.assert_called_once()
        event_publisher.publish.assert_called_once()
    
    def test_mark_as_read_notification_not_found(self):
        """Si la notificación no existe, lanza NotificationNotFound."""
        # Arrange
        repository = Mock()
        event_publisher = Mock()
        repository.find_by_id.return_value = None
        
        use_case = MarkNotificationAsReadUseCase(repository, event_publisher)
        command = MarkNotificationAsReadCommand(notification_id=999)
        
        # Act & Assert
        with pytest.raises(NotificationNotFound) as exc_info:
            use_case.execute(command)
        
        assert exc_info.value.notification_id == 999
        repository.find_by_id.assert_called_once_with(999)
        repository.save.assert_not_called()
        event_publisher.publish.assert_not_called()
    
    def test_mark_as_read_already_read_no_event(self):
        """Si la notificación ya está leída, no se publica evento."""
        # Arrange
        repository = Mock()
        event_publisher = Mock()
        
        notification = Notification(
            id=1,
            ticket_id="T-123",
            message="Test",
            sent_at=datetime.now(),
            read=True  # Ya está leída
        )
        repository.find_by_id.return_value = notification
        repository.save.return_value = notification
        
        use_case = MarkNotificationAsReadUseCase(repository, event_publisher)
        command = MarkNotificationAsReadCommand(notification_id=1)
        
        # Act
        result = use_case.execute(command)
        
        # Assert
        assert result.read is True
        repository.save.assert_called_once()
        # No se publicó evento (idempotencia)
        event_publisher.publish.assert_not_called()
