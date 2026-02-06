from django.test import TestCase
from unittest.mock import patch

from .models import Ticket
from .serializer import TicketSerializer
from .views import TicketViewSet


class TicketServiceUnitTests(TestCase):
	# Prueba: creación del modelo Ticket (caso feliz)
	# Qué verifica:
	# - al crear un Ticket sin status explícito, el status por defecto es "OPEN"
	# - se establece el campo created_at automáticamente
	def test_ticket_model_creation(self):
		t = Ticket.objects.create(title="A", description="Desc")
		self.assertEqual(t.status, "OPEN")
		self.assertIsNotNone(t.created_at)

	# Prueba: el serializador crea un ticket válido
	# Qué verifica:
	# - los datos válidos son aceptados por el serializer
	# - al guardar, se crea un Ticket con los campos esperados
	def test_serializer_creates_ticket(self):
		data = {"title": "S", "description": "D"}
		s = TicketSerializer(data=data)
		self.assertTrue(s.is_valid())
		ticket = s.save()
		self.assertEqual(ticket.title, "S")

	# Prueba: la vista invoca la función que publica el evento en RabbitMQ
	# Qué verifica:
	# - `perform_create` guarda el ticket y luego llama a `publish_ticket_created`
	# - si la publicación está parcheada, comprobamos que fue invocada
	def test_perform_create_calls_publish(self):
		data = {"title": "X", "description": "Y"}
		s = TicketSerializer(data=data)
		self.assertTrue(s.is_valid())

		with patch('tickets.views.publish_ticket_created') as mock_pub:
			view = TicketViewSet()
			view.perform_create(s)
			# publish_ticket_created debe haberse llamado con el id del ticket creado
			self.assertTrue(mock_pub.called)

	# Prueba: serializador rechaza datos sin campo `title`
	# Qué verifica:
	# - la validación falla y reporta el campo faltante en los errores
	def test_serializer_invalid_missing_title(self):
		data = {"description": "No title"}
		s = TicketSerializer(data=data)
		self.assertFalse(s.is_valid())
		self.assertIn('title', s.errors)

	# Prueba: serializador rechaza títulos que exceden el máximo permitido
	# Qué verifica:
	# - la validación detecta `title` demasiado largo y lo reporta en errores
	def test_serializer_title_too_long(self):
		data = {"title": 'x' * 300, "description": "long"}
		s = TicketSerializer(data=data)
		self.assertFalse(s.is_valid())
		self.assertIn('title', s.errors)

	# Prueba: si la publicación falla, el ticket ya fue guardado en la BD
	# Qué verifica:
	# - `perform_create` guarda el ticket primero; si publish falla, la excepción se propaga
	# - el ticket persiste en la base de datos a pesar del fallo de publicación
	def test_perform_create_publish_raises_ticket_still_saved(self):
		data = {"title": "ERR", "description": "Will raise on publish"}
		s = TicketSerializer(data=data)
		self.assertTrue(s.is_valid())

		# simular fallo en publish (network/rabbit caído)
		with patch('tickets.views.publish_ticket_created', side_effect=Exception('publish failed')):
			view = TicketViewSet()
			with self.assertRaises(Exception):
				view.perform_create(s)

		# El ticket debe existir en la BD porque save() se llama antes de publish
		self.assertTrue(Ticket.objects.filter(title="ERR").exists())

	# Prueba: `publish_ticket_created` propaga excepción si falla la conexión a pika
	# Qué verifica:
	# - al fallar `pika.BlockingConnection`, la función de publish no silencia el error
	def test_publish_ticket_created_raises_when_pika_fails(self):
		# parchear BlockingConnection para que lance excepción y comprobar propagación
		from . import messaging
		with patch('tickets.messaging.events.pika.BlockingConnection', side_effect=Exception('conn fail')):
			with self.assertRaises(Exception):
				messaging.events.publish_ticket_created(12345)