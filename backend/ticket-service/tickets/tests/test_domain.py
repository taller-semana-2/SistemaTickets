"""
Tests de la capa de dominio (puro Python, sin Django).
Prueban reglas de negocio, entidades, factories y excepciones.
"""

import pytest
from datetime import datetime

from tickets.domain.entities import Ticket
from tickets.domain.factories import TicketFactory
from tickets.domain.exceptions import (
    InvalidTicketData,
    TicketAlreadyClosed
)
from tickets.domain.events import TicketCreated, TicketStatusChanged


class TestTicketEntity:
    """Tests de la entidad Ticket (reglas de negocio)."""
    
    def test_create_ticket_with_valid_data(self):
        """Crear un ticket con datos válidos inicia en estado OPEN."""
        ticket = Ticket.create("Test Title", "Test Description")
        
        assert ticket.title == "Test Title"
        assert ticket.description == "Test Description"
        assert ticket.status == Ticket.OPEN
        assert ticket.id is None  # ID asignado al persistir
        assert isinstance(ticket.created_at, datetime)
    
    def test_ticket_entity_validates_initial_status(self):
        """La entidad valida que el estado inicial sea válido."""
        with pytest.raises(ValueError, match="Estado inválido"):
            Ticket(
                id=1,
                title="Test",
                description="Desc",
                status="INVALID",
                created_at=datetime.now()
            )
    
    def test_change_status_from_open_to_in_progress(self):
        """Cambiar estado de OPEN a IN_PROGRESS genera evento."""
        ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            created_at=datetime.now()
        )
        
        ticket.change_status(Ticket.IN_PROGRESS)
        
        assert ticket.status == Ticket.IN_PROGRESS
        events = ticket.collect_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], TicketStatusChanged)
        assert events[0].old_status == Ticket.OPEN
        assert events[0].new_status == Ticket.IN_PROGRESS
        assert events[0].ticket_id == 1
    
    def test_change_status_from_in_progress_to_closed(self):
        """Cambiar estado de IN_PROGRESS a CLOSED genera evento."""
        ticket = Ticket(
            id=2,
            title="Test",
            description="Desc",
            status=Ticket.IN_PROGRESS,
            created_at=datetime.now()
        )
        
        ticket.change_status(Ticket.CLOSED)
        
        assert ticket.status == Ticket.CLOSED
        events = ticket.collect_domain_events()
        assert len(events) == 1
        assert events[0].new_status == Ticket.CLOSED
    
    def test_cannot_change_status_of_closed_ticket(self):
        """No se puede cambiar el estado de un ticket cerrado."""
        ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.CLOSED,
            created_at=datetime.now()
        )
        
        with pytest.raises(TicketAlreadyClosed) as exc_info:
            ticket.change_status(Ticket.OPEN)
        
        assert exc_info.value.ticket_id == 1
        assert "cerrado" in str(exc_info.value).lower()
    
    def test_change_status_is_idempotent(self):
        """Cambiar al mismo estado no genera eventos (idempotente)."""
        ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            created_at=datetime.now()
        )
        
        ticket.change_status(Ticket.OPEN)  # Mismo estado
        
        events = ticket.collect_domain_events()
        assert len(events) == 0  # No se generaron eventos
        assert ticket.status == Ticket.OPEN
    
    def test_invalid_status_raises_error(self):
        """Intentar cambiar a un estado inválido lanza ValueError."""
        ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            created_at=datetime.now()
        )
        
        with pytest.raises(ValueError, match="Estado inválido"):
            ticket.change_status("INVALID_STATUS")
    
    def test_multiple_status_changes_generate_multiple_events(self):
        """Múltiples cambios de estado generan múltiples eventos."""
        ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            created_at=datetime.now()
        )
        
        ticket.change_status(Ticket.IN_PROGRESS)
        ticket.change_status(Ticket.CLOSED)
        
        events = ticket.collect_domain_events()
        assert len(events) == 2
        assert events[0].new_status == Ticket.IN_PROGRESS
        assert events[1].new_status == Ticket.CLOSED
    
    def test_collect_domain_events_clears_list(self):
        """Recolectar eventos limpia la lista interna."""
        ticket = Ticket(
            id=1,
            title="Test",
            description="Desc",
            status=Ticket.OPEN,
            created_at=datetime.now()
        )
        
        ticket.change_status(Ticket.IN_PROGRESS)
        
        # Primera recolección
        events1 = ticket.collect_domain_events()
        assert len(events1) == 1
        
        # Segunda recolección debe estar vacía
        events2 = ticket.collect_domain_events()
        assert len(events2) == 0


class TestTicketFactory:
    """Tests del factory para creación de tickets."""
    
    def test_factory_creates_valid_ticket(self):
        """Factory crea un ticket válido en estado OPEN."""
        ticket = TicketFactory.create("Title", "Description")
        
        assert ticket.title == "Title"
        assert ticket.description == "Description"
        assert ticket.status == Ticket.OPEN
        assert ticket.id is None
    
    def test_factory_rejects_empty_title(self):
        """Factory rechaza título vacío."""
        with pytest.raises(InvalidTicketData, match="título"):
            TicketFactory.create("", "Description")
    
    def test_factory_rejects_whitespace_only_title(self):
        """Factory rechaza título con solo espacios."""
        with pytest.raises(InvalidTicketData, match="título"):
            TicketFactory.create("   ", "Description")
    
    def test_factory_rejects_empty_description(self):
        """Factory rechaza descripción vacía."""
        with pytest.raises(InvalidTicketData, match="descripción"):
            TicketFactory.create("Title", "")
    
    def test_factory_rejects_whitespace_only_description(self):
        """Factory rechaza descripción con solo espacios."""
        with pytest.raises(InvalidTicketData, match="descripción"):
            TicketFactory.create("Title", "   ")
    
    def test_factory_strips_whitespace(self):
        """Factory elimina espacios en blanco al inicio y final."""
        ticket = TicketFactory.create("  Title  ", "  Description  ")
        
        assert ticket.title == "Title"
        assert ticket.description == "Description"
    
    def test_factory_preserves_internal_whitespace(self):
        """Factory preserva espacios internos en título y descripción."""
        ticket = TicketFactory.create("Test  Title", "Test  Description")
        
        assert ticket.title == "Test  Title"
        assert ticket.description == "Test  Description"


class TestDomainEvents:
    """Tests de eventos de dominio."""
    
    def test_ticket_created_event_is_immutable(self):
        """Los eventos de dominio son inmutables (frozen)."""
        event = TicketCreated(
            occurred_at=datetime.now(),
            ticket_id=1,
            title="Test",
            description="Desc",
            status="OPEN"
        )
        
        # Intentar modificar debe fallar
        with pytest.raises(Exception):  # dataclass frozen raises
            event.ticket_id = 999
    
    def test_ticket_status_changed_event_is_immutable(self):
        """TicketStatusChanged es inmutable."""
        event = TicketStatusChanged(
            occurred_at=datetime.now(),
            ticket_id=1,
            old_status="OPEN",
            new_status="CLOSED"
        )
        
        with pytest.raises(Exception):
            event.new_status = "OTHER"
