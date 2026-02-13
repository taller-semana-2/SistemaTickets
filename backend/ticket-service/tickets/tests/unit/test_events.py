"""
Tests unitarios de eventos de dominio.
Verifican la correcta creación e inmutabilidad de eventos.
"""


from datetime import datetime
from dataclasses import FrozenInstanceError

from tickets.domain.events import DomainEvent, TicketCreated, TicketStatusChanged
from tickets.domain.entities import Ticket


class TestDomainEvent:
    """Tests de la clase base DomainEvent."""
    
    def test_domain_event_has_occurred_at(self):
        """DomainEvent debe tener fecha de ocurrencia."""
        event = DomainEvent(occurred_at=datetime.now())
        assert isinstance(event.occurred_at, datetime)
    
    def test_domain_event_is_immutable(self):
        """Los eventos de dominio son inmutables (frozen)."""
        event = DomainEvent(occurred_at=datetime.now())
        
        with pytest.raises(FrozenInstanceError):
            event.occurred_at = datetime.now()


class TestTicketCreated:
    """Tests del evento TicketCreated."""
    
    def test_ticket_created_event_has_all_fields(self):
        """TicketCreated contiene todos los campos necesarios."""
        now = datetime.now()
        event = TicketCreated(
            occurred_at=now,
            ticket_id=123,
            title="Test Ticket",
            description="Test Description",
            status=Ticket.OPEN
        )
        
        assert event.occurred_at == now
        assert event.ticket_id == 123
        assert event.title == "Test Ticket"
        assert event.description == "Test Description"
        assert event.status == Ticket.OPEN
    
    def test_ticket_created_is_immutable(self):
        """TicketCreated es inmutable."""
        event = TicketCreated(
            occurred_at=datetime.now(),
            ticket_id=1,
            title="Title",
            description="Desc",
            status=Ticket.OPEN
        )
        
        with pytest.raises(FrozenInstanceError):
            event.ticket_id = 999
        
        with pytest.raises(FrozenInstanceError):
            event.title = "New Title"
    
    def test_ticket_created_equality(self):
        """Eventos con los mismos datos son iguales."""
        now = datetime.now()
        event1 = TicketCreated(
            occurred_at=now,
            ticket_id=1,
            title="Title",
            description="Desc",
            status=Ticket.OPEN
        )
        event2 = TicketCreated(
            occurred_at=now,
            ticket_id=1,
            title="Title",
            description="Desc",
            status=Ticket.OPEN
        )
        
        assert event1 == event2
    
    def test_ticket_created_inheritance(self):
        """TicketCreated hereda de DomainEvent."""
        event = TicketCreated(
            occurred_at=datetime.now(),
            ticket_id=1,
            title="T",
            description="D",
            status=Ticket.OPEN
        )
        
        assert isinstance(event, DomainEvent)


class TestTicketStatusChanged:
    """Tests del evento TicketStatusChanged."""
    
    def test_ticket_status_changed_has_all_fields(self):
        """TicketStatusChanged contiene todos los campos necesarios."""
        now = datetime.now()
        event = TicketStatusChanged(
            occurred_at=now,
            ticket_id=456,
            old_status=Ticket.OPEN,
            new_status=Ticket.IN_PROGRESS
        )
        
        assert event.occurred_at == now
        assert event.ticket_id == 456
        assert event.old_status == Ticket.OPEN
        assert event.new_status == Ticket.IN_PROGRESS
    
    def test_ticket_status_changed_is_immutable(self):
        """TicketStatusChanged es inmutable."""
        event = TicketStatusChanged(
            occurred_at=datetime.now(),
            ticket_id=1,
            old_status=Ticket.OPEN,
            new_status=Ticket.IN_PROGRESS
        )
        
        with pytest.raises(FrozenInstanceError):
            event.old_status = Ticket.CLOSED
        
        with pytest.raises(FrozenInstanceError):
            event.new_status = Ticket.CLOSED
    
    def test_ticket_status_changed_equality(self):
        """Eventos con los mismos datos son iguales."""
        now = datetime.now()
        event1 = TicketStatusChanged(
            occurred_at=now,
            ticket_id=1,
            old_status=Ticket.OPEN,
            new_status=Ticket.IN_PROGRESS
        )
        event2 = TicketStatusChanged(
            occurred_at=now,
            ticket_id=1,
            old_status=Ticket.OPEN,
            new_status=Ticket.IN_PROGRESS
        )
        
        assert event1 == event2
    
    def test_ticket_status_changed_inheritance(self):
        """TicketStatusChanged hereda de DomainEvent."""
        event = TicketStatusChanged(
            occurred_at=datetime.now(),
            ticket_id=1,
            old_status=Ticket.OPEN,
            new_status=Ticket.CLOSED
        )
        
        assert isinstance(event, DomainEvent)
    
    def test_different_events_are_not_equal(self):
        """Eventos con datos diferentes no son iguales."""
        now = datetime.now()
        event1 = TicketStatusChanged(
            occurred_at=now,
            ticket_id=1,
            old_status=Ticket.OPEN,
            new_status=Ticket.IN_PROGRESS
        )
        event2 = TicketStatusChanged(
            occurred_at=now,
            ticket_id=1,
            old_status=Ticket.IN_PROGRESS,
            new_status=Ticket.CLOSED
        )
        
        assert event1 != event2


class TestEventTimestamps:
    """Tests de timestamps en eventos."""
    
    def test_event_timestamp_precision(self):
        """Los eventos capturan timestamps con precisión."""
        before = datetime.now()
        event = TicketCreated(
            occurred_at=datetime.now(),
            ticket_id=1,
            title="T",
            description="D",
            status=Ticket.OPEN
        )
        after = datetime.now()
        
        assert before <= event.occurred_at <= after
    
    def test_events_can_have_same_timestamp(self):
        """Múltiples eventos pueden tener el mismo timestamp."""
        now = datetime.now()
        
        event1 = TicketCreated(
            occurred_at=now,
            ticket_id=1,
            title="T1",
            description="D1",
            status=Ticket.OPEN
        )
        event2 = TicketCreated(
            occurred_at=now,
            ticket_id=2,
            title="T2",
            description="D2",
            status=Ticket.OPEN
        )
        
        assert event1.occurred_at == event2.occurred_at
        assert event1 != event2  # Pero son eventos diferentes
