"""
Integration tests for complete ticket workflows.
Tests end-to-end scenarios with all architectural layers working together.

These tests validate:
- Clean Architecture layer interaction
- Domain-Driven Design patterns
- Repository pattern implementation
- Event-driven architecture
- Business rules enforcement across the stack
"""

from django.test import TestCase
from unittest.mock import Mock, call, patch

from tickets.domain.entities import Ticket as DomainTicket
from tickets.domain.exceptions import (
    TicketAlreadyClosed,
    InvalidTicketStateTransition,
    InvalidTicketData,
    InvalidPriorityTransition,
    DomainException
)
from tickets.application.use_cases import (
    CreateTicketUseCase,
    CreateTicketCommand,
    ChangeTicketStatusUseCase,
    ChangeTicketStatusCommand,
    ChangeTicketPriorityUseCase,
    ChangeTicketPriorityCommand
)
from tickets.infrastructure.repository import DjangoTicketRepository
from tickets.infrastructure.event_publisher import RabbitMQEventPublisher
from tickets.models import Ticket as DjangoTicket


class TestCompleteTicketWorkflow(TestCase):
    """Integration tests for complete ticket workflows with all components."""
    
    def setUp(self):
        """Set up real repository and mock event publisher."""
        self.repository = DjangoTicketRepository()
        self.event_publisher = Mock(spec=RabbitMQEventPublisher)
    
    def tearDown(self):
        """Clean up database after each test."""
        DjangoTicket.objects.all().delete()
    
    # ==================== Happy Path Workflows ====================
    
    def test_complete_ticket_lifecycle(self):
        """Test: Complete ticket lifecycle from creation to closure."""
        # 1. Create ticket
        create_use_case = CreateTicketUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        
        ticket = create_use_case.execute(
            CreateTicketCommand(
                title="Complete Lifecycle Test",
                description="Testing full workflow"
            )
        )
        
        # Verify initial state
        assert ticket.id is not None
        assert ticket.status == DomainTicket.OPEN
        assert self.event_publisher.publish.call_count == 1
        
        # Verify persistence
        db_ticket = DjangoTicket.objects.get(pk=ticket.id)
        assert db_ticket.status == "OPEN"
        
        # 2. Move to IN_PROGRESS
        change_use_case = ChangeTicketStatusUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        
        ticket = change_use_case.execute(
            ChangeTicketStatusCommand(
                ticket_id=ticket.id,
                new_status=DomainTicket.IN_PROGRESS
            )
        )
        
        assert ticket.status == DomainTicket.IN_PROGRESS
        assert self.event_publisher.publish.call_count == 2
        
        db_ticket.refresh_from_db()
        assert db_ticket.status == "IN_PROGRESS"
        
        # 3. Close ticket
        ticket = change_use_case.execute(
            ChangeTicketStatusCommand(
                ticket_id=ticket.id,
                new_status=DomainTicket.CLOSED
            )
        )
        
        assert ticket.status == DomainTicket.CLOSED
        assert self.event_publisher.publish.call_count == 3
        
        db_ticket.refresh_from_db()
        assert db_ticket.status == "CLOSED"
    
    def test_direct_open_to_closed_transition(self):
        """Test: Ticket can go directly from OPEN to CLOSED."""
        # Create ticket
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand("Direct Close", "Test")
        )
        
        # Close directly from OPEN
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.CLOSED)
        )
        
        # Verify
        assert ticket.status == DomainTicket.CLOSED
        db_ticket = DjangoTicket.objects.get(pk=ticket.id)
        assert db_ticket.status == "CLOSED"
    
    def test_multiple_tickets_independent_workflows(self):
        """Test: Multiple tickets can have independent workflows."""
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        
        # Create three tickets
        ticket1 = create_use_case.execute(CreateTicketCommand("T1", "D1"))
        ticket2 = create_use_case.execute(CreateTicketCommand("T2", "D2"))
        ticket3 = create_use_case.execute(CreateTicketCommand("T3", "D3"))
        
        # Move them to different states
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket1.id, DomainTicket.IN_PROGRESS)
        )
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket2.id, DomainTicket.CLOSED)
        )
        # ticket3 stays OPEN
        
        # Verify independent states
        db_t1 = DjangoTicket.objects.get(pk=ticket1.id)
        db_t2 = DjangoTicket.objects.get(pk=ticket2.id)
        db_t3 = DjangoTicket.objects.get(pk=ticket3.id)
        
        assert db_t1.status == "IN_PROGRESS"
        assert db_t2.status == "CLOSED"
        assert db_t3.status == "OPEN"
    
    # ==================== Business Rules Enforcement ====================
    
    def test_cannot_modify_closed_ticket(self):
        """Test: Business rule - closed tickets cannot be modified."""
        # Create and close ticket
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand("To Close", "Test")
        )
        
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.CLOSED)
        )
        
        # Attempt to reopen
        with self.assertRaises(TicketAlreadyClosed):
            change_use_case.execute(
                ChangeTicketStatusCommand(ticket.id, DomainTicket.OPEN)
            )
        
        # Verify state unchanged
        db_ticket = DjangoTicket.objects.get(pk=ticket.id)
        assert db_ticket.status == "CLOSED"
    
    def test_cannot_skip_to_invalid_status(self):
        """Test: Invalid state transitions are rejected."""
        # Create ticket
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand("Test", "Desc")
        )
        
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        
        # Try invalid transition
        with self.assertRaises(ValueError):
            change_use_case.execute(
                ChangeTicketStatusCommand(ticket.id, "INVALID_STATUS")
            )
    
    def test_idempotent_status_changes_do_not_publish_events(self):
        """Test: Changing to same status is idempotent and doesn't publish events."""
        # Create ticket
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand("Test", "Desc")
        )
        
        initial_call_count = self.event_publisher.publish.call_count
        
        # Change to same status (OPEN -> OPEN)
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.OPEN)
        )
        
        # Verify no new event published
        assert self.event_publisher.publish.call_count == initial_call_count
        
        # Verify database unchanged
        db_ticket = DjangoTicket.objects.get(pk=ticket.id)
        assert db_ticket.status == "OPEN"
    
    # ==================== Event Publishing Validation ====================
    
    def test_create_ticket_publishes_ticket_created_event(self):
        """Test: Creating ticket publishes TicketCreated event."""
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        
        ticket = create_use_case.execute(
            CreateTicketCommand("Event Test", "Testing events")
        )
        
        # Verify event published
        assert self.event_publisher.publish.call_count == 1
        
        # Verify event type and data
        published_event = self.event_publisher.publish.call_args[0][0]
        assert published_event.__class__.__name__ == "TicketCreated"
        assert published_event.ticket_id == ticket.id
        assert published_event.title == "Event Test"
        assert published_event.description == "Testing events"
        assert published_event.status == "OPEN"
    
    def test_change_status_publishes_status_changed_event(self):
        """Test: Changing status publishes TicketStatusChanged event."""
        # Create ticket
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand("Test", "Desc")
        )
        
        self.event_publisher.reset_mock()
        
        # Change status
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.IN_PROGRESS)
        )
        
        # Verify event published
        assert self.event_publisher.publish.call_count == 1
        
        # Verify event data
        published_event = self.event_publisher.publish.call_args[0][0]
        assert published_event.__class__.__name__ == "TicketStatusChanged"
        assert published_event.ticket_id == ticket.id
        assert published_event.old_status == "OPEN"
        assert published_event.new_status == "IN_PROGRESS"
    
    def test_multiple_status_changes_publish_multiple_events(self):
        """Test: Each status change publishes a separate event."""
        # Create ticket
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand("Multi", "Events")
        )
        
        # Track events
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        
        initial_count = self.event_publisher.publish.call_count
        
        # Make multiple changes
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.IN_PROGRESS)
        )
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.CLOSED)
        )
        
        # Verify two additional events published
        assert self.event_publisher.publish.call_count == initial_count + 2
    
    # ==================== Repository Pattern Validation ====================
    
    def test_repository_correctly_translates_domain_to_persistence(self):
        """Test: Repository correctly translates between domain and Django models."""
        # Create through use case
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        domain_ticket = create_use_case.execute(
            CreateTicketCommand("Translation Test", "Testing repository")
        )
        
        # Verify domain entity properties
        assert isinstance(domain_ticket, DomainTicket)
        assert domain_ticket.status == DomainTicket.OPEN
        
        # Verify Django model properties
        django_ticket = DjangoTicket.objects.get(pk=domain_ticket.id)
        assert django_ticket.title == "Translation Test"
        assert django_ticket.description == "Testing repository"
        assert django_ticket.status == "OPEN"
        
        # Verify types match expected
        assert isinstance(django_ticket.title, str)
        assert isinstance(django_ticket.status, str)
    
    def test_repository_preserves_data_across_operations(self):
        """Test: Repository maintains data integrity across multiple operations."""
        # Create ticket
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand("Preserve", "Data integrity test")
        )
        
        original_title = ticket.title
        original_description = ticket.description
        
        # Change status multiple times
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.IN_PROGRESS)
        )
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.CLOSED)
        )
        
        # Verify title and description unchanged
        db_ticket = DjangoTicket.objects.get(pk=ticket.id)
        assert db_ticket.title == original_title
        assert db_ticket.description == original_description
        assert db_ticket.status == "CLOSED"
    
    # ==================== Error Handling ====================
    
    def test_invalid_ticket_data_raises_domain_exception(self):
        """Test: Invalid ticket data raises domain exception."""
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        
        # Try to create ticket with empty title
        with self.assertRaises(InvalidTicketData):
            create_use_case.execute(
                CreateTicketCommand(title="", description="No title")
            )
        
        # Verify no ticket created
        count = DjangoTicket.objects.count()
        assert count == 0
    
    def test_nonexistent_ticket_change_status_fails_gracefully(self):
        """Test: Attempting to change status of non-existent ticket raises ValueError."""
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        
        # Try to change status of non-existent ticket
        with self.assertRaises(ValueError):
            change_use_case.execute(
                ChangeTicketStatusCommand(
                    ticket_id=99999,
                    new_status=DomainTicket.CLOSED
                )
            )
    
    # ==================== Clean Architecture Validation ====================
    
    def test_use_case_depends_on_abstractions_not_implementations(self):
        """Test: Use cases depend on repository interface, not Django ORM."""
        # Create use case with repository
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        
        # Verify use case stores repository reference
        assert create_use_case.repository is self.repository
        assert create_use_case.event_publisher is self.event_publisher
        
        # Create ticket
        ticket = create_use_case.execute(
            CreateTicketCommand("Architecture", "Testing layers")
        )
        
        # Verify domain entity returned (not Django model)
        assert isinstance(ticket, DomainTicket)
        assert not isinstance(ticket, DjangoTicket)
    
    def test_domain_entities_remain_independent_of_framework(self):
        """Test: Domain entities don't depend on Django or any framework."""
        # Create domain entity directly (no Django involved) using factory
        domain_ticket = DomainTicket.create(
            title="Pure Domain",
            description="No framework dependencies"
        )
        
        # Apply business rule
        domain_ticket.change_status(DomainTicket.IN_PROGRESS)
        
        # Verify entity behavior independent of persistence
        assert domain_ticket.status == DomainTicket.IN_PROGRESS
        
        # Now persist through repository
        saved_ticket = self.repository.save(domain_ticket)
        
        # Verify persistence successful
        assert saved_ticket.id is not None
        db_ticket = DjangoTicket.objects.get(pk=saved_ticket.id)
        assert db_ticket.status == "IN_PROGRESS"
    
    # ==================== Consistency Tests ====================
    
    def test_concurrent_status_changes_maintain_consistency(self):
        """Test: Multiple status changes maintain data consistency."""
        # Create ticket
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand("Concurrent", "Test")
        )
        
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        
        # Load ticket twice (simulating concurrent access)
        ticket1 = self.repository.find_by_id(ticket.id)
        ticket2 = self.repository.find_by_id(ticket.id)
        
        # Modify both and save
        ticket1.change_status(DomainTicket.IN_PROGRESS)
        self.repository.save(ticket1)
        
        ticket2.change_status(DomainTicket.CLOSED)
        self.repository.save(ticket2)
        
        # Verify last write wins
        db_ticket = DjangoTicket.objects.get(pk=ticket.id)
        assert db_ticket.status == "CLOSED"
    
    def test_workflow_rollback_on_event_publish_failure(self):
        """Test: Workflow behavior when event publishing fails."""
        # Configure event publisher to raise exception
        failing_publisher = Mock(spec=RabbitMQEventPublisher)
        failing_publisher.publish.side_effect = Exception("RabbitMQ unavailable")
        
        create_use_case = CreateTicketUseCase(
            self.repository,
            failing_publisher
        )
        
        # Try to create ticket (should fail on event publish)
        with self.assertRaises(Exception):
            create_use_case.execute(
                CreateTicketCommand("Failing", "Event publish fails")
            )
        
        # Note: Current implementation doesn't rollback on publish failure
        # This test documents current behavior
        # In production, consider implementing transaction boundaries

    # ==================== Priority Workflow Integration ====================

    def test_complete_priority_change_workflow(self):
        """RED-6.1: Flujo completo — crear ticket + cambiar prioridad persiste y publica evento."""
        # 1. Crear ticket
        create_use_case = CreateTicketUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand(title="Priority Workflow", description="Integration test", user_id="1")
        )

        # 2. Cambiar prioridad
        change_priority_use_case = ChangeTicketPriorityUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        command = ChangeTicketPriorityCommand(
            ticket_id=ticket.id,
            new_priority="High",
        )
        command.user_role = "Administrador"
        command.justification = "Urgente"

        updated_ticket = change_priority_use_case.execute(command)

        # 3. Verificar entidad de dominio
        assert updated_ticket.priority == "High"
        assert updated_ticket.priority_justification == "Urgente"

        # 4. Verificar persistencia en BD
        db_ticket = DjangoTicket.objects.get(pk=ticket.id)
        assert db_ticket.priority == "High"
        assert db_ticket.priority_justification == "Urgente"

        # 5. Verificar evento TicketPriorityChanged publicado
        priority_events = [
            c for c in self.event_publisher.publish.call_args_list
            if c[0][0].__class__.__name__ == "TicketPriorityChanged"
        ]
        assert len(priority_events) == 1
        event = priority_events[0][0][0]
        assert event.ticket_id == ticket.id
        assert event.old_priority == "Unassigned"
        assert event.new_priority == "High"
        assert event.justification == "Urgente"

    def test_priority_change_on_closed_ticket_raises_error(self):
        """RED-6.2: Flujo — cambiar prioridad de ticket cerrado falla con TicketAlreadyClosed."""
        # 1. Crear ticket
        create_use_case = CreateTicketUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand(title="Close Then Priority", description="Test", user_id="1")
        )

        # 2. Cerrar ticket: OPEN → IN_PROGRESS → CLOSED
        change_status_use_case = ChangeTicketStatusUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        change_status_use_case.execute(
            ChangeTicketStatusCommand(ticket_id=ticket.id, new_status=DomainTicket.IN_PROGRESS)
        )
        change_status_use_case.execute(
            ChangeTicketStatusCommand(ticket_id=ticket.id, new_status=DomainTicket.CLOSED)
        )

        # 3. Intentar cambiar prioridad en ticket cerrado
        change_priority_use_case = ChangeTicketPriorityUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        command = ChangeTicketPriorityCommand(
            ticket_id=ticket.id,
            new_priority="High",
        )
        command.user_role = "Administrador"

        with self.assertRaises(TicketAlreadyClosed):
            change_priority_use_case.execute(command)

    def test_priority_change_with_non_admin_raises_error(self):
        """RED-6.3: Flujo — cambiar prioridad con usuario no admin falla con DomainException."""
        # 1. Crear ticket
        create_use_case = CreateTicketUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand(title="Non Admin Priority", description="Test", user_id="1")
        )

        # 2. Intentar cambiar prioridad con rol "Usuario"
        change_priority_use_case = ChangeTicketPriorityUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        command = ChangeTicketPriorityCommand(
            ticket_id=ticket.id,
            new_priority="High",
        )
        command.user_role = "Usuario"

        with self.assertRaises(DomainException) as ctx:
            change_priority_use_case.execute(command)

        assert "permiso insuficiente" in str(ctx.exception).lower()

    def test_revert_to_unassigned_raises_error_in_workflow(self):
        """RED-6.4: Flujo — reversión a Unassigned falla con InvalidPriorityTransition."""
        # 1. Crear ticket
        create_use_case = CreateTicketUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand(title="Revert Priority", description="Test", user_id="1")
        )

        # 2. Asignar prioridad High
        change_priority_use_case = ChangeTicketPriorityUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        command_high = ChangeTicketPriorityCommand(
            ticket_id=ticket.id,
            new_priority="High",
        )
        command_high.user_role = "Administrador"
        change_priority_use_case.execute(command_high)

        # 3. Intentar revertir a Unassigned
        command_unassigned = ChangeTicketPriorityCommand(
            ticket_id=ticket.id,
            new_priority="Unassigned",
        )
        command_unassigned.user_role = "Administrador"

        with self.assertRaises(InvalidPriorityTransition):
            change_priority_use_case.execute(command_unassigned)

    def test_idempotent_priority_change_no_extra_event(self):
        """RED-6.5: Flujo — idempotencia: mismo valor no publica evento adicional."""
        # 1. Crear ticket
        create_use_case = CreateTicketUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand(title="Idempotent Priority", description="Test", user_id="1")
        )

        # 2. Cambiar prioridad a High (primera vez)
        change_priority_use_case = ChangeTicketPriorityUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        command = ChangeTicketPriorityCommand(
            ticket_id=ticket.id,
            new_priority="High",
        )
        command.user_role = "Administrador"
        change_priority_use_case.execute(command)

        # Registrar el conteo de llamadas después del primer cambio
        call_count_after_first = self.event_publisher.publish.call_count

        # 3. Cambiar prioridad a High (segunda vez — idempotente)
        command2 = ChangeTicketPriorityCommand(
            ticket_id=ticket.id,
            new_priority="High",
        )
        command2.user_role = "Administrador"
        change_priority_use_case.execute(command2)

        # Verificar que NO se publicó evento adicional
        assert self.event_publisher.publish.call_count == call_count_after_first
