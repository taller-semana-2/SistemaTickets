"""
Tests unitarios para respuestas de admin en tickets.
Issue #37: feat: validaciones de estado y obligatoriedad en respuestas (EP16, EP18)

Estos tests validan reglas de dominio puro (sin Django).
"""

import pytest
from datetime import datetime

from tickets.domain.entities import Ticket
from tickets.domain.exceptions import TicketAlreadyClosed


class TestTicketResponses:
    """Tests de la entidad Ticket relacionados con respuestas de admin."""

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
        ticket = Ticket(
            id=42,
            title="Problema con facturacion",
            description="No puedo descargar mi factura",
            status=Ticket.CLOSED,
            user_id="user-100",
            created_at=datetime(2026, 2, 19, 10, 0, 0),
        )

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
