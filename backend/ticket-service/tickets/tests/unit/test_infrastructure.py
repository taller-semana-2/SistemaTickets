"""
Tests de la capa de infraestructura (adaptadores).
Prueban Repository y EventPublisher con Django.
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

from django.test import TestCase

from tickets.models import Ticket as DjangoTicket
from tickets.domain.entities import Ticket as DomainTicket
from tickets.domain.events import TicketCreated, TicketStatusChanged, TicketPriorityChanged
from tickets.infrastructure.repository import DjangoTicketRepository
from tickets.infrastructure.event_publisher import RabbitMQEventPublisher


class TestDjangoTicketRepository(TestCase):
    """Tests del repositorio Django."""
    
    def setUp(self):
        """Configurar repositorio para cada test."""
        self.repository = DjangoTicketRepository()
    
    def test_save_new_ticket_assigns_id(self):
        """Guardar nuevo ticket asigna ID automáticamente."""
        domain_ticket = DomainTicket(
            id=None,  # Sin ID
            title="Test Ticket",
            description="Test Description",
            status=DomainTicket.OPEN,
            created_at=datetime.now()
        )
        
        saved_ticket = self.repository.save(domain_ticket)
        
        # Debe tener ID asignado
        assert saved_ticket.id is not None
        assert saved_ticket.id > 0
        
        # Verificar que existe en BD
        assert DjangoTicket.objects.filter(pk=saved_ticket.id).exists()
    
    def test_save_existing_ticket_updates(self):
        """Guardar ticket existente actualiza sus datos."""
        # Crear ticket en BD
        django_ticket = DjangoTicket.objects.create(
            title="Original",
            description="Original Description",
            status="OPEN"
        )
        
        # Crear entidad de dominio y modificarla
        domain_ticket = DomainTicket(
            id=django_ticket.id,
            title="Updated",
            description="Updated Description",
            status=DomainTicket.IN_PROGRESS,
            created_at=django_ticket.created_at
        )
        
        # Guardar cambios
        saved_ticket = self.repository.save(domain_ticket)
        
        # Verificar que se actualizó
        django_ticket.refresh_from_db()
        assert django_ticket.title == "Updated"
        assert django_ticket.description == "Updated Description"
        assert django_ticket.status == "IN_PROGRESS"
    
    def test_find_by_id_returns_domain_ticket(self):
        """find_by_id devuelve entidad de dominio."""
        # Crear ticket en BD
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="OPEN"
        )
        
        # Buscar por ID
        domain_ticket = self.repository.find_by_id(django_ticket.id)
        
        # Verificar conversión a dominio
        assert domain_ticket is not None
        assert isinstance(domain_ticket, DomainTicket)
        assert domain_ticket.id == django_ticket.id
        assert domain_ticket.title == "Test"
        assert domain_ticket.status == DomainTicket.OPEN
    
    def test_find_by_id_returns_none_if_not_exists(self):
        """find_by_id devuelve None si no existe."""
        domain_ticket = self.repository.find_by_id(999999)
        assert domain_ticket is None
    
    def test_find_all_returns_list_of_domain_tickets(self):
        """find_all devuelve lista de entidades de dominio."""
        # Crear varios tickets
        DjangoTicket.objects.create(title="T1", description="D1", status="OPEN")
        DjangoTicket.objects.create(title="T2", description="D2", status="IN_PROGRESS")
        DjangoTicket.objects.create(title="T3", description="D3", status="CLOSED")
        
        # Obtener todos
        tickets = self.repository.find_all()
        
        # Verificar
        assert len(tickets) >= 3
        assert all(isinstance(t, DomainTicket) for t in tickets)
        
        # Verificar ordenamiento (más reciente primero)
        titles = [t.title for t in tickets]
        assert "T3" in titles[0:3]  # Más reciente entre los primeros
    
    def test_delete_removes_ticket(self):
        """delete elimina el ticket de la BD."""
        django_ticket = DjangoTicket.objects.create(
            title="To Delete",
            description="Will be deleted",
            status="OPEN"
        )
        ticket_id = django_ticket.id
        
        # Eliminar
        self.repository.delete(ticket_id)
        
        # Verificar que no existe
        assert not DjangoTicket.objects.filter(pk=ticket_id).exists()
    
    def test_delete_nonexistent_ticket_does_not_raise(self):
        """delete no falla si el ticket no existe."""
        # No debe lanzar excepción
        self.repository.delete(999999)


class TestRabbitMQEventPublisher(TestCase):
    """Tests del publicador de eventos RabbitMQ."""
    
    @patch('tickets.infrastructure.event_publisher.pika')
    def test_publish_ticket_created_event(self, mock_pika):
        """Publicar evento TicketCreated envía mensaje a RabbitMQ."""
        # Configurar mocks
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        # Crear publisher y evento
        publisher = RabbitMQEventPublisher()
        event = TicketCreated(
            occurred_at=datetime(2024, 1, 1, 10, 0, 0),
            ticket_id=123,
            title="Test",
            description="Desc",
            status="OPEN"
        )
        
        # Publicar
        publisher.publish(event)
        
        # Verificar que se declaró el exchange
        mock_channel.exchange_declare.assert_called_once()
        
        # Verificar que se publicó el mensaje
        mock_channel.basic_publish.assert_called_once()
        call_kwargs = mock_channel.basic_publish.call_args[1]
        
        assert 'exchange' in call_kwargs
        assert 'body' in call_kwargs
        
        # Verificar contenido del mensaje
        body = json.loads(call_kwargs['body'])
        assert body['event_type'] == 'ticket.created'
        assert body['ticket_id'] == 123
        assert body['title'] == "Test"
    
    @patch('tickets.infrastructure.event_publisher.pika')
    def test_publish_ticket_status_changed_event(self, mock_pika):
        """Publicar evento TicketStatusChanged envía mensaje correcto."""
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        publisher = RabbitMQEventPublisher()
        event = TicketStatusChanged(
            occurred_at=datetime(2024, 1, 1, 10, 0, 0),
            ticket_id=456,
            old_status="OPEN",
            new_status="IN_PROGRESS"
        )
        
        publisher.publish(event)
        
        # Verificar mensaje
        call_kwargs = mock_channel.basic_publish.call_args[1]
        body = json.loads(call_kwargs['body'])
        
        assert body['event_type'] == 'ticket.status_changed'
        assert body['ticket_id'] == 456
        assert body['old_status'] == 'OPEN'
        assert body['new_status'] == 'IN_PROGRESS'
    
    @patch('tickets.infrastructure.event_publisher.pika')
    def test_publish_closes_connection(self, mock_pika):
        """Publicar evento cierra la conexión después."""
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        
        publisher = RabbitMQEventPublisher()
        event = TicketCreated(
            occurred_at=datetime.now(),
            ticket_id=1,
            title="T",
            description="D",
            status="OPEN"
        )
        
        publisher.publish(event)
        
        # Verificar que cerró la conexión
        mock_connection.close.assert_called_once()
    
    @patch('tickets.infrastructure.event_publisher.pika')
    def test_publish_propagates_connection_errors(self, mock_pika):
        """Errores de conexión se propagan correctamente."""
        mock_pika.BlockingConnection.side_effect = Exception("Connection failed")
        
        publisher = RabbitMQEventPublisher()
        event = TicketCreated(
            occurred_at=datetime.now(),
            ticket_id=1,
            title="T",
            description="D",
            status="OPEN"
        )
        
        # Debe propagar la excepción
        with self.assertRaises(Exception) as context:
            publisher.publish(event)
        
        assert "Connection failed" in str(context.exception)

    @patch('tickets.infrastructure.event_publisher.pika')
    def test_publish_ticket_priority_changed_event(self, mock_pika):
        """Publicar evento TicketPriorityChanged envía mensaje correcto."""
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        publisher = RabbitMQEventPublisher()
        event = TicketPriorityChanged(
            occurred_at=datetime(2026, 2, 19, 14, 30, 0),
            ticket_id=42,
            old_priority="Unassigned",
            new_priority="High",
            justification="Urgente"
        )

        publisher.publish(event)

        call_kwargs = mock_channel.basic_publish.call_args[1]
        body = json.loads(call_kwargs['body'])

        assert body['event_type'] == 'ticket.priority_changed'
        assert body['ticket_id'] == 42
        assert body['old_priority'] == 'Unassigned'
        assert body['new_priority'] == 'High'
        assert body['justification'] == 'Urgente'
        assert 'occurred_at' in body

    @patch('tickets.infrastructure.event_publisher.pika')
    def test_publish_ticket_priority_changed_event_without_justification(self, mock_pika):
        """Publicar evento TicketPriorityChanged sin justificación envía None."""
        mock_connection = Mock()
        mock_channel = Mock()
        mock_pika.BlockingConnection.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel

        publisher = RabbitMQEventPublisher()
        event = TicketPriorityChanged(
            occurred_at=datetime(2026, 2, 19, 14, 30, 0),
            ticket_id=99,
            old_priority="Low",
            new_priority="Medium",
            justification=None
        )

        publisher.publish(event)

        call_kwargs = mock_channel.basic_publish.call_args[1]
        body = json.loads(call_kwargs['body'])

        assert body['event_type'] == 'ticket.priority_changed'
        assert body['ticket_id'] == 99
        assert body['old_priority'] == 'Low'
        assert body['new_priority'] == 'Medium'
        assert body['justification'] is None
        assert 'occurred_at' in body


class TestTicketModel(TestCase):
    """Tests del modelo Django Ticket — campos de prioridad (Phase 1)."""

    def setUp(self):
        """Crear ticket base reutilizable para cada test."""
        self.ticket = DjangoTicket.objects.create(
            title="Test",
            description="Description",
        )

    def test_ticket_model_creation_defaults_priority_to_unassigned(self):
        """Crear ticket sin prioridad explícita debe asignar 'Unassigned' por defecto."""
        assert self.ticket.priority == "Unassigned"

    def test_ticket_model_creation_defaults_priority_justification_to_none(self):
        """Crear ticket sin justificación debe dejar priority_justification en None."""
        assert self.ticket.priority_justification is None

    def test_ticket_model_accepts_valid_priority_values(self):
        """El modelo acepta los valores de prioridad válidos: Low, Medium, High."""
        valid_priorities = ["Low", "Medium", "High"]
        for value in valid_priorities:
            ticket = DjangoTicket.objects.create(
                title=f"Test {value}",
                description="Description",
                priority=value,
            )
            ticket.refresh_from_db()
            assert ticket.priority == value, (
                f"Se esperaba priority='{value}', se obtuvo '{ticket.priority}'"
            )

    def test_ticket_model_can_update_priority_and_justification(self):
        """Un ticket existente puede actualizar priority y priority_justification."""
        self.ticket.priority = "High"
        self.ticket.priority_justification = "Urgente"
        self.ticket.save()

        updated_ticket = DjangoTicket.objects.get(pk=self.ticket.id)
        assert updated_ticket.priority == "High"
        assert updated_ticket.priority_justification == "Urgente"
