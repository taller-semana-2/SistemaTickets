"""
Tests unitarios de la entidad Ticket (State Machine).
Prueban reglas de negocio y transiciones de estados.
"""


from datetime import datetime

from tickets.domain.entities import Ticket
from tickets.domain.exceptions import TicketAlreadyClosed
from tickets.domain.events import TicketStatusChanged


class TestTicketEntity:
    """Tests de la entidad Ticket y sus reglas de negocio."""
    
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
        """No se puede cambiar el estado de un ticket cerrado (regla de negocio)."""
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


class TestTicketStateMachine:
    """Tests de la máquina de estados del ticket."""
    
    def test_all_valid_state_transitions(self):
        """Todas las transiciones de estado válidas funcionan correctamente."""
        # OPEN -> IN_PROGRESS
        ticket = Ticket(1, "T", "D", Ticket.OPEN, datetime.now())
        ticket.change_status(Ticket.IN_PROGRESS)
        assert ticket.status == Ticket.IN_PROGRESS
        
        # IN_PROGRESS -> CLOSED
        ticket2 = Ticket(2, "T", "D", Ticket.IN_PROGRESS, datetime.now())
        ticket2.change_status(Ticket.CLOSED)
        assert ticket2.status == Ticket.CLOSED
        
        # OPEN -> CLOSED (salto directo permitido)
        ticket3 = Ticket(3, "T", "D", Ticket.OPEN, datetime.now())
        ticket3.change_status(Ticket.CLOSED)
        assert ticket3.status == Ticket.CLOSED
    
    def test_closed_is_final_state(self):
        """CLOSED es un estado final, no permite transiciones."""
        ticket = Ticket(1, "T", "D", Ticket.CLOSED, datetime.now())
        
        # Intentar cualquier transición desde CLOSED falla
        with pytest.raises(TicketAlreadyClosed):
            ticket.change_status(Ticket.OPEN)
        
        with pytest.raises(TicketAlreadyClosed):
            ticket.change_status(Ticket.IN_PROGRESS)
        
        with pytest.raises(TicketAlreadyClosed):
            ticket.change_status(Ticket.CLOSED)
    
    def test_state_machine_generates_correct_events(self):
        """La máquina de estados genera eventos correctos en cada transición."""
        ticket = Ticket(1, "Test", "Desc", Ticket.OPEN, datetime.now())
        
        # OPEN -> IN_PROGRESS
        ticket.change_status(Ticket.IN_PROGRESS)
        events = ticket.collect_domain_events()
        assert len(events) == 1
        assert events[0].old_status == Ticket.OPEN
        assert events[0].new_status == Ticket.IN_PROGRESS
        
        # IN_PROGRESS -> CLOSED
        ticket.change_status(Ticket.CLOSED)
        events = ticket.collect_domain_events()
        assert len(events) == 1
        assert events[0].old_status == Ticket.IN_PROGRESS
        assert events[0].new_status == Ticket.CLOSED
