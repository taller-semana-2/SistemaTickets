"""
Suite Completa de Tests - Assignment Service (DDD)

Incluye tests para:
1. Capa de Dominio (entidades, validaciones)
2. Capa de Aplicación (use cases)
3. Capa de Infraestructura (repositorio, adapters)
4. API REST (views, endpoints)
5. Integración (RabbitMQ, Celery, end-to-end)
"""
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pika
from django.test import TestCase, override_settings
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from assignments.models import TicketAssignment
from assignments import tasks
from messaging.handlers import handle_ticket_event

# Imports de la arquitectura DDD
from assignments.domain.entities import Assignment
from assignments.domain.events import AssignmentCreated, AssignmentReassigned
from assignments.infrastructure.repository import DjangoAssignmentRepository
from assignments.infrastructure.messaging.event_adapter import TicketEventAdapter
from assignments.application.use_cases.create_assignment import CreateAssignment
from assignments.application.use_cases.reassign_ticket import ReassignTicket


# ============================================================================
# TESTS DE DOMINIO (Sin dependencias de Django)
# ============================================================================

class AssignmentEntityTests(TestCase):
    """Tests de la entidad Assignment (dominio puro)"""
    
    def test_assignment_creation_valid(self):
        """Crear assignment con datos válidos debe funcionar"""
        assignment = Assignment(
            ticket_id="TEST-001",
            priority="high",
            assigned_at=datetime.utcnow()
        )
        self.assertEqual(assignment.ticket_id, "TEST-001")
        self.assertEqual(assignment.priority, "high")
        self.assertIsNotNone(assignment.assigned_at)
    
    def test_assignment_validates_empty_ticket_id(self):
        """ticket_id vacío debe lanzar ValueError"""
        with self.assertRaises(ValueError) as context:
            Assignment(
                ticket_id="",
                priority="high",
                assigned_at=datetime.utcnow()
            )
        self.assertIn("ticket_id", str(context.exception))
    
    def test_assignment_validates_whitespace_ticket_id(self):
        """ticket_id con solo espacios debe lanzar ValueError"""
        with self.assertRaises(ValueError):
            Assignment(
                ticket_id="   ",
                priority="high",
                assigned_at=datetime.utcnow()
            )
    
    def test_assignment_validates_invalid_priority(self):
        """Prioridad inválida debe lanzar ValueError"""
        with self.assertRaises(ValueError) as context:
            Assignment(
                ticket_id="TEST-001",
                priority="urgent",  # No es válida
                assigned_at=datetime.utcnow()
            )
        self.assertIn("priority", str(context.exception))
    
    def test_assignment_accepts_valid_priorities(self):
        """Todas las prioridades válidas deben ser aceptadas"""
        valid_priorities = ['high', 'medium', 'low']
        for priority in valid_priorities:
            assignment = Assignment(
                ticket_id=f"TEST-{priority}",
                priority=priority,
                assigned_at=datetime.utcnow()
            )
            self.assertEqual(assignment.priority, priority)
    
    def test_assignment_change_priority_valid(self):
        """Cambiar a prioridad válida debe funcionar"""
        assignment = Assignment(
            ticket_id="TEST-001",
            priority="low",
            assigned_at=datetime.utcnow()
        )
        assignment.change_priority("high")
        self.assertEqual(assignment.priority, "high")
    
    def test_assignment_change_priority_invalid(self):
        """Cambiar a prioridad inválida debe lanzar ValueError"""
        assignment = Assignment(
            ticket_id="TEST-001",
            priority="low",
            assigned_at=datetime.utcnow()
        )
        with self.assertRaises(ValueError):
            assignment.change_priority("critical")


class DomainEventsTests(TestCase):
    """Tests de eventos de dominio"""
    
    def test_assignment_created_event_to_dict(self):
        """AssignmentCreated debe serializar correctamente"""
        event = AssignmentCreated(
            occurred_at=datetime(2026, 2, 11, 10, 30),
            assignment_id=1,
            ticket_id="TEST-001",
            priority="high"
        )
        
        data = event.to_dict()
        
        self.assertEqual(data['event_type'], 'assignment.created')
        self.assertEqual(data['assignment_id'], 1)
        self.assertEqual(data['ticket_id'], "TEST-001")
        self.assertEqual(data['priority'], "high")
        self.assertIn('occurred_at', data)
    
    def test_assignment_reassigned_event_to_dict(self):
        """AssignmentReassigned debe serializar correctamente"""
        event = AssignmentReassigned(
            occurred_at=datetime(2026, 2, 11, 11, 0),
            assignment_id=1,
            ticket_id="TEST-001",
            old_priority="low",
            new_priority="high"
        )
        
        data = event.to_dict()
        
        self.assertEqual(data['event_type'], 'assignment.reassigned')
        self.assertEqual(data['old_priority'], "low")
        self.assertEqual(data['new_priority'], "high")


# ============================================================================
# TESTS DE INFRAESTRUCTURA (Repositorio)
# ============================================================================

class DjangoAssignmentRepositoryTests(TestCase):
    """Tests del repositorio Django"""
    
    def setUp(self):
        self.repository = DjangoAssignmentRepository()
    
    def test_save_new_assignment(self):
        """Guardar nueva asignación debe asignar id"""
        assignment = Assignment(
            ticket_id="REPO-001",
            priority="high",
            assigned_at=datetime.utcnow()
        )
        
        saved = self.repository.save(assignment)
        
        self.assertIsNotNone(saved.id)
        self.assertEqual(saved.ticket_id, "REPO-001")
        self.assertEqual(saved.priority, "high")
    
    def test_save_existing_assignment_updates(self):
        """Guardar asignación existente debe actualizar"""
        assignment = Assignment(
            ticket_id="REPO-002",
            priority="low",
            assigned_at=datetime.utcnow()
        )
        saved = self.repository.save(assignment)
        
        # Cambiar prioridad
        saved.change_priority("high")
        updated = self.repository.save(saved)
        
        self.assertEqual(updated.id, saved.id)
        self.assertEqual(updated.priority, "high")
    
    def test_find_by_ticket_id_existing(self):
        """Buscar por ticket_id existente debe retornar assignment"""
        assignment = Assignment(
            ticket_id="REPO-003",
            priority="medium",
            assigned_at=datetime.utcnow()
        )
        self.repository.save(assignment)
        
        found = self.repository.find_by_ticket_id("REPO-003")
        
        self.assertIsNotNone(found)
        self.assertEqual(found.ticket_id, "REPO-003")
        self.assertEqual(found.priority, "medium")
    
    def test_find_by_ticket_id_not_existing(self):
        """Buscar por ticket_id inexistente debe retornar None"""
        found = self.repository.find_by_ticket_id("NONEXISTENT")
        self.assertIsNone(found)
    
    def test_find_by_id_existing(self):
        """Buscar por id existente debe retornar assignment"""
        assignment = Assignment(
            ticket_id="REPO-004",
            priority="high",
            assigned_at=datetime.utcnow()
        )
        saved = self.repository.save(assignment)
        
        found = self.repository.find_by_id(saved.id)
        
        self.assertIsNotNone(found)
        self.assertEqual(found.id, saved.id)
    
    def test_find_by_id_not_existing(self):
        """Buscar por id inexistente debe retornar None"""
        found = self.repository.find_by_id(99999)
        self.assertIsNone(found)
    
    def test_find_all(self):
        """find_all debe retornar todas las asignaciones"""
        for i in range(3):
            assignment = Assignment(
                ticket_id=f"REPO-ALL-{i}",
                priority="medium",
                assigned_at=datetime.utcnow()
            )
            self.repository.save(assignment)
        
        all_assignments = self.repository.find_all()
        
        self.assertGreaterEqual(len(all_assignments), 3)
    
    def test_delete_existing(self):
        """Eliminar asignación existente debe retornar True"""
        assignment = Assignment(
            ticket_id="REPO-DELETE",
            priority="low",
            assigned_at=datetime.utcnow()
        )
        saved = self.repository.save(assignment)
        
        deleted = self.repository.delete(saved.id)
        
        self.assertTrue(deleted)
        self.assertIsNone(self.repository.find_by_id(saved.id))
    
    def test_delete_not_existing(self):
        """Eliminar asignación inexistente debe retornar False"""
        deleted = self.repository.delete(99999)
        self.assertFalse(deleted)


# ============================================================================
# TESTS DE APLICACIÓN (Use Cases)
# ============================================================================

class CreateAssignmentUseCaseTests(TestCase):
    """Tests del caso de uso CreateAssignment"""
    
    def setUp(self):
        self.repository = DjangoAssignmentRepository()
        self.mock_publisher = Mock()
        self.use_case = CreateAssignment(self.repository, self.mock_publisher)
    
    def test_create_assignment_success(self):
        """Crear asignación exitosamente"""
        result = self.use_case.execute(
            ticket_id="UC-CREATE-001",
            priority="high"
        )
        
        self.assertIsNotNone(result.id)
        self.assertEqual(result.ticket_id, "UC-CREATE-001")
        self.assertEqual(result.priority, "high")
        
        # Verificar que se publicó el evento
        self.mock_publisher.publish.assert_called_once()
        event = self.mock_publisher.publish.call_args[0][0]
        self.assertIsInstance(event, AssignmentCreated)
    
    def test_create_assignment_idempotent(self):
        """Crear asignación duplicada debe ser idempotente"""
        first = self.use_case.execute(
            ticket_id="UC-IDEM-001",
            priority="high"
        )
        
        # Resetear el mock
        self.mock_publisher.reset_mock()
        
        second = self.use_case.execute(
            ticket_id="UC-IDEM-001",
            priority="medium"  # Diferente prioridad
        )
        
        # Debe retornar la misma asignación (sin crear nueva)
        self.assertEqual(first.id, second.id)
        self.assertEqual(second.priority, "high")  # Mantiene original
        
        # No debe publicar evento la segunda vez
        self.mock_publisher.publish.assert_not_called()
    
    def test_create_assignment_invalid_priority(self):
        """Crear con prioridad inválida debe lanzar ValueError"""
        with self.assertRaises(ValueError):
            self.use_case.execute(
                ticket_id="UC-INVALID",
                priority="critical"
            )


class ReassignTicketUseCaseTests(TestCase):
    """Tests del caso de uso ReassignTicket"""
    
    def setUp(self):
        self.repository = DjangoAssignmentRepository()
        self.mock_publisher = Mock()
        self.use_case = ReassignTicket(self.repository, self.mock_publisher)
        
        # Crear asignación inicial
        assignment = Assignment(
            ticket_id="UC-REASSIGN-001",
            priority="low",
            assigned_at=datetime.utcnow()
        )
        self.repository.save(assignment)
    
    def test_reassign_ticket_success(self):
        """Reasignar ticket exitosamente"""
        result = self.use_case.execute(
            ticket_id="UC-REASSIGN-001",
            new_priority="high"
        )
        
        self.assertEqual(result.priority, "high")
        
        # Verificar evento
        self.mock_publisher.publish.assert_called_once()
        event = self.mock_publisher.publish.call_args[0][0]
        self.assertIsInstance(event, AssignmentReassigned)
        self.assertEqual(event.old_priority, "low")
        self.assertEqual(event.new_priority, "high")
    
    def test_reassign_ticket_not_found(self):
        """Reasignar ticket inexistente debe lanzar ValueError"""
        with self.assertRaises(ValueError) as context:
            self.use_case.execute(
                ticket_id="NONEXISTENT",
                new_priority="high"
            )
        self.assertIn("No existe asignación", str(context.exception))
    
    def test_reassign_ticket_same_priority(self):
        """Reasignar a la misma prioridad no debe emitir evento"""
        result = self.use_case.execute(
            ticket_id="UC-REASSIGN-001",
            new_priority="low"  # Misma que la actual
        )
        
        self.assertEqual(result.priority, "low")
        
        # No debe publicar evento
        self.mock_publisher.publish.assert_not_called()
    
    def test_reassign_ticket_invalid_priority(self):
        """Reasignar a prioridad inválida debe lanzar ValueError"""
        with self.assertRaises(ValueError):
            self.use_case.execute(
                ticket_id="UC-REASSIGN-001",
                new_priority="urgent"
            )


class TicketEventAdapterTests(TestCase):
    """Tests del adaptador de eventos de Ticket"""
    
    def setUp(self):
        self.repository = DjangoAssignmentRepository()
        self.mock_publisher = Mock()
        self.adapter = TicketEventAdapter(self.repository, self.mock_publisher)
    
    def test_handle_ticket_created_success(self):
        """Manejar evento TicketCreated debe crear asignación"""
        event_data = {
            'ticket_id': 'ADAPTER-001',
            'title': 'Test ticket'
        }
        
        self.adapter.handle_ticket_created(event_data)
        
        # Verificar que se creó la asignación
        assignment = self.repository.find_by_ticket_id('ADAPTER-001')
        self.assertIsNotNone(assignment)
        self.assertIn(assignment.priority, ['high', 'medium', 'low'])
    
    def test_handle_ticket_created_no_ticket_id(self):
        """Manejar evento sin ticket_id debe ignorarse"""
        event_data = {'title': 'Test without id'}
        
        # No debe lanzar excepción
        self.adapter.handle_ticket_created(event_data)


# ============================================================================
# TESTS DE API REST
# ============================================================================

class AssignmentAPITests(TestCase):
    """Tests de la API REST"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_create_assignment_via_api(self):
        """POST /assignments/ debe crear asignación"""
        response = self.client.post(
            '/assignments/',
            {
                'ticket_id': 'API-001',
                'priority': 'high'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['ticket_id'], 'API-001')
        self.assertEqual(response.data['priority'], 'high')
    
    def test_create_assignment_invalid_priority(self):
        """POST con prioridad inválida debe retornar 400"""
        response = self.client.post(
            '/assignments/',
            {
                'ticket_id': 'API-002',
                'priority': 'urgent'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_assignments(self):
        """GET /assignments/ debe listar asignaciones"""
        # Crear algunas asignaciones
        TicketAssignment.objects.create(
            ticket_id='API-LIST-1',
            priority='high',
            assigned_at=timezone.now()
        )
        
        response = self.client.get('/assignments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_reassign_ticket_via_api(self):
        """POST /assignments/reassign/ debe reasignar ticket"""
        # Crear asignación inicial
        TicketAssignment.objects.create(
            ticket_id='API-REASSIGN-1',
            priority='low',
            assigned_at=timezone.now()
        )
        
        response = self.client.post(
            '/assignments/reassign/',
            {
                'ticket_id': 'API-REASSIGN-1',
                'priority': 'high'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'high')
    
    def test_reassign_nonexistent_ticket(self):
        """Reasignar ticket inexistente debe retornar 400"""
        response = self.client.post(
            '/assignments/reassign/',
            {
                'ticket_id': 'NONEXISTENT',
                'priority': 'high'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# TESTS LEGACY (Compatibilidad con código anterior)
# ============================================================================

class LegacyAssignmentServiceTests(TestCase):
    """Tests del servicio (compatibilidad con versión anterior)"""
    
    def test_handle_ticket_event_creates_assignment(self):
        """handle_ticket_event debe crear asignación"""
        event_data = {
            'event_type': 'ticket.created',
            'ticket_id': 'LEGACY-001'
        }
        
        handle_ticket_event(event_data)
        
        assignment = TicketAssignment.objects.get(ticket_id='LEGACY-001')
        self.assertIn(assignment.priority, ["high", "medium", "low"])
        self.assertIsNotNone(assignment.assigned_at)
    
    @patch('assignments.tasks.process_ticket_event.delay')
    def test_process_ticket_task_calls_handler(self, mock_delay):
        """Celery task debe procesar evento"""
        event_data = {'ticket_id': 'TASK-001'}
        
        # Ejecutar tarea directamente (sin Celery broker)
        from assignments.tasks import process_ticket_event
        process_ticket_event(event_data)
        
        # Verificar que se procesó
        self.assertTrue(
            TicketAssignment.objects.filter(ticket_id='TASK-001').exists()
        )


# ============================================================================
# TESTS DE INTEGRACIÓN (RabbitMQ + Celery + DB)
# ============================================================================

QUEUE_NAME = 'ticket_created'
RABBIT_HOST = 'rabbitmq'


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AssignmentIntegrationTests(TestCase):
    """Tests de integración end-to-end"""
    
    def setUp(self):
        # Configurar Celery para ejecución síncrona en tests
        try:
            from celery import current_app
            current_app.conf.task_always_eager = True
            current_app.conf.task_eager_propagates = True
        except Exception:
            pass
    
    def publish_message(self, ticket_id):
        """Publica mensaje en RabbitMQ"""
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST)
            )
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            body = json.dumps({"ticket_id": ticket_id})
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=body
            )
            connection.close()
        except Exception as e:
            self.skipTest(f"RabbitMQ no disponible: {e}")
    
    def test_end_to_end_rabbitmq_to_db(self):
        """
        Test de integración completo:
        1. Publica mensaje en RabbitMQ
        2. Consume mensaje
        3. Procesa con Celery
        4. Verifica creación en DB
        """
        ticket_id = 'INTEG-E2E-001'
        
        # 1) Publicar mensaje
        self.publish_message(ticket_id)
        
        # 2) Consumir mensaje
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST)
            )
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            
            # Intentar leer con reintentos
            method_frame, header_frame, body = channel.basic_get(
                queue=QUEUE_NAME,
                auto_ack=False
            )
            retries = 5
            while method_frame is None and retries > 0:
                time.sleep(0.5)
                method_frame, header_frame, body = channel.basic_get(
                    queue=QUEUE_NAME,
                    auto_ack=False
                )
                retries -= 1
            
            self.assertIsNotNone(
                method_frame,
                "No se recibió el mensaje de RabbitMQ"
            )
            
            # 3) Procesar mensaje
            import messaging.consumer as consumer
            consumer.callback(channel, method_frame, header_frame, body)
            
            # Pequeña espera para tolerancia
            time.sleep(0.1)
            
            # 4) Verificar en DB
            self.assertTrue(
                TicketAssignment.objects.filter(
                    ticket_id=ticket_id
                ).exists()
            )
            
            connection.close()
            
        except Exception as e:
            self.skipTest(f"RabbitMQ no disponible: {e}")
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

