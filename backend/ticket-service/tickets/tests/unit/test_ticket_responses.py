"""
Tests unitarios para respuestas de admin en tickets.
Issue #37: feat: validaciones de estado y obligatoriedad en respuestas (EP16, EP18)

Estos tests validan reglas de dominio puro (sin Django).
"""

import pytest
from datetime import datetime

from tickets.domain.entities import Ticket
from tickets.domain.exceptions import TicketAlreadyClosed, EmptyResponseError, ResponseTooLongError


class TestTicketResponses:
    """Tests de la entidad Ticket relacionados con respuestas de admin."""

    def _make_ticket(
        self,
        status: str = Ticket.OPEN,
        ticket_id: int = 1,
        title: str = "Ticket de prueba",
    ) -> Ticket:
        """Helper: crea un Ticket de dominio con valores por defecto razonables."""
        return Ticket(
            id=ticket_id,
            title=title,
            description="Descripción de prueba",
            status=status,
            user_id="user-test",
            created_at=datetime(2026, 2, 20, 10, 0, 0),
        )

    def test_cannot_add_response_to_closed_ticket_ep16(self):
        """
        EP16 (R7): Admin no puede responder ticket en estado CLOSED.

        Scenario: Admin no puede responder ticket en estado CLOSED (EP16)
          Given un ticket en estado "CLOSED"
          And el usuario autenticado tiene rol "ADMIN"
          When intenta enviar una respuesta
          Then el sistema rechaza la accion
          And se informa que no se pueden responder tickets cerrados
        """
        # Arrange — ticket en estado CLOSED
        ticket = self._make_ticket(status=Ticket.CLOSED, ticket_id=42)

        # Act & Assert — intentar responder debe lanzar TicketAlreadyClosed
        with pytest.raises(TicketAlreadyClosed) as exc_info:
            ticket.add_response(
                text="Estamos revisando tu caso",
                admin_id="admin-001",
            )

        assert exc_info.value.ticket_id == 42

        # Verify — no se generaron eventos de dominio
        events = ticket.collect_domain_events()
        assert len(events) == 0, "No debe generar eventos al rechazar respuesta en ticket cerrado"

    def test_cannot_add_response_with_empty_text_ep18(self):
        """
        EP18 (R8): Respuesta con texto vacío es rechazada.
        Issue #37: feat: validaciones de estado y obligatoriedad en respuestas

        Scenario: Respuesta con texto vacío es rechazada (EP18)
          Given un ticket en estado "OPEN"
          And el usuario autenticado tiene rol "ADMIN"
          When intenta enviar una respuesta sin texto
          Then el sistema rechaza la acción
          And retorna un error indicando que el texto es obligatorio
        """
        # Arrange — ticket en estado OPEN (válido para respuestas)
        ticket = self._make_ticket(ticket_id=99)

        # Act & Assert — texto vacío debe lanzar EmptyResponseError
        with pytest.raises(EmptyResponseError) as exc_info:
            ticket.add_response(
                text="",
                admin_id="admin-001",
            )

        assert "obligatori" in str(exc_info.value).lower(), (
            "El mensaje de error debe indicar que el texto es obligatorio"
        )

        # Verify — no se generaron eventos de dominio
        events = ticket.collect_domain_events()
        assert len(events) == 0, "No debe generar eventos al rechazar respuesta con texto vacío"

        # Act & Assert — texto None también debe lanzar EmptyResponseError
        with pytest.raises(EmptyResponseError):
            ticket.add_response(
                text=None,
                admin_id="admin-001",
            )

    # --- Tests de límite de 2000 caracteres (Issue #77) ---

    def test_add_response_accepts_exactly_2000_chars(self):
        """
        Regla de negocio: El texto de la respuesta puede tener hasta 2000 caracteres.

        Scenario: Respuesta con exactamente 2000 caracteres es aceptada
          Given un ticket en estado OPEN
          When admin envía respuesta con exactamente 2000 caracteres
          Then la respuesta es aceptada sin error
        """
        ticket = self._make_ticket(ticket_id=50)

        text_2000 = "a" * 2000

        # Should NOT raise any exception
        ticket.add_response(text=text_2000, admin_id="admin-001")

    def test_add_response_rejects_2001_chars(self):
        """
        Regla de negocio: El texto de la respuesta NO puede exceder 2000 caracteres.

        Scenario: Respuesta con 2001 caracteres es rechazada
          Given un ticket en estado OPEN
          When admin envía respuesta con 2001 caracteres
          Then el sistema rechaza la acción con ResponseTooLongError
        """
        ticket = self._make_ticket(ticket_id=51)

        text_2001 = "b" * 2001

        with pytest.raises(ResponseTooLongError):
            ticket.add_response(text=text_2001, admin_id="admin-001")

    def test_add_response_accepts_short_text(self):
        """
        Regla de negocio: Textos cortos válidos son aceptados.

        Scenario: Respuesta con texto corto "OK" es aceptada
          Given un ticket en estado OPEN
          When admin envía respuesta con texto "OK"
          Then la respuesta es aceptada sin error
        """
        ticket = self._make_ticket(ticket_id=52)

        # Should NOT raise any exception
        ticket.add_response(text="OK", admin_id="admin-001")

    def test_response_too_long_error_message_includes_limit(self):
        """
        La excepción ResponseTooLongError debe incluir el límite de 2000
        en su mensaje para informar al usuario.
        """
        ticket = self._make_ticket(ticket_id=53)

        text_too_long = "c" * 2500

        with pytest.raises(ResponseTooLongError) as exc_info:
            ticket.add_response(text=text_too_long, admin_id="admin-001")

        assert "2000" in str(exc_info.value), (
            "El mensaje de error debe indicar el límite de 2000 caracteres"
        )
