from django.test import TestCase
from django.db import IntegrityError

from assignments.models import TicketAssignment
from assignments import tasks
from messaging.handlers import handle_ticket_created
from unittest.mock import patch
from django.utils import timezone
from datetime import timedelta


class AssignmentServiceTests(TestCase):
	# Prueba: caso feliz - cuando llega un ticket, se crea una asignación en DB
	# Qué verifica:
	# - `handle_ticket_created` crea un objeto TicketAssignment con el ticket_id dado
	# - la prioridad está entre las opciones esperadas
	# - el campo assigned_at queda establecido
	def test_handle_ticket_created_creates_assignment(self):
		ticket_id = "TICKET-1"
		handle_ticket_created(ticket_id)

		assignment = TicketAssignment.objects.get(ticket_id=ticket_id)
		self.assertIn(assignment.priority, ["high", "medium", "low"])
		self.assertIsNotNone(assignment.assigned_at)

	# Prueba: comportamiento ante duplicado - intentar crear dos asignaciones con mismo ticket_id
	# Qué verifica:
	# - la segunda llamada lanza IntegrityError debido a la restricción unique del modelo
	def test_handle_ticket_created_duplicate_ticket_raises(self):
		ticket_id = "DUP-1"
		handle_ticket_created(ticket_id)
		with self.assertRaises(IntegrityError):
			# la segunda creación con el mismo ticket_id debe lanzar IntegrityError
			handle_ticket_created(ticket_id)

	# Prueba: ejecutar la tarea Celery directamente
	# Qué verifica:
	# - llamar a `process_ticket.run` ejecuta la lógica de procesamiento sin necesitar broker
	# - al final existe un TicketAssignment con el ticket_id procesado
	def test_process_ticket_task_runs_handler(self):
		ticket_id = "TASK-1"
		# ejecutar la implementación de la tarea directamente (sin broker)
		tasks.process_ticket.run(ticket_id)
		self.assertTrue(TicketAssignment.objects.filter(ticket_id=ticket_id).exists())

	# Prueba: entrada inválida - pasar None como ticket_id
	# Qué verifica:
	# - la función `handle_ticket_created` lanza una excepción ante un ticket_id inválido
	def test_handle_ticket_created_invalid_ticketid_raises(self):
		# pasar un ticket_id inválido debería lanzar una excepción
		with self.assertRaises(Exception):
			handle_ticket_created(None)

	# Prueba: controlar la aleatoriedad de la prioridad mediante mock
	# Qué verifica:
	# - si `random.choice` devuelve 'high', la asignación creada debe tener prioridad 'high'
	def test_handle_ticket_created_sets_expected_priority_with_mock(self):
		ticket_id = "MOCK-1"
		with patch('messaging.handlers.random.choice', return_value='high'):
			handle_ticket_created(ticket_id)

		assignment = TicketAssignment.objects.get(ticket_id=ticket_id)
		self.assertEqual(assignment.priority, 'high')

	# Prueba: verificación de `__str__` y de timestamp de creación
	# Qué verifica:
	# - el método `__str__` incluye ticket_id y priority
	# - el campo `assigned_at` refleja una fecha reciente cuando se crea manualmente
	def test_ticketassignment_str_and_timestamp(self):
		ticket_id = "STR-1"
		# crear una asignación directamente
		now = timezone.now()
		a = TicketAssignment.objects.create(ticket_id=ticket_id, priority='low', assigned_at=now)

		# __str__ contiene ticket id y priority
		self.assertIn(ticket_id, str(a))
		self.assertIn('low', str(a))

		# assigned_at es reciente (dentro de un delta pequeño)
		self.assertTrue(timezone.now() - a.assigned_at < timedelta(seconds=5))

	# Prueba: ejecutar la tarea Celery usando `apply` para ejecución síncrona
	# Qué verifica:
	# - `process_ticket.apply` ejecuta la tarea en el proceso actual y produce el efecto esperado
	def test_process_ticket_apply_runs_task_synchronously(self):
		ticket_id = "APPLY-1"
		# usar Task.apply para ejecutar sincrónicamente sin broker
		tasks.process_ticket.apply(args=[ticket_id])
		self.assertTrue(TicketAssignment.objects.filter(ticket_id=ticket_id).exists())

