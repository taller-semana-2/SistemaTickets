"""
Tests de casos de uso (Application Layer).
Usan mocks para repositories y event publishers.
"""

import pytest
from unittest.mock import Mock, MagicMock, call
from datetime import datetime

from tickets.domain.entities import Ticket
from tickets.domain.repositories import TicketRepository
from tickets.domain.event_publisher import EventPublisher
from tickets.domain.events import TicketCreated, TicketStatusChanged
from tickets.domain.exceptions import TicketAlreadyClosed, InvalidTicketData

from tickets.application.use_cases import (
    CreateTicketUseCase,
    CreateTicketCommand,
    ChangeTicketStatusUseCase,
    ChangeTicketStatusCommand
)


class TestCreateTicketUseCase:
    """Tests del caso de uso CreateTicket."""
    
    def test_create_ticket_persists_and_publishes_event(self):
        """Crear ticket persiste en repositorio y publica evento."""
        # Arrange: Mocks
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        # Simular que el repositorio asigna ID
        def assign_id(ticket):
            ticket.id = 123
            return ticket
        mock_repo.save.side_effect = assign_id
        
        use_case = CreateTicketUseCase(mock_repo, mock_publisher)
        command = CreateTicketCommand("Test Title", "Test Description")
        
        # Act
        ticket = use_case.execute(command)
        
        # Assert
        assert ticket.id == 123
        assert ticket.title == "Test Title"
        assert ticket.description == "Test Description"
        assert ticket.status == Ticket.OPEN
        
        # Verificar que se llamó a save
        mock_repo.save.assert_called_once()
        saved_ticket = mock_repo.save.call_args[0][0]
        assert saved_ticket.title == "Test Title"
        
        # Verificar que se publicó evento
        mock_publisher.publish.assert_called_once()
        published_event = mock_publisher.publish.call_args[0][0]
        assert isinstance(published_event, TicketCreated)
        assert published_event.ticket_id == 123
        assert published_event.title == "Test Title"
    
    def test_create_ticket_with_invalid_data_raises_exception(self):
        """Crear ticket con datos inválidos lanza excepción."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        use_case = CreateTicketUseCase(mock_repo, mock_publisher)
        command = CreateTicketCommand("", "Description")  # Título vacío
        
        with pytest.raises(InvalidTicketData):
            use_case.execute(command)
        
        # No debe persistir ni publicar si falló validación
        mock_repo.save.assert_not_called()
        mock_publisher.publish.assert_not_called()
    
    def test_create_ticket_with_empty_description_fails(self):
        """Crear ticket con descripción vacía falla."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        use_case = CreateTicketUseCase(mock_repo, mock_publisher)
        command = CreateTicketCommand("Title", "")
        
        with pytest.raises(InvalidTicketData):
            use_case.execute(command)
        
        mock_repo.save.assert_not_called()
        mock_publisher.publish.assert_not_called()
    
    def test_create_ticket_uses_factory_for_validation(self):
        """El caso de uso usa factory para validación."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        def assign_id(ticket):
            ticket.id = 456
            return ticket
        mock_repo.save.side_effect = assign_id
        
        use_case = CreateTicketUseCase(mock_repo, mock_publisher)
        command = CreateTicketCommand("  Trimmed  ", "  Also Trimmed  ")
        
        ticket = use_case.execute(command)
        
        # Factory debe haber eliminado espacios
        assert ticket.title == "Trimmed"
        assert ticket.description == "Also Trimmed"


class TestChangeTicketStatusUseCase:
    """Tests del caso de uso ChangeTicketStatus."""
    
    def test_change_status_persists_and_publishes_event(self):
        """Cambiar estado persiste y publica evento."""
        # Arrange
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        existing_ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = existing_ticket
        mock_repo.save.return_value = existing_ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(1, Ticket.IN_PROGRESS)
        
        # Act
        ticket = use_case.execute(command)
        
        # Assert
        assert ticket.status == Ticket.IN_PROGRESS
        mock_repo.find_by_id.assert_called_once_with(1)
        mock_repo.save.assert_called_once()
        mock_publisher.publish.assert_called_once()
        
        # Verificar que se publicó TicketStatusChanged
        published_event = mock_publisher.publish.call_args[0][0]
        assert isinstance(published_event, TicketStatusChanged)
        assert published_event.ticket_id == 1
        assert published_event.old_status == Ticket.OPEN
        assert published_event.new_status == Ticket.IN_PROGRESS
    
    def test_change_status_of_closed_ticket_raises_exception(self):
        """Cambiar estado de ticket cerrado lanza excepción."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        closed_ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.CLOSED,
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = closed_ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(1, Ticket.OPEN)
        
        with pytest.raises(TicketAlreadyClosed):
            use_case.execute(command)
        
        # No debe publicar si falló la regla de negocio
        mock_publisher.publish.assert_not_called()
    
    def test_change_status_of_nonexistent_ticket_raises_error(self):
        """Cambiar estado de ticket inexistente lanza error."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        mock_repo.find_by_id.return_value = None  # Ticket no existe
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(999, Ticket.CLOSED)
        
        with pytest.raises(ValueError, match="no encontrado"):
            use_case.execute(command)
        
        mock_publisher.publish.assert_not_called()
    
    def test_change_status_to_same_status_is_idempotent(self):
        """Cambiar al mismo estado no publica evento (idempotente)."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        existing_ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = existing_ticket
        mock_repo.save.return_value = existing_ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(1, Ticket.OPEN)  # Mismo estado
        
        ticket = use_case.execute(command)
        
        # Estado sigue igual
        assert ticket.status == Ticket.OPEN
        
        # Se guardó (por si hay otros cambios)
        mock_repo.save.assert_called_once()
        
        # NO se publicó evento (idempotente)
        mock_publisher.publish.assert_not_called()
    
    def test_change_status_with_invalid_status_raises_error(self):
        """Cambiar a estado inválido lanza error."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        existing_ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = existing_ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(1, "INVALID")
        
        with pytest.raises(ValueError, match="Estado inválido"):
            use_case.execute(command)
        
        mock_publisher.publish.assert_not_called()
    
    def test_multiple_status_changes_publish_multiple_events(self):
        """Múltiples cambios de estado publican múltiples eventos."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = ticket
        mock_repo.save.return_value = ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        
        # Primer cambio: OPEN → IN_PROGRESS
        command1 = ChangeTicketStatusCommand(1, Ticket.IN_PROGRESS)
        use_case.execute(command1)
        
        # Segundo cambio: IN_PROGRESS → CLOSED
        command2 = ChangeTicketStatusCommand(1, Ticket.CLOSED)
        use_case.execute(command2)
        
        # Se publicaron 2 eventos
        assert mock_publisher.publish.call_count == 2
