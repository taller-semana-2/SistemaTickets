"""
Tests de dispatch del consumer RabbitMQ (Gap A, Issue #76).

El consumer callback debe inspeccionar event_type y delegar a los
use cases correspondientes en lugar de crear notificaciones directamente
vía ORM para todos los eventos.

Cubre:
- Dispatch de ticket.response_added → CreateNotificationFromResponseUseCase
- Backward-compatibility de ticket.created → creación directa (ORM)
- ACK del mensaje en ambos flujos
- Manejo de errores en eventos response_added mal formados
"""

import json
import logging
import pytest
from unittest.mock import Mock, MagicMock, patch


class TestConsumerDispatch:
    """Tests del dispatch de eventos en el consumer callback."""

    def _make_channel(self):
        """Helper: crea un mock de canal pika con basic_ack."""
        ch = Mock()
        ch.basic_ack = Mock()
        return ch

    def _make_method(self, delivery_tag=1):
        """Helper: crea un mock de method con delivery_tag."""
        method = Mock()
        method.delivery_tag = delivery_tag
        return method

    def _make_body(self, data: dict) -> bytes:
        """Helper: serializa un dict como body JSON bytes."""
        return json.dumps(data).encode("utf-8")

    # ─────────────────────────────────────────────
    # Gap A (#76): Dispatch de ticket.response_added
    # ─────────────────────────────────────────────

    @patch("notifications.messaging.consumer.CreateNotificationFromResponseUseCase", create=True)
    @patch("notifications.messaging.consumer.Notification")
    def test_callback_dispatches_response_added_to_use_case(
        self, mock_orm_notification, mock_use_case_cls
    ):
        """#76 Gap A: Cuando event_type es 'ticket.response_added',
        el consumer debe delegar al CreateNotificationFromResponseUseCase
        en lugar de crear directamente vía ORM."""
        # Arrange
        mock_use_case = Mock()
        mock_use_case_cls.return_value = mock_use_case

        from notifications.messaging.consumer import callback

        ch = self._make_channel()
        method = self._make_method()
        body = self._make_body({
            "event_type": "ticket.response_added",
            "ticket_id": 42,
            "response_id": 7,
            "admin_id": "admin-001",
            "response_text": "Revisando tu caso",
            "user_id": "user-123",
            "timestamp": "2026-02-18T14:30:00Z",
        })

        # Act
        callback(ch, method, None, body)

        # Assert: el use case debe haber sido invocado
        mock_use_case.execute.assert_called_once()
        # Assert: NO se creó vía ORM directamente
        mock_orm_notification.objects.create.assert_not_called()

    @patch("notifications.messaging.consumer.Notification")
    def test_callback_handles_ticket_created_normally(self, mock_orm_notification):
        """#76 Backward-compat: Cuando event_type es 'ticket.created'
        (o no hay event_type), el consumer debe crear la notificación
        vía ORM como lo hace actualmente."""
        # Arrange
        from notifications.messaging.consumer import callback

        ch = self._make_channel()
        method = self._make_method()
        body = self._make_body({
            "event_type": "ticket.created",
            "ticket_id": 99,
        })

        # Act
        callback(ch, method, None, body)

        # Assert: se creó vía ORM
        mock_orm_notification.objects.create.assert_called_once()
        call_kwargs = mock_orm_notification.objects.create.call_args
        # Verificar que el ticket_id es correcto
        assert "99" in str(call_kwargs)

    @patch("notifications.messaging.consumer.CreateNotificationFromResponseUseCase", create=True)
    @patch("notifications.messaging.consumer.Notification")
    def test_callback_acks_message_on_response_added(
        self, mock_orm_notification, mock_use_case_cls
    ):
        """#76: Tras procesar un evento ticket.response_added, el consumer
        debe hacer ACK del mensaje para confirmar recepción."""
        # Arrange
        mock_use_case = Mock()
        mock_use_case_cls.return_value = mock_use_case

        from notifications.messaging.consumer import callback

        ch = self._make_channel()
        method = self._make_method(delivery_tag=42)
        body = self._make_body({
            "event_type": "ticket.response_added",
            "ticket_id": 10,
            "response_id": 3,
            "admin_id": "admin-002",
            "response_text": "Solucionado",
            "user_id": "user-456",
            "timestamp": "2026-02-18T15:00:00Z",
        })

        # Act
        callback(ch, method, None, body)

        # Assert
        ch.basic_ack.assert_called_once_with(delivery_tag=42)

    @patch("notifications.messaging.consumer.CreateNotificationFromResponseUseCase", create=True)
    @patch("notifications.messaging.consumer.Notification")
    def test_callback_logs_error_on_invalid_response_event(
        self, mock_orm_notification, mock_use_case_cls, caplog
    ):
        """#76: Si un evento ticket.response_added tiene schema inválido
        (ej. falta ticket_id), el consumer debe loguear el error y hacer
        ACK del mensaje sin crashear el loop del consumidor."""
        # Arrange
        from notifications.domain.exceptions import InvalidEventSchema

        mock_use_case = Mock()
        mock_use_case.execute.side_effect = InvalidEventSchema(
            missing_fields=["ticket_id"]
        )
        mock_use_case_cls.return_value = mock_use_case

        from notifications.messaging.consumer import callback

        ch = self._make_channel()
        method = self._make_method(delivery_tag=55)
        body = self._make_body({
            "event_type": "ticket.response_added",
            "response_id": 3,
            # ticket_id missing intentionally
            "admin_id": "admin-002",
            "response_text": "Texto",
            "user_id": "user-456",
            "timestamp": "2026-02-18T15:00:00Z",
        })

        # Act — must NOT raise
        with caplog.at_level(logging.ERROR):
            callback(ch, method, None, body)

        # Assert: ACK always sent (never leave message unacked)
        ch.basic_ack.assert_called_once_with(delivery_tag=55)
        # Assert: error was logged
        assert any("error" in record.message.lower() or "invalid" in record.message.lower()
                    for record in caplog.records), (
            "Expected an error/invalid log entry for invalid response event"
        )
