"""
Tests unitarios para la traduccion del evento ticket.response_added en RabbitMQEventPublisher.
Issue: #39 - EP15: contrato del evento
"""

import pytest
from datetime import datetime

from tickets.domain.events import TicketResponseAdded
from tickets.infrastructure.event_publisher import RabbitMQEventPublisher


class TestRabbitMQEventPublisherResponseAdded:
    """Tests de traduccion del evento TicketResponseAdded a JSON."""

    def test_translate_ticket_response_added_event_issue39_ep15(self):
        """EP15: El evento traducido a JSON contiene todos los campos del contrato."""
        # Arrange
        event = TicketResponseAdded(
            occurred_at=datetime(2026, 2, 19, 14, 30, 0),
            ticket_id=42,
            response_id=7,
            admin_id="admin-001",
            response_text="Estamos revisando tu caso",
            user_id="user-123",
        )
        publisher = RabbitMQEventPublisher()

        # Act
        message = publisher._translate_event(event)

        # Assert - all contract fields present
        assert message["event_type"] == "ticket.response_added"
        assert message["ticket_id"] == 42
        assert message["response_id"] == 7
        assert message["admin_id"] == "admin-001"
        assert message["response_text"] == "Estamos revisando tu caso"
        assert message["user_id"] == "user-123"
        assert "occurred_at" in message or "timestamp" in message
