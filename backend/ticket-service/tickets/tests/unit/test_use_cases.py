"""
Tests unitarios de casos de uso (Application Layer).
Usan mocks para repositories y event publishers (aislados de infraestructura).
"""

import pytest
from unittest.mock import Mock, call
from datetime import datetime

from tickets.domain.entities import Ticket
from tickets.domain.repositories import TicketRepository
from tickets.domain.event_publisher import EventPublisher
from tickets.domain.events import TicketCreated, TicketStatusChanged, TicketPriorityChanged
from tickets.domain.exceptions import (
    DomainException,
    InvalidPriorityTransition,
    InvalidTicketData,
    InvalidTicketStateTransition,
    TicketAlreadyClosed,
)
from tickets.domain.factories import TicketFactory

from tickets.application.use_cases import (
    CreateTicketUseCase,
    CreateTicketCommand,
    ChangeTicketStatusUseCase,
    ChangeTicketStatusCommand,
    ChangeTicketPriorityUseCase,
    ChangeTicketPriorityCommand
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
        command = CreateTicketCommand("Test Title", "Test Description", "user-1")
        
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
        assert published_event.user_id == "user-1"
    
    def test_create_ticket_with_invalid_data_raises_exception(self):
        """Crear ticket con datos inválidos lanza excepción."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        use_case = CreateTicketUseCase(mock_repo, mock_publisher)
        command = CreateTicketCommand("", "Description", "user-1")  # Título vacío
        
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
        command = CreateTicketCommand("Title", "", "user-1")
        
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
        
        # Inyectar factory mock
        mock_factory = Mock(spec=TicketFactory)
        mock_factory.create.return_value = Ticket.create("Valid", "Valid", "user-1")
        
        use_case = CreateTicketUseCase(mock_repo, mock_publisher, mock_factory)
        command = CreateTicketCommand("Title", "Description", "user-1")
        
        use_case.execute(command)
        
        # Verificar que se usó el factory
        mock_factory.create.assert_called_once_with(
            title="Title",
            description="Description",
            user_id="user-1"
        )
    
    def test_create_ticket_event_contains_correct_data(self):
        """El evento publicado contiene todos los datos correctos."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        def assign_id(ticket):
            ticket.id = 789
            return ticket
        mock_repo.save.side_effect = assign_id
        
        use_case = CreateTicketUseCase(mock_repo, mock_publisher)
        command = CreateTicketCommand("Event Test", "Testing events", "user-1")
        
        ticket = use_case.execute(command)
        
        # Verificar evento publicado
        assert mock_publisher.publish.call_count == 1
        event = mock_publisher.publish.call_args[0][0]
        
        assert event.ticket_id == 789
        assert event.title == "Event Test"
        assert event.description == "Testing events"
        assert event.status == Ticket.OPEN
        assert event.user_id == "user-1"
        assert isinstance(event.occurred_at, datetime)


class TestChangeTicketStatusUseCase:
    """Tests del caso de uso ChangeTicketStatus."""
    
    def test_change_status_updates_and_publishes_event(self):
        """Cambiar estado actualiza el ticket y publica evento."""
        # Arrange
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        # Ticket existente
        existing_ticket = Ticket(
            id=100,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            user_id="user-1",
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = existing_ticket
        mock_repo.save.return_value = existing_ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(100, Ticket.IN_PROGRESS)
        
        # Act
        updated_ticket = use_case.execute(command)
        
        # Assert
        assert updated_ticket.status == Ticket.IN_PROGRESS
        mock_repo.find_by_id.assert_called_once_with(100)
        mock_repo.save.assert_called_once()
        
        # Verificar evento publicado
        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        assert isinstance(event, TicketStatusChanged)
        assert event.ticket_id == 100
        assert event.old_status == Ticket.OPEN
        assert event.new_status == Ticket.IN_PROGRESS
    
    def test_change_status_ticket_not_found(self):
        """Cambiar estado de ticket inexistente lanza excepción."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        mock_repo.find_by_id.return_value = None
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(999, Ticket.IN_PROGRESS)
        
        with pytest.raises(ValueError, match="no encontrado"):
            use_case.execute(command)
        
        # No debe guardar ni publicar
        mock_repo.save.assert_not_called()
        mock_publisher.publish.assert_not_called()
    
    def test_change_status_of_closed_ticket_raises_error(self):
        """Cambiar estado de ticket cerrado lanza TicketAlreadyClosed."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        closed_ticket = Ticket(
            id=200,
            title="Closed",
            description="Desc",
            status=Ticket.CLOSED,
            user_id="user-1",
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = closed_ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(200, Ticket.OPEN)
        
        with pytest.raises(TicketAlreadyClosed):
            use_case.execute(command)
        
        # No debe publicar evento
        mock_publisher.publish.assert_not_called()
    
    def test_change_to_invalid_status_raises_error(self):
        """Cambiar a estado inválido lanza ValueError."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        ticket = Ticket(
            id=300,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            user_id="user-1",
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(300, "INVALID_STATUS")
        
        with pytest.raises(ValueError, match="Estado inválido"):
            use_case.execute(command)
    
    def test_change_to_same_status_is_idempotent(self):
        """Cambiar al mismo estado no publica eventos (idempotente)."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        ticket = Ticket(
            id=400,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            user_id="user-1",
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = ticket
        mock_repo.save.return_value = ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(400, Ticket.OPEN)  # Mismo estado
        
        updated_ticket = use_case.execute(command)
        
        assert updated_ticket.status == Ticket.OPEN
        mock_repo.save.assert_called_once()
        # No debe publicar eventos (idempotente)
        mock_publisher.publish.assert_not_called()
    
    def test_multiple_status_changes_publish_multiple_events(self):
        """Múltiples cambios de estado publican múltiples eventos."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        ticket = Ticket(
            id=500,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            user_id="user-1",
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = ticket
        mock_repo.save.return_value = ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        
        # Primer cambio: OPEN -> IN_PROGRESS
        command1 = ChangeTicketStatusCommand(500, Ticket.IN_PROGRESS)
        use_case.execute(command1)
        
        # Segundo cambio: IN_PROGRESS -> CLOSED
        command2 = ChangeTicketStatusCommand(500, Ticket.CLOSED)
        use_case.execute(command2)
        
        # Verificar que se publicaron 2 eventos
        assert mock_publisher.publish.call_count == 2
        
        # Verificar eventos
        calls = mock_publisher.publish.call_args_list
        event1 = calls[0][0][0]
        event2 = calls[1][0][0]
        
        assert event1.new_status == Ticket.IN_PROGRESS
        assert event2.new_status == Ticket.CLOSED


class TestChangeTicketPriorityUseCase:
    """Tests del caso de uso ChangeTicketPriority."""

    def _create_ticket_and_use_case(
        self,
        ticket_id: int = 1,
        status: str = Ticket.OPEN,
        priority: str = "Unassigned",
        new_priority: str = "High",
        user_role: str = "Administrador",
    ):
        """Helper: crea mocks, ticket, use case y command para tests de prioridad."""
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)

        existing_ticket = Ticket(
            id=ticket_id,
            title="Test Ticket",
            description="Test Description",
            status=status,
            user_id="user123",
            created_at=datetime.now(),
            priority=priority,
        )
        mock_repo.find_by_id.return_value = existing_ticket
        mock_repo.save.return_value = existing_ticket

        use_case = ChangeTicketPriorityUseCase(mock_repo, mock_publisher)
        command = ChangeTicketPriorityCommand(
            ticket_id=ticket_id,
            new_priority=new_priority,
        )
        command.user_role = user_role

        return existing_ticket, use_case, command, mock_repo, mock_publisher

    def test_admin_changes_priority_successfully(self):
        """
        EP1: Administrador cambia prioridad exitosamente.
        
        Scenario: Administrador cambia prioridad de ticket Open
          Given un ticket en estado "Open" con prioridad "Unassigned"
          And el usuario autenticado tiene rol "Administrador"
          When intenta cambiar la prioridad a "High"
          Then la prioridad del ticket se actualiza a "High"
          And se genera un evento de dominio "TicketPriorityChanged"
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(ticket_id=1, new_priority="High")
        )
        
        # Act
        updated_ticket = use_case.execute(command)
        
        # Assert
        assert updated_ticket.priority == "High"
        mock_repo.find_by_id.assert_called_once_with(1)
        mock_repo.save.assert_called_once()
        
        # Verificar evento publicado
        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        assert isinstance(event, TicketPriorityChanged)
        assert event.ticket_id == 1
        assert event.old_priority == "Unassigned"
        assert event.new_priority == "High"

    def test_user_without_permissions_cannot_change_priority(self):
        """
        EP2: Usuario sin permisos no puede cambiar prioridad.

        Scenario: Usuario sin permisos no puede cambiar prioridad (EP2)
          Given un ticket en estado "Open" con prioridad "Unassigned"
          And el usuario autenticado tiene rol "Usuario"
          When intenta cambiar la prioridad a "High"
          Then el sistema bloquea la accion
          And se retorna un error de permiso insuficiente
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=2, new_priority="High", user_role="Usuario"
            )
        )

        # Act & Assert
        with pytest.raises(DomainException) as exc_info:
            use_case.execute(command)

        assert "permiso insuficiente" in str(exc_info.value).lower()
        assert existing_ticket.priority == "Unassigned"

        # Assert — rejected before lookup (permission check is first)
        mock_repo.find_by_id.assert_not_called()

        # No debe persistir ni publicar eventos
        mock_repo.save.assert_not_called()
        mock_publisher.publish.assert_not_called()

    def test_admin_changes_priority_in_progress_ticket(self):
        """
        EP4: Cambio de prioridad permitido en ticket In-Progress.
        
        Scenario: Administrador cambia prioridad de ticket In-Progress (EP4)
          Given un ticket en estado "In-Progress" con prioridad "Low"
          And el usuario autenticado tiene rol "Administrador"
          When intenta cambiar la prioridad a "High"
          Then la prioridad del ticket se actualiza a "High"
          And se genera un evento de dominio "TicketPriorityChanged"
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=3,
                status=Ticket.IN_PROGRESS,
                priority="Low",
                new_priority="High",
            )
        )
        
        # Act
        updated_ticket = use_case.execute(command)
        
        # Assert
        assert updated_ticket.priority == "High"
        mock_repo.find_by_id.assert_called_once_with(3)
        mock_repo.save.assert_called_once()
        
        # Verificar evento publicado
        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        assert isinstance(event, TicketPriorityChanged)
        assert event.ticket_id == 3
        assert event.old_priority == "Low"
        assert event.new_priority == "High"

    def test_priority_change_blocked_on_closed_ticket(self):
        """
        EP5: Cambio de prioridad bloqueado en ticket Closed.

        Scenario: Administrador intenta cambiar prioridad de ticket Closed (EP5)
          Given un ticket en estado "Closed" con prioridad "Low"
          And el usuario autenticado tiene rol "Administrador"
          When intenta cambiar la prioridad a "High"
          Then el sistema lanza la excepción TicketAlreadyClosed
          And la prioridad del ticket permanece en "Low"
          And no se persiste ningún cambio
          And no se publica ningún evento de dominio
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=4,
                status=Ticket.CLOSED,
                priority="Low",
                new_priority="High",
            )
        )

        # Act & Assert
        with pytest.raises(TicketAlreadyClosed):
            use_case.execute(command)

        # La prioridad debe permanecer sin cambios
        assert existing_ticket.priority == "Low"

        # Assert — repository looked up by correct ID
        mock_repo.find_by_id.assert_called_once_with(4)

        # No debe persistir ni publicar eventos
        mock_repo.save.assert_not_called()
        mock_publisher.publish.assert_not_called()

    @pytest.mark.parametrize("priority", ["Low", "Medium", "High"])
    def test_change_to_each_valid_priority(self, priority: str):
        """
        EP6: Cambio a prioridad válida es exitoso.

        Scenario Outline: Cambio a prioridad válida es exitoso (EP6)
          Given un ticket en estado "Open" con prioridad "Unassigned"
          And el usuario autenticado tiene rol "Administrador"
          When intenta cambiar la prioridad a "<prioridad>"
          Then la prioridad del ticket se actualiza a "<prioridad>"
          And se genera un evento TicketPriorityChanged con old_priority="Unassigned" y new_priority="<prioridad>"
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(ticket_id=6, new_priority=priority)
        )

        # Act
        updated_ticket = use_case.execute(command)

        # Assert — priority is updated
        assert updated_ticket.priority == priority

        # Assert — repository looked up by correct ID
        mock_repo.find_by_id.assert_called_once_with(6)

        # Assert — save was called once
        mock_repo.save.assert_called_once()

        # Assert — TicketPriorityChanged event published with correct data
        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        assert isinstance(event, TicketPriorityChanged)
        assert event.ticket_id == 6
        assert event.old_priority == "Unassigned"
        assert event.new_priority == priority

    def test_priority_change_without_justification_is_valid(self):
        """
        EP10: Cambio de prioridad sin justificación es válido.

        Scenario: Cambio de prioridad sin justificación es válido (EP10)
          Given un ticket en estado "In-Progress" con prioridad "Low"
          And el usuario autenticado tiene rol "Administrador"
          When cambia la prioridad a "High" sin ingresar justificación
          Then la prioridad del ticket se actualiza a "High"
          And no se muestra sección de justificación en el detalle
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=10,
                status=Ticket.IN_PROGRESS,
                priority="Low",
                new_priority="High",
                user_role="Administrador",
            )
        )

        # Act
        updated_ticket = use_case.execute(command)

        # Assert
        assert updated_ticket.priority == "High"
        assert updated_ticket.priority_justification is None
        mock_repo.find_by_id.assert_called_once_with(10)
        mock_repo.save.assert_called_once()
        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        assert isinstance(event, TicketPriorityChanged)
        assert event.ticket_id == 10
        assert event.old_priority == "Low"
        assert event.new_priority == "High"
        assert event.justification is None

    def test_cannot_revert_to_unassigned(self):
        """
        EP7: No se puede volver a Unassigned una vez asignada prioridad.

        Scenario: No se puede volver a Unassigned una vez asignada prioridad (EP7)
          Given un ticket en estado "Open" con prioridad "Medium"
          And el usuario autenticado tiene rol "Administrador"
          When intenta cambiar la prioridad a "Unassigned"
          Then el sistema bloquea la acción
          And se informa que no es posible volver a "Unassigned"
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=7,
                status=Ticket.OPEN,
                priority="Medium",
                new_priority="Unassigned",
                user_role="Administrador",
            )
        )

        # Act & Assert
        with pytest.raises(InvalidPriorityTransition) as exc_info:
            use_case.execute(command)

        # El mensaje debe mencionar "Unassigned"
        assert "Unassigned" in str(exc_info.value)

        # La prioridad debe permanecer sin cambios
        assert existing_ticket.priority == "Medium"

        # Assert — repository looked up by correct ID
        mock_repo.find_by_id.assert_called_once_with(7)

        # No debe persistir ni publicar eventos
        mock_repo.save.assert_not_called()
        mock_publisher.publish.assert_not_called()

    def test_unassigned_to_unassigned_is_noop(self):
        """
        EP8: Asignar Unassigned a ticket que ya tiene Unassigned no genera cambio ni evento.

        Scenario: Asignar Unassigned a ticket que ya tiene Unassigned es no-op (EP8)
          Given un ticket en estado "Open" con prioridad "Unassigned"
          And el usuario autenticado tiene rol "Administrador"
          When intenta cambiar la prioridad a "Unassigned"
          Then no se realiza ningún cambio
          And no se publica ningún evento de dominio
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=8,
                status=Ticket.OPEN,
                priority="Unassigned",
                new_priority="Unassigned",
                user_role="Administrador",
            )
        )

        # Act — should NOT raise
        updated_ticket = use_case.execute(command)

        # Assert — priority remains "Unassigned"
        assert updated_ticket.priority == "Unassigned"
        assert existing_ticket.priority == "Unassigned"

        # Assert — repository looked up by correct ID
        mock_repo.find_by_id.assert_called_once_with(8)

        # Assert — save WAS called (use case calls save regardless)
        mock_repo.save.assert_called_once()

        # Assert — no event published (no actual change occurred)
        mock_publisher.publish.assert_not_called()

        # Assert — no domain events collected
        assert existing_ticket.collect_domain_events() == []

    @pytest.mark.parametrize("invalid_priority", ["critical", "urgent", "CRITICAL", "none", "123"])
    def test_invalid_priority_value_is_rejected(self, invalid_priority: str):
        """
        EP9: Valor de prioridad fuera de enumeración es rechazado.

        Scenario: Valor de prioridad fuera de enumeración es rechazado (EP9)
          Given un ticket en estado "Open" con prioridad "Unassigned"
          And el usuario autenticado tiene rol "Administrador"
          When intenta cambiar la prioridad a un valor no válido
          Then el sistema rechaza la acción
          And no se persiste ningún cambio
          And no se publica ningún evento de dominio
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=9,
                status=Ticket.OPEN,
                priority="Unassigned",
                new_priority=invalid_priority,
                user_role="Administrador",
            )
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Prioridad inválida"):
            use_case.execute(command)

        # No debe persistir ni publicar eventos
        mock_repo.save.assert_not_called()
        mock_publisher.publish.assert_not_called()

    def test_priority_change_with_justification_is_saved(self):
        """
        EP11: Justificación ingresada se guarda y se muestra en el detalle.

        Scenario: Justificación ingresada se guarda y se muestra en el detalle (EP11)
          Given un ticket en estado "Open" con prioridad "Unassigned"
          And el usuario autenticado tiene rol "Administrador"
          When cambia la prioridad a "High" con justificación "Urgente por SLA"
          Then la prioridad del ticket se actualiza a "High"
          And la justificación "Urgente por SLA" es visible en el detalle del ticket
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=11,
                status=Ticket.OPEN,
                priority="Unassigned",
                new_priority="High",
                user_role="Administrador",
            )
        )
        command.justification = "Urgente por SLA"

        # Act
        updated_ticket = use_case.execute(command)

        # Assert
        assert updated_ticket.priority == "High"
        assert updated_ticket.priority_justification == "Urgente por SLA"
        mock_repo.find_by_id.assert_called_once_with(11)
        mock_repo.save.assert_called_once()
        mock_publisher.publish.assert_called_once()
        event = mock_publisher.publish.call_args[0][0]
        assert isinstance(event, TicketPriorityChanged)
        assert event.ticket_id == 11
        assert event.old_priority == "Unassigned"
        assert event.new_priority == "High"
        assert event.justification == "Urgente por SLA"

    def test_empty_justification_is_accepted_bva7(self):
        """
        BVA7: Justificación vacía (0 caracteres) es aceptada.

        Scenario: Justificación vacía es aceptada (BVA7)
          Given un ticket en estado "Open"
          And el usuario autenticado tiene rol "Administrador"
          When cambia la prioridad a "High" con justificación de 0 caracteres
          Then la prioridad se actualiza exitosamente
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=107,
                status=Ticket.OPEN,
                priority="Unassigned",
                new_priority="High",
                user_role="Administrador",
            )
        )
        command.justification = ""

        # Act
        updated_ticket = use_case.execute(command)

        # Assert
        assert updated_ticket.priority == "High"
        mock_repo.save.assert_called_once()
        mock_publisher.publish.assert_called_once()

    @pytest.mark.parametrize("length", [254, 255])
    def test_justification_within_limit_is_accepted_bva8_bva9(self, length: int):
        """
        BVA8/BVA9: Justificación de 254 y 255 caracteres es aceptada.

        Scenario: Justificación dentro del límite es aceptada (BVA8/BVA9)
          Given un ticket en estado "Open"
          And el usuario autenticado tiene rol "Administrador"
          When cambia la prioridad a "Medium" con una justificación de <length> caracteres
          Then la prioridad se actualiza exitosamente
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=108,
                status=Ticket.OPEN,
                priority="Unassigned",
                new_priority="Medium",
                user_role="Administrador",
            )
        )
        command.justification = "a" * length

        # Act
        updated_ticket = use_case.execute(command)

        # Assert
        assert updated_ticket.priority == "Medium"
        assert len(updated_ticket.priority_justification) == length
        mock_repo.save.assert_called_once()
        mock_publisher.publish.assert_called_once()

    def test_justification_exceeding_max_length_is_rejected_bva10(self):
        """
        BVA10: Justificación que excede 255 caracteres es rechazada.

        Scenario: Justificación que excede el límite de caracteres es rechazada (BVA10)
          Given un ticket en estado "Open"
          And el usuario autenticado tiene rol "Administrador"
          When intenta cambiar la prioridad a "Medium" con una justificación de 256 caracteres
          Then el sistema rechaza la acción
          And se informa que la justificación excede la longitud máxima
        """
        # Arrange
        existing_ticket, use_case, command, mock_repo, mock_publisher = (
            self._create_ticket_and_use_case(
                ticket_id=110,
                status=Ticket.OPEN,
                priority="Unassigned",
                new_priority="Medium",
                user_role="Administrador",
            )
        )
        command.justification = "a" * 256

        # Act & Assert
        with pytest.raises(ValueError, match="justificación.*longitud máxima"):
            use_case.execute(command)

        # No debe persistir ni publicar eventos
        mock_repo.save.assert_not_called()
        mock_publisher.publish.assert_not_called()


class TestChangeTicketStatusValidation:
    """Tests para validación de transiciones de estado inválidas."""
    
    def test_direct_transition_open_to_closed_is_invalid(self):
        """
        U17: Transición directa OPEN → CLOSED es rechazada.
        
        Scenario: Transición directa OPEN → CLOSED es rechazada (U17)
          Given un ticket en estado "OPEN"
          When se intenta cambiar el estado directamente a "CLOSED"
          Then se lanza una excepción InvalidTicketStateTransition
          And el estado del ticket permanece sin cambios
          And no se publica ningún evento de dominio
        """
        # Arrange
        mock_repo = Mock(spec=TicketRepository)
        mock_publisher = Mock(spec=EventPublisher)
        
        # Ticket en estado OPEN
        existing_ticket = Ticket(
            id=100,
            title="Test Ticket",
            description="Test Description",
            status=Ticket.OPEN,
            user_id="user123",
            created_at=datetime.now()
        )
        mock_repo.find_by_id.return_value = existing_ticket
        
        use_case = ChangeTicketStatusUseCase(mock_repo, mock_publisher)
        command = ChangeTicketStatusCommand(100, Ticket.CLOSED)
        
        # Act & Assert
        with pytest.raises(InvalidTicketStateTransition):
            use_case.execute(command)
        
        # Estado debe permanecer sin cambios
        assert existing_ticket.status == Ticket.OPEN
        
        # No debe publicar eventos
        mock_publisher.publish.assert_not_called()
        mock_repo.save.assert_not_called()
