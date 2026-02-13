"""
Tests unitarios del TicketFactory.
Prueban la validación y creación correcta de entidades.
"""


from datetime import datetime

from tickets.domain.entities import Ticket
from tickets.domain.factories import TicketFactory
from tickets.domain.exceptions import InvalidTicketData


class TestTicketFactory:
    """Tests del factory para creación de tickets."""
    
    def test_factory_creates_valid_ticket(self):
        """Factory crea un ticket válido en estado OPEN."""
        ticket = TicketFactory.create("Title", "Description")
        
        assert ticket.title == "Title"
        assert ticket.description == "Description"
        assert ticket.status == Ticket.OPEN
        assert ticket.id is None
        assert isinstance(ticket.created_at, datetime)
    
    def test_factory_rejects_empty_title(self):
        """Factory rechaza título vacío."""
        with pytest.raises(InvalidTicketData, match="título"):
            TicketFactory.create("", "Description")
    
    def test_factory_rejects_whitespace_only_title(self):
        """Factory rechaza título con solo espacios."""
        with pytest.raises(InvalidTicketData, match="título"):
            TicketFactory.create("   ", "Description")
    
    def test_factory_rejects_none_title(self):
        """Factory rechaza título None."""
        with pytest.raises(InvalidTicketData):
            TicketFactory.create(None, "Description")
    
    def test_factory_rejects_empty_description(self):
        """Factory rechaza descripción vacía."""
        with pytest.raises(InvalidTicketData, match="descripción"):
            TicketFactory.create("Title", "")
    
    def test_factory_rejects_whitespace_only_description(self):
        """Factory rechaza descripción con solo espacios."""
        with pytest.raises(InvalidTicketData, match="descripción"):
            TicketFactory.create("Title", "   ")
    
    def test_factory_rejects_none_description(self):
        """Factory rechaza descripción None."""
        with pytest.raises(InvalidTicketData):
            TicketFactory.create("Title", None)
    
    def test_factory_strips_whitespace(self):
        """Factory elimina espacios en blanco al inicio y final."""
        ticket = TicketFactory.create("  Title  ", "  Description  ")
        
        assert ticket.title == "Title"
        assert ticket.description == "Description"
    
    def test_factory_preserves_internal_whitespace(self):
        """Factory preserva espacios internos en título y descripción."""
        ticket = TicketFactory.create(
            "  Multi Word Title  ",
            "  Description with spaces  "
        )
        
        assert ticket.title == "Multi Word Title"
        assert ticket.description == "Description with spaces"
    
    def test_factory_creates_ticket_with_correct_timestamp(self):
        """Factory crea tickets con timestamp correcto."""
        before = datetime.now()
        ticket = TicketFactory.create("Title", "Description")
        after = datetime.now()
        
        assert before <= ticket.created_at <= after
    
    def test_factory_creates_independent_instances(self):
        """Factory crea instancias independientes."""
        ticket1 = TicketFactory.create("Title1", "Desc1")
        ticket2 = TicketFactory.create("Title2", "Desc2")
        
        assert ticket1 is not ticket2
        assert ticket1.title != ticket2.title
        assert ticket1.created_at != ticket2.created_at


class TestTicketFactoryValidation:
    """Tests de validación estricta del factory."""
    
    def test_factory_validates_title_length_minimum(self):
        """Factory valida longitud mínima de título (implícito en no vacío)."""
        # Título de 1 caracter debería ser válido
        ticket = TicketFactory.create("T", "Description")
        assert ticket.title == "T"
    
    def test_factory_accepts_long_title(self):
        """Factory acepta títulos largos."""
        long_title = "A" * 500
        ticket = TicketFactory.create(long_title, "Description")
        assert ticket.title == long_title
    
    def test_factory_accepts_long_description(self):
        """Factory acepta descripciones largas."""
        long_desc = "B" * 5000
        ticket = TicketFactory.create("Title", long_desc)
        assert ticket.description == long_desc
    
    def test_factory_accepts_special_characters(self):
        """Factory acepta caracteres especiales."""
        ticket = TicketFactory.create(
            "Title #123 @user",
            "Description with émojis 🎉 and symbols $%^&*()"
        )
        assert ticket.title == "Title #123 @user"
        assert "🎉" in ticket.description
    
    def test_factory_accepts_multiline_description(self):
        """Factory acepta descripciones multilínea."""
        description = """
        Line 1
        Line 2
        Line 3
        """
        ticket = TicketFactory.create("Title", description)
        assert "Line 1" in ticket.description
        assert "Line 2" in ticket.description
        assert "Line 3" in ticket.description
