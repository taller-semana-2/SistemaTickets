"""
Tests de la capa de presentación (ViewSet).
Prueban la integración HTTP con casos de uso.
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from unittest.mock import Mock, patch

from tickets.models import Ticket as DjangoTicket
from tickets.domain.entities import Ticket as DomainTicket
from tickets.domain.exceptions import TicketAlreadyClosed, InvalidTicketData
from tickets.views import TicketViewSet
from tickets.serializer import TicketSerializer
from datetime import datetime


class TestTicketViewSet(TestCase):
    """Tests del ViewSet con nueva arquitectura DDD."""
    
    def setUp(self):
        """Configurar para cada test."""
        self.factory = APIRequestFactory()
    
    def test_viewset_uses_create_use_case_on_create(self):
        """ViewSet ejecuta CreateTicketUseCase al crear ticket."""
        viewset = TicketViewSet()
        
        # Mockear el caso de uso
        mock_use_case = Mock()
        mock_domain_ticket = DomainTicket(
            id=123,
            title="Test",
            description="Desc",
            status=DomainTicket.OPEN,
            created_at=datetime.now()
        )
        mock_use_case.execute.return_value = mock_domain_ticket
        viewset.create_ticket_use_case = mock_use_case
        
        # Crear ticket Django para serializer
        DjangoTicket.objects.create(
            id=123,
            title="Test",
            description="Desc",
            status="OPEN"
        )
        
        # Simular perform_create
        serializer = TicketSerializer(data={"title": "Test", "description": "Desc"})
        serializer.is_valid()
        
        viewset.perform_create(serializer)
        
        # Verificar que se ejecutó el caso de uso
        mock_use_case.execute.assert_called_once()
    
    def test_viewset_handles_invalid_ticket_data_exception(self):
        """ViewSet maneja InvalidTicketData y devuelve error de validación."""
        viewset = TicketViewSet()
        
        # Mockear caso de uso para que lance excepción
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = InvalidTicketData("Título vacío")
        viewset.create_ticket_use_case = mock_use_case
        
        serializer = TicketSerializer(data={"title": "", "description": "Desc"})
        serializer.is_valid()
        
        # Debe lanzar ValidationError
        from rest_framework.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            viewset.perform_create(serializer)
    
    def test_change_status_endpoint_executes_use_case(self):
        """Endpoint change_status ejecuta ChangeTicketStatusUseCase."""
        # Crear ticket en BD
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="OPEN"
        )
        
        viewset = TicketViewSet()
        
        # Mockear caso de uso
        mock_use_case = Mock()
        mock_domain_ticket = DomainTicket(
            id=django_ticket.id,
            title="Test",
            description="Desc",
            status=DomainTicket.IN_PROGRESS,
            created_at=django_ticket.created_at
        )
        mock_use_case.execute.return_value = mock_domain_ticket
        viewset.change_status_use_case = mock_use_case
        
        # Crear request
        request = self.factory.patch('', {"status": "IN_PROGRESS"})
        
        # Ejecutar action
        response = viewset.change_status(request, pk=django_ticket.id)
        
        # Verificar que se ejecutó el caso de uso
        mock_use_case.execute.assert_called_once()
        assert response.status_code == status.HTTP_200_OK
    
    def test_change_status_handles_ticket_already_closed(self):
        """ViewSet maneja TicketAlreadyClosed y devuelve 400."""
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="CLOSED"
        )
        
        viewset = TicketViewSet()
        
        # Mockear caso de uso para que lance excepción
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = TicketAlreadyClosed(django_ticket.id)
        viewset.change_status_use_case = mock_use_case
        
        request = self.factory.patch('', {"status": "OPEN"})
        
        response = viewset.change_status(request, pk=django_ticket.id)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cerrado" in str(response.data['error']).lower()
    
    def test_change_status_requires_status_field(self):
        """Endpoint change_status requiere el campo 'status'."""
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="OPEN"
        )
        
        viewset = TicketViewSet()
        request = self.factory.patch('', {})  # Sin status
        
        response = viewset.change_status(request, pk=django_ticket.id)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "requerido" in str(response.data['error']).lower()
    
    def test_change_status_handles_invalid_status(self):
        """ViewSet maneja estado inválido y devuelve 400."""
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="OPEN"
        )
        
        viewset = TicketViewSet()
        
        # Mockear caso de uso para que lance ValueError
        mock_use_case = Mock()
        mock_use_case.execute.side_effect = ValueError("Estado inválido")
        viewset.change_status_use_case = mock_use_case
        
        request = self.factory.patch('', {"status": "INVALID"})
        
        response = viewset.change_status(request, pk=django_ticket.id)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTicketSerializer(TestCase):
    """Tests del serializer (sin cambios desde refactor)."""
    
    def test_serializer_accepts_valid_data(self):
        """Serializer acepta datos válidos."""
        data = {"title": "Test", "description": "Description"}
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid()
    
    def test_serializer_rejects_missing_title(self):
        """Serializer rechaza datos sin título."""
        data = {"description": "Description"}
        serializer = TicketSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'title' in serializer.errors
    
    def test_serializer_rejects_missing_description(self):
        """Serializer rechaza datos sin descripción."""
        data = {"title": "Test"}
        serializer = TicketSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'description' in serializer.errors
    
    def test_serializer_rejects_title_too_long(self):
        """Serializer rechaza título demasiado largo."""
        data = {"title": "x" * 300, "description": "Desc"}
        serializer = TicketSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'title' in serializer.errors


class TestTicketModel(TestCase):
    """Tests del modelo Django (persistencia)."""
    
    def test_ticket_model_creation_defaults_to_open(self):
        """Crear ticket sin status explícito usa OPEN por defecto."""
        ticket = DjangoTicket.objects.create(
            title="Test",
            description="Description"
        )
        
        assert ticket.status == "OPEN"
        assert ticket.created_at is not None
    
    def test_ticket_model_can_be_updated(self):
        """Modelo Django permite actualizaciones."""
        ticket = DjangoTicket.objects.create(
            title="Original",
            description="Original Desc",
            status="OPEN"
        )
        
        ticket.status = "IN_PROGRESS"
        ticket.save()
        
        ticket.refresh_from_db()
        assert ticket.status == "IN_PROGRESS"
