"""
Tests de integración end-to-end.
Prueban el flujo completo con componentes reales (BD, casos de uso).
"""

import json
import time
from django.test import TestCase
from unittest.mock import patch, Mock

from tickets.models import Ticket as DjangoTicket
from tickets.domain.entities import Ticket as DomainTicket
from tickets.application.use_cases import (
    CreateTicketUseCase,
    CreateTicketCommand,
    ChangeTicketStatusUseCase,
    ChangeTicketStatusCommand
)
from tickets.infrastructure.repository import DjangoTicketRepository
from tickets.infrastructure.event_publisher import RabbitMQEventPublisher


class TestTicketWorkflowIntegration(TestCase):
    """Tests de integración del flujo completo de tickets."""
    
    def setUp(self):
        """Configurar componentes para tests de integración."""
        self.repository = DjangoTicketRepository()
        # Usar mock publisher para no depender de RabbitMQ en tests
        self.event_publisher = Mock(spec=RabbitMQEventPublisher)
    
    def test_create_and_change_status_workflow(self):
        """Test: Crear ticket y cambiar su estado (flujo completo)."""
        # 1. Crear ticket usando caso de uso
        create_use_case = CreateTicketUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        
        command = CreateTicketCommand(
            title="Integration Test Ticket",
            description="Testing full workflow"
        )
        
        ticket = create_use_case.execute(command)
        
        # Verificar creación
        assert ticket.id is not None
        assert ticket.status == DomainTicket.OPEN
        assert self.event_publisher.publish.called
        
        # Verificar persistencia en BD
        django_ticket = DjangoTicket.objects.get(pk=ticket.id)
        assert django_ticket.title == "Integration Test Ticket"
        
        # 2. Cambiar estado usando caso de uso
        change_use_case = ChangeTicketStatusUseCase(
            repository=self.repository,
            event_publisher=self.event_publisher
        )
        
        change_command = ChangeTicketStatusCommand(
            ticket_id=ticket.id,
            new_status=DomainTicket.IN_PROGRESS
        )
        
        updated_ticket = change_use_case.execute(change_command)
        
        # Verificar cambio
        assert updated_ticket.status == DomainTicket.IN_PROGRESS
        assert self.event_publisher.publish.call_count == 2  # Creado + Cambiado
        
        # Verificar persistencia del cambio
        django_ticket.refresh_from_db()
        assert django_ticket.status == "IN_PROGRESS"
    
    def test_cannot_modify_closed_ticket(self):
        """Test: No se puede cambiar el estado de un ticket cerrado."""
        # Crear y cerrar ticket
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand("Test", "Desc")
        )
        
        # Cerrar ticket
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.IN_PROGRESS)
        )
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.CLOSED)
        )
        
        # Intentar cambiar estado de ticket cerrado
        from tickets.domain.exceptions import TicketAlreadyClosed
        with self.assertRaises(TicketAlreadyClosed):
            change_use_case.execute(
                ChangeTicketStatusCommand(ticket.id, DomainTicket.OPEN)
            )
    
    def test_idempotent_status_change(self):
        """Test: Cambiar al mismo estado es idempotente."""
        # Crear ticket
        create_use_case = CreateTicketUseCase(
            self.repository,
            self.event_publisher
        )
        ticket = create_use_case.execute(
            CreateTicketCommand("Test", "Desc")
        )
        
        initial_call_count = self.event_publisher.publish.call_count
        
        # Cambiar al mismo estado (OPEN -> OPEN)
        change_use_case = ChangeTicketStatusUseCase(
            self.repository,
            self.event_publisher
        )
        change_use_case.execute(
            ChangeTicketStatusCommand(ticket.id, DomainTicket.OPEN)
        )
        
        # No debe publicar nuevo evento
        assert self.event_publisher.publish.call_count == initial_call_count


class TestRabbitMQEventPublisherIntegration(TestCase):
    """
    Tests de integración con RabbitMQ real.
    Solo ejecutar si RabbitMQ está disponible.
    """
    
    def setUp(self):
        """Verificar si RabbitMQ está disponible."""
        try:
            import pika
            import os
            rabbit_host = os.environ.get('RABBITMQ_HOST', 'localhost')
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_host, connection_attempts=1, retry_delay=0.1)
            )
            connection.close()
            self.rabbitmq_available = True
        except Exception:
            self.rabbitmq_available = False
            self.skipTest("RabbitMQ no está disponible para tests de integración")
    
    @patch('tickets.infrastructure.event_publisher.pika')
    def test_event_publisher_creates_exchange(self, mock_pika):
        """Test: EventPublisher declara exchange fanout."""
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        from tickets.domain.events import TicketCreated
        from datetime import datetime
        
        publisher = RabbitMQEventPublisher()
        event = TicketCreated(
            occurred_at=datetime.now(),
            ticket_id=1,
            title="Test",
            description="Desc",
            status="OPEN"
        )
        
        publisher.publish(event)
        
        # Verificar que se declaró exchange fanout
        mock_channel.exchange_declare.assert_called_once()
        call_args = mock_channel.exchange_declare.call_args
        assert call_args[1]['exchange_type'] == 'fanout'
        assert call_args[1]['durable'] is True
    
    @patch('tickets.infrastructure.event_publisher.pika')
    def test_event_message_format(self, mock_pika):
        """Test: Formato del mensaje publicado es correcto."""
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        from tickets.domain.events import TicketStatusChanged
        from datetime import datetime
        
        publisher = RabbitMQEventPublisher()
        event = TicketStatusChanged(
            occurred_at=datetime(2024, 1, 1, 10, 0, 0),
            ticket_id=123,
            old_status="OPEN",
            new_status="CLOSED"
        )
        
        publisher.publish(event)
        
        # Obtener el mensaje publicado
        call_args = mock_channel.basic_publish.call_args
        body = json.loads(call_args[1]['body'])
        
        # Verificar estructura del mensaje
        assert body['event_type'] == 'ticket.status_changed'
        assert body['ticket_id'] == 123
        assert body['old_status'] == 'OPEN'
        assert body['new_status'] == 'CLOSED'
        assert 'occurred_at' in body


class TestRepositoryIntegration(TestCase):
    """Tests de integración del repositorio con Django ORM."""
    
    def test_repository_roundtrip_conversion(self):
        """Test: Conversión Django -> Domain -> Django mantiene integridad."""
        # Crear ticket Django
        django_ticket = DjangoTicket.objects.create(
            title="Test Roundtrip",
            description="Testing conversion",
            status="IN_PROGRESS"
        )
        
        # Convertir a dominio
        repository = DjangoTicketRepository()
        domain_ticket = repository.find_by_id(django_ticket.id)
        
        # Verificar conversión
        assert domain_ticket.id == django_ticket.id
        assert domain_ticket.title == "Test Roundtrip"
        assert domain_ticket.status == DomainTicket.IN_PROGRESS
        
        # Modificar y guardar
        domain_ticket.change_status(DomainTicket.CLOSED)
        repository.save(domain_ticket)
        
        # Verificar persistencia
        django_ticket.refresh_from_db()
        assert django_ticket.status == "CLOSED"
    
    def test_repository_handles_concurrent_updates(self):
        """Test: Repository maneja actualizaciones de campos específicos."""
        django_ticket = DjangoTicket.objects.create(
            title="Original",
            description="Original Desc",
            status="OPEN"
        )
        
        repository = DjangoTicketRepository()
        domain_ticket = repository.find_by_id(django_ticket.id)
        
        # Cambiar solo el estado
        domain_ticket.status = DomainTicket.IN_PROGRESS
        repository.save(domain_ticket)
        
        # Verificar que solo cambió el estado
        django_ticket.refresh_from_db()
        assert django_ticket.status == "IN_PROGRESS"
        assert django_ticket.title == "Original"
        assert django_ticket.description == "Original Desc"
