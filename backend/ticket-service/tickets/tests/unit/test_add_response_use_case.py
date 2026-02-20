"""
Tests unitarios para AddTicketResponseUseCase (Application Layer).
Usan mocks para repositories y event publishers (aislados de infraestructura).

Issue: #39 — feat: persistencia de respuestas y despacho de eventos (EP12, EP13, EP15)
"""

import pytest
from unittest.mock import Mock
from datetime import datetime

from tickets.domain.entities import Ticket
from tickets.domain.repositories import TicketRepository
from tickets.domain.event_publisher import EventPublisher
from tickets.domain.exceptions import TicketAlreadyClosed, EmptyResponseError

from tickets.application.use_cases import (
    AddTicketResponseUseCase,
    AddTicketResponseCommand,
)


class TestAddTicketResponseUseCase:
    """Tests del caso de uso AddTicketResponse (#39)."""

    def test_successful_response_persists_ticket_issue39_ep12(self):
        """EP12: Persistir respuesta exitosa — el repositorio guarda el ticket
        y la validacion de dominio (add_response) se ejecuta."""
        # Arrange
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)

        existing_ticket = Ticket(
            id=42,
            title="Problema con factura",
            description="No puedo descargar mi factura",
            status=Ticket.OPEN,
            user_id="user-100",
            created_at=datetime(2026, 2, 19, 10, 0, 0),
        )
        mock_repo.find_by_id.return_value = existing_ticket
        mock_repo.save.return_value = existing_ticket

        use_case = AddTicketResponseUseCase(mock_repo, mock_publisher)
        command = AddTicketResponseCommand(
            ticket_id=42,
            text="Estamos revisando tu caso",
            admin_id="admin-001",
        )

        # Act
        use_case.execute(command)

        # Assert — persistence happened
        mock_repo.find_by_id.assert_called_once_with(42)
        mock_repo.save.assert_called_once()

    def test_closed_ticket_raises_ticket_already_closed_issue39_ep12(self):
        """EP12: Responder a ticket cerrado propaga TicketAlreadyClosed.
        No debe persistir ni publicar evento."""
        # Arrange
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)

        closed_ticket = Ticket(
            id=42,
            title="Problema resuelto",
            description="Ya se resolvio",
            status=Ticket.CLOSED,
            user_id="user-100",
            created_at=datetime(2026, 2, 19, 10, 0, 0),
        )
        mock_repo.find_by_id.return_value = closed_ticket

        use_case = AddTicketResponseUseCase(mock_repo, mock_publisher)
        command = AddTicketResponseCommand(
            ticket_id=42,
            text="Texto valido de respuesta",
            admin_id="admin-001",
        )

        # Act & Assert
        with pytest.raises(TicketAlreadyClosed):
            use_case.execute(command)

        mock_repo.save.assert_not_called()
        mock_publisher.publish.assert_not_called()

    def test_empty_text_raises_empty_response_error_issue39_ep12(self):
        """EP12: Respuesta con texto vacio propaga EmptyResponseError.
        No debe persistir ni publicar evento."""
        # Arrange
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)

        open_ticket = Ticket(
            id=42,
            title="Problema con factura",
            description="No puedo descargar mi factura",
            status=Ticket.OPEN,
            user_id="user-100",
            created_at=datetime(2026, 2, 19, 10, 0, 0),
        )
        mock_repo.find_by_id.return_value = open_ticket

        use_case = AddTicketResponseUseCase(mock_repo, mock_publisher)
        command = AddTicketResponseCommand(
            ticket_id=42,
            text="",
            admin_id="admin-001",
        )

        # Act & Assert
        with pytest.raises(EmptyResponseError):
            use_case.execute(command)

        mock_repo.save.assert_not_called()
        mock_publisher.publish.assert_not_called()

    def test_ticket_not_found_raises_value_error_issue39_ep12(self):
        """EP12: Si el ticket no existe el caso de uso lanza ValueError."""
        # Arrange
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)

        mock_repo.find_by_id.return_value = None

        use_case = AddTicketResponseUseCase(mock_repo, mock_publisher)
        command = AddTicketResponseCommand(
            ticket_id=9999,
            text="Respuesta a ticket inexistente",
            admin_id="admin-001",
        )

        # Act & Assert
        with pytest.raises(ValueError):
            use_case.execute(command)
