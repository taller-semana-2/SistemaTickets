"""
Tests unitarios de excepciones de dominio.
Verifican que las excepciones se lanzan correctamente y contienen la información necesaria.
"""


from tickets.domain.exceptions import (
    DomainException,
    InvalidTicketStateTransition,
    TicketAlreadyClosed,
    InvalidTicketData
)
from tickets.domain.entities import Ticket


class TestDomainException:
    """Tests de la excepción base DomainException."""
    
    def test_domain_exception_is_exception(self):
        """DomainException hereda de Exception."""
        exc = DomainException("Test error")
        assert isinstance(exc, Exception)
    
    def test_domain_exception_has_message(self):
        """DomainException puede tener mensaje."""
        exc = DomainException("Custom message")
        assert str(exc) == "Custom message"


class TestInvalidTicketStateTransition:
    """Tests de la excepción InvalidTicketStateTransition."""
    
    def test_invalid_state_transition_has_states(self):
        """InvalidTicketStateTransition guarda estados."""
        exc = InvalidTicketStateTransition(Ticket.OPEN, Ticket.CLOSED)
        
        assert exc.current_status == Ticket.OPEN
        assert exc.new_status == Ticket.CLOSED
    
    def test_invalid_state_transition_message(self):
        """InvalidTicketStateTransition tiene mensaje descriptivo."""
        exc = InvalidTicketStateTransition(Ticket.IN_PROGRESS, Ticket.OPEN)
        message = str(exc)
        
        assert "IN_PROGRESS" in message
        assert "OPEN" in message
        assert "No se puede cambiar" in message or "cambiar" in message.lower()
    
    def test_invalid_state_transition_is_domain_exception(self):
        """InvalidTicketStateTransition hereda de DomainException."""
        exc = InvalidTicketStateTransition(Ticket.OPEN, Ticket.CLOSED)
        assert isinstance(exc, DomainException)
    
    def test_can_be_raised_and_caught(self):
        """La excepción puede ser lanzada y capturada."""
        with pytest.raises(InvalidTicketStateTransition) as exc_info:
            raise InvalidTicketStateTransition(Ticket.OPEN, Ticket.CLOSED)
        
        assert exc_info.value.current_status == Ticket.OPEN
        assert exc_info.value.new_status == Ticket.CLOSED


class TestTicketAlreadyClosed:
    """Tests de la excepción TicketAlreadyClosed."""
    
    def test_ticket_already_closed_has_ticket_id(self):
        """TicketAlreadyClosed guarda el ID del ticket."""
        exc = TicketAlreadyClosed(ticket_id=123)
        assert exc.ticket_id == 123
    
    def test_ticket_already_closed_message(self):
        """TicketAlreadyClosed tiene mensaje descriptivo."""
        exc = TicketAlreadyClosed(ticket_id=456)
        message = str(exc)
        
        assert "456" in message
        assert "cerrado" in message.lower()
        assert "no puede" in message.lower() or "cannot" in message.lower()
    
    def test_ticket_already_closed_is_domain_exception(self):
        """TicketAlreadyClosed hereda de DomainException."""
        exc = TicketAlreadyClosed(ticket_id=1)
        assert isinstance(exc, DomainException)
    
    def test_can_be_raised_and_caught(self):
        """La excepción puede ser lanzada y capturada."""
        with pytest.raises(TicketAlreadyClosed) as exc_info:
            raise TicketAlreadyClosed(ticket_id=789)
        
        assert exc_info.value.ticket_id == 789


class TestInvalidTicketData:
    """Tests de la excepción InvalidTicketData."""
    
    def test_invalid_ticket_data_can_have_message(self):
        """InvalidTicketData puede tener mensaje personalizado."""
        exc = InvalidTicketData("El título no puede estar vacío")
        assert "título" in str(exc) or "title" in str(exc).lower()
    
    def test_invalid_ticket_data_is_domain_exception(self):
        """InvalidTicketData hereda de DomainException."""
        exc = InvalidTicketData("Invalid data")
        assert isinstance(exc, DomainException)
    
    def test_can_be_raised_for_empty_title(self):
        """Puede ser lanzada para título vacío."""
        with pytest.raises(InvalidTicketData) as exc_info:
            raise InvalidTicketData("El título no puede estar vacío")
        
        assert "título" in str(exc_info.value).lower() or "title" in str(exc_info.value).lower()
    
    def test_can_be_raised_for_empty_description(self):
        """Puede ser lanzada para descripción vacía."""
        with pytest.raises(InvalidTicketData) as exc_info:
            raise InvalidTicketData("La descripción no puede estar vacía")
        
        assert "descripción" in str(exc_info.value).lower() or "description" in str(exc_info.value).lower()
    
    def test_can_be_raised_without_message(self):
        """Puede ser lanzada sin mensaje."""
        exc = InvalidTicketData()
        assert isinstance(exc, InvalidTicketData)


class TestExceptionHierarchy:
    """Tests de la jerarquía de excepciones."""
    
    def test_all_domain_exceptions_inherit_from_domain_exception(self):
        """Todas las excepciones de dominio heredan de DomainException."""
        exceptions = [
            InvalidTicketStateTransition(Ticket.OPEN, Ticket.CLOSED),
            TicketAlreadyClosed(1),
            InvalidTicketData("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, DomainException)
            assert isinstance(exc, Exception)
    
    def test_can_catch_all_domain_exceptions(self):
        """Se pueden capturar todas las excepciones de dominio con DomainException."""
        exceptions = [
            InvalidTicketStateTransition(Ticket.OPEN, Ticket.CLOSED),
            TicketAlreadyClosed(1),
            InvalidTicketData("test")
        ]
        
        for exc in exceptions:
            try:
                raise exc
            except DomainException:
                pass  # Exitoso
            except Exception:
                pytest.fail("No se capturó como DomainException")
