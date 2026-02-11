"""
Tests legacy actualizados para nueva arquitectura DDD/EDA.

NOTA: La mayoría de tests se han movido a tickets/tests/
Este archivo mantiene solo tests de compatibilidad con código legacy.

Para tests nuevos, ver:
- tickets/tests/test_domain.py
- tickets/tests/test_use_cases.py
- tickets/tests/test_infrastructure.py
- tickets/tests/test_views.py
- tickets/tests/test_integration.py
"""

from django.test import TestCase
from unittest.mock import patch, Mock

from .models import Ticket
from .serializer import TicketSerializer
from .views import TicketViewSet


class TicketServiceLegacyCompatibilityTests(TestCase):
	"""Tests de compatibilidad con código existente."""
	
	def test_ticket_model_creation(self):
		"""Test: creación del modelo Ticket (caso feliz)."""
		t = Ticket.objects.create(title="A", description="Desc")
		self.assertEqual(t.status, "OPEN")
		self.assertIsNotNone(t.created_at)

	def test_serializer_creates_ticket(self):
		"""Test: el serializador crea un ticket válido."""
		data = {"title": "S", "description": "D"}
		s = TicketSerializer(data=data)
		self.assertTrue(s.is_valid())
		ticket = s.save()
		self.assertEqual(ticket.title, "S")

	def test_perform_create_executes_use_case(self):
		"""Test: la vista ejecuta el caso de uso CreateTicket."""
		data = {"title": "X", "description": "Y"}
		s = TicketSerializer(data=data)
		self.assertTrue(s.is_valid())

		# Mockear el caso de uso en lugar de publish_ticket_created
		with patch.object(TicketViewSet, '__init__', lambda x: None):
			view = TicketViewSet()
			mock_use_case = Mock()
			
			# Simular que el caso de uso crea el ticket
			from .domain.entities import Ticket as DomainTicket
			from datetime import datetime
			mock_domain_ticket = DomainTicket(
				id=1,
				title="X",
				description="Y",
				status="OPEN",
				created_at=datetime.now()
			)
			mock_use_case.execute.return_value = mock_domain_ticket
			
			view.create_ticket_use_case = mock_use_case
			view.perform_create(s)
			
			# Verificar que se ejecutó el caso de uso
			self.assertTrue(mock_use_case.execute.called)

	def test_serializer_invalid_missing_title(self):
		"""Test: serializador rechaza datos sin campo `title`."""
		data = {"description": "No title"}
		s = TicketSerializer(data=data)
		self.assertFalse(s.is_valid())
		self.assertIn('title', s.errors)

	def test_serializer_title_too_long(self):
		"""Test: serializador rechaza títulos que exceden el máximo permitido."""
		data = {"title": 'x' * 300, "description": "long"}
		s = TicketSerializer(data=data)
		self.assertFalse(s.is_valid())
		self.assertIn('title', s.errors)

	def test_perform_create_with_use_case_failure_propagates(self):
		"""Test: si el caso de uso falla, la excepción se propaga."""
		data = {"title": "ERR", "description": "Will raise"}
		s = TicketSerializer(data=data)
		self.assertTrue(s.is_valid())

		# Simular fallo en el caso de uso
		with patch.object(TicketViewSet, '__init__', lambda x: None):
			view = TicketViewSet()
			mock_use_case = Mock()
			mock_use_case.execute.side_effect = Exception('Use case failed')
			view.create_ticket_use_case = mock_use_case

			# Debe propagar la excepción
			with self.assertRaises(Exception):
				view.perform_create(s)


# ==================== TESTS MIGRADOS ====================
# Los siguientes tests han sido MIGRADOS a tickets/tests/
#
# 1. Tests de dominio → test_domain.py
#    - Reglas de negocio de Ticket
#    - TicketFactory
#    - Domain Events
#
# 2. Tests de casos de uso → test_use_cases.py
#    - CreateTicketUseCase
#    - ChangeTicketStatusUseCase
#
# 3. Tests de infraestructura → test_infrastructure.py
#    - DjangoTicketRepository
#    - RabbitMQEventPublisher
#
# 4. Tests de ViewSet → test_views.py
#    - Integración HTTP con casos de uso
#
# 5. Tests de integración → test_integration.py
#    - Flujos end-to-end
#    - Tests con RabbitMQ (mockeable)
#
# Ver tickets/tests/ para la suite completa de tests DDD/EDA
