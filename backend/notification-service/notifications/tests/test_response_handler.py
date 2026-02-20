"""
Tests del handler de eventos ticket.response_added (Application layer).
Prueban la creación de notificaciones a partir de eventos y validación de schema.

Issue #45: feat: notification consumer with idempotency (EP21, EP22)
TDD Phase: RED — Todos estos tests deben FALLAR porque el use case no existe aún.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from notifications.application.use_cases import (
    CreateNotificationFromResponseUseCase,
    CreateNotificationFromResponseCommand,
)
from notifications.domain.exceptions import InvalidEventSchema


class TestCreateNotificationFromResponseUseCase:
    """Tests del caso de uso: crear notificación a partir de ticket.response_added."""

    def _build_valid_command(self) -> CreateNotificationFromResponseCommand:
        """Helper: construye un comando válido con todos los campos requeridos."""
        return CreateNotificationFromResponseCommand(
            event_type="ticket.response_added",
            ticket_id=42,
            response_id=7,
            admin_id="admin-001",
            response_text="Estamos revisando tu caso",
            user_id="user-123",
            timestamp="2026-02-18T14:30:00Z",
        )

    # ─────────────────────────────────────────────
    # HU-2.1: Creación de notificación desde evento válido
    # ─────────────────────────────────────────────

    def test_create_notification_from_valid_response_event(self):
        """HU-2.1: Un evento válido ticket.response_added crea una Notification
        con read=False, asociada al ticket_id y user_id del evento, y la
        persiste mediante el repositorio."""
        # Arrange
        repository = Mock()
        repository.find_by_response_id.return_value = None
        repository.save.side_effect = lambda n: n

        use_case = CreateNotificationFromResponseUseCase(repository=repository)
        command = self._build_valid_command()

        # Act
        result = use_case.execute(command)

        # Assert
        assert result is not None
        assert result.ticket_id == "42"
        assert result.read is False
        repository.save.assert_called_once()
        saved_notification = repository.save.call_args[0][0]
        assert saved_notification.read is False
        assert saved_notification.ticket_id == "42"

    def test_create_notification_message_format(self):
        """HU-2.1: El mensaje de la notificación debe ser exactamente
        'Nueva respuesta en Ticket #<ticket_id>'."""
        # Arrange
        repository = Mock()
        repository.find_by_response_id.return_value = None
        repository.save.side_effect = lambda n: n

        use_case = CreateNotificationFromResponseUseCase(repository=repository)
        command = self._build_valid_command()

        # Act
        result = use_case.execute(command)

        # Assert
        assert result.message == "Nueva respuesta en Ticket #42"

    # ─────────────────────────────────────────────
    # EP21 (R9): Validación de schema del evento
    # ─────────────────────────────────────────────

    def test_event_missing_ticket_id_raises_invalid_schema(self):
        """EP21: Un evento sin ticket_id debe lanzar InvalidEventSchema."""
        # Arrange
        repository = Mock()
        use_case = CreateNotificationFromResponseUseCase(repository=repository)
        command = CreateNotificationFromResponseCommand(
            event_type="ticket.response_added",
            ticket_id=None,
            response_id=7,
            admin_id="admin-001",
            response_text="Texto",
            user_id="user-123",
            timestamp="2026-02-18T14:30:00Z",
        )

        # Act & Assert
        with pytest.raises(InvalidEventSchema) as exc_info:
            use_case.execute(command)
        assert "ticket_id" in str(exc_info.value)

    def test_event_missing_response_id_raises_invalid_schema(self):
        """EP21: Un evento sin response_id debe lanzar InvalidEventSchema."""
        # Arrange
        repository = Mock()
        use_case = CreateNotificationFromResponseUseCase(repository=repository)
        command = CreateNotificationFromResponseCommand(
            event_type="ticket.response_added",
            ticket_id=42,
            response_id=None,
            admin_id="admin-001",
            response_text="Texto",
            user_id="user-123",
            timestamp="2026-02-18T14:30:00Z",
        )

        # Act & Assert
        with pytest.raises(InvalidEventSchema) as exc_info:
            use_case.execute(command)
        assert "response_id" in str(exc_info.value)

    def test_event_missing_user_id_raises_invalid_schema(self):
        """EP21: Un evento sin user_id debe lanzar InvalidEventSchema."""
        # Arrange
        repository = Mock()
        use_case = CreateNotificationFromResponseUseCase(repository=repository)
        command = CreateNotificationFromResponseCommand(
            event_type="ticket.response_added",
            ticket_id=42,
            response_id=7,
            admin_id="admin-001",
            response_text="Texto",
            user_id=None,
            timestamp="2026-02-18T14:30:00Z",
        )

        # Act & Assert
        with pytest.raises(InvalidEventSchema) as exc_info:
            use_case.execute(command)
        assert "user_id" in str(exc_info.value)

    def test_event_missing_multiple_fields_raises_invalid_schema(self):
        """EP21: Un evento con múltiples campos faltantes debe lanzar
        InvalidEventSchema indicando todos los campos que faltan."""
        # Arrange
        repository = Mock()
        use_case = CreateNotificationFromResponseUseCase(repository=repository)
        command = CreateNotificationFromResponseCommand(
            event_type="ticket.response_added",
            ticket_id=None,
            response_id=None,
            admin_id=None,
            response_text=None,
            user_id=None,
            timestamp=None,
        )

        # Act & Assert
        with pytest.raises(InvalidEventSchema) as exc_info:
            use_case.execute(command)
        error_msg = str(exc_info.value)
        assert "ticket_id" in error_msg
        assert "response_id" in error_msg
        assert "user_id" in error_msg
