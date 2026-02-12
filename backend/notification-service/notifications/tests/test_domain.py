"""
Tests de la capa de dominio (puro Python, sin Django).
Prueban reglas de negocio, entidades y excepciones.
"""

import pytest
from datetime import datetime

from notifications.domain.entities import Notification
from notifications.domain.exceptions import NotificationAlreadyRead
from notifications.domain.events import NotificationMarkedAsRead


class TestNotificationEntity:
    """Tests de la entidad Notification (reglas de negocio)."""
    
    def test_create_notification_with_valid_data(self):
        """Crear una notificación con datos válidos."""
        notification = Notification(
            id=1,
            ticket_id="T-123",
            message="Ticket creado",
            sent_at=datetime.now(),
            read=False
        )
        
        assert notification.id == 1
        assert notification.ticket_id == "T-123"
        assert notification.message == "Ticket creado"
        assert notification.read is False
        assert isinstance(notification.sent_at, datetime)
    
    def test_mark_as_read_changes_state(self):
        """Marcar como leída cambia el estado y genera evento."""
        notification = Notification(
            id=1,
            ticket_id="T-123",
            message="Ticket creado",
            sent_at=datetime.now(),
            read=False
        )
        
        notification.mark_as_read()
        
        assert notification.read is True
        events = notification.collect_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], NotificationMarkedAsRead)
        assert events[0].notification_id == 1
        assert events[0].ticket_id == "T-123"
    
    def test_mark_as_read_is_idempotent(self):
        """Marcar como leída múltiples veces es idempotente."""
        notification = Notification(
            id=1,
            ticket_id="T-123",
            message="Ticket creado",
            sent_at=datetime.now(),
            read=False
        )
        
        # Primera vez: cambia estado y genera evento
        notification.mark_as_read()
        events = notification.collect_domain_events()
        assert len(events) == 1
        assert notification.read is True
        
        # Segunda vez: no cambia nada (idempotente)
        notification.mark_as_read()
        events = notification.collect_domain_events()
        assert len(events) == 0  # No genera nuevo evento
        assert notification.read is True  # Mantiene estado
    
    def test_mark_as_read_already_read_notification(self):
        """Marcar como leída una notificación ya leída no hace nada."""
        notification = Notification(
            id=1,
            ticket_id="T-123",
            message="Ticket creado",
            sent_at=datetime.now(),
            read=True  # Ya está leída
        )
        
        notification.mark_as_read()
        
        # No genera eventos
        events = notification.collect_domain_events()
        assert len(events) == 0
        assert notification.read is True
    
    def test_collect_domain_events_clears_list(self):
        """Recolectar eventos limpia la lista interna."""
        notification = Notification(
            id=1,
            ticket_id="T-123",
            message="Ticket creado",
            sent_at=datetime.now(),
            read=False
        )
        
        notification.mark_as_read()
        
        # Primera recolección
        events1 = notification.collect_domain_events()
        assert len(events1) == 1
        
        # Segunda recolección: lista vacía
        events2 = notification.collect_domain_events()
        assert len(events2) == 0
