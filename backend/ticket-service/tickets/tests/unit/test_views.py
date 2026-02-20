"""
Tests de la capa de presentación (ViewSet).
Prueban la integración HTTP con casos de uso.
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework import status
from unittest.mock import Mock, patch

from tickets.models import Ticket as DjangoTicket
from tickets.domain.entities import Ticket as DomainTicket
from tickets.domain.exceptions import TicketAlreadyClosed, InvalidTicketData, InvalidPriorityTransition, DomainException
from tickets.views import TicketViewSet
from tickets.serializer import TicketSerializer
from datetime import datetime


class TestTicketViewSet(TestCase):
    """Tests del ViewSet con nueva arquitectura DDD."""
    
    def setUp(self):
        """Configurar para cada test."""
        self.factory = APIRequestFactory()

    def _make_drf_request(self, wsgi_request):
        """Envuelve un WSGIRequest en un DRF Request para llamadas directas a métodos del ViewSet."""
        return Request(wsgi_request, parsers=[JSONParser(), FormParser(), MultiPartParser()])
    
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

    # ── Phase 5: change_priority endpoint tests (RED) ──────────────────

    def test_change_priority_endpoint_executes_use_case(self):
        """Endpoint change_priority ejecuta ChangePriorityUseCase."""
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="OPEN"
        )

        viewset = TicketViewSet()

        mock_use_case = Mock()
        mock_domain_ticket = DomainTicket(
            id=django_ticket.id,
            title="Test",
            description="Desc",
            status=DomainTicket.OPEN,
            user_id="1",
            created_at=django_ticket.created_at,
            priority="High"
        )
        mock_use_case.execute.return_value = mock_domain_ticket
        viewset.change_priority_use_case = mock_use_case

        request = self._make_drf_request(self.factory.patch('', {"priority": "High", "user_role": "Administrador"}))

        response = viewset.change_priority(request, pk=django_ticket.id)

        mock_use_case.execute.assert_called_once()
        assert response.status_code == status.HTTP_200_OK

    def test_change_priority_requires_priority_field(self):
        """Endpoint change_priority requiere el campo 'priority'."""
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="OPEN"
        )

        viewset = TicketViewSet()

        request = self._make_drf_request(self.factory.patch('', {}))

        response = viewset.change_priority(request, pk=django_ticket.id)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "requerido" in str(response.data['error']).lower()

    def test_change_priority_handles_ticket_already_closed(self):
        """ViewSet maneja TicketAlreadyClosed en change_priority y devuelve 400."""
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="CLOSED"
        )

        viewset = TicketViewSet()

        mock_use_case = Mock()
        mock_use_case.execute.side_effect = TicketAlreadyClosed(django_ticket.id)
        viewset.change_priority_use_case = mock_use_case

        request = self._make_drf_request(self.factory.patch('', {"priority": "High", "user_role": "Administrador"}))

        response = viewset.change_priority(request, pk=django_ticket.id)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cerrado" in str(response.data['error']).lower()

    def test_change_priority_handles_invalid_priority_transition(self):
        """ViewSet maneja InvalidPriorityTransition y devuelve 400."""
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="OPEN"
        )

        viewset = TicketViewSet()

        mock_use_case = Mock()
        mock_use_case.execute.side_effect = InvalidPriorityTransition(
            "High", "Unassigned", "no se puede volver"
        )
        viewset.change_priority_use_case = mock_use_case

        request = self._make_drf_request(self.factory.patch('', {"priority": "Unassigned", "user_role": "Administrador"}))

        response = viewset.change_priority(request, pk=django_ticket.id)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_priority_handles_permission_denied(self):
        """ViewSet maneja DomainException de permiso y devuelve 403."""
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="OPEN"
        )

        viewset = TicketViewSet()

        mock_use_case = Mock()
        mock_use_case.execute.side_effect = DomainException("Permiso insuficiente")
        viewset.change_priority_use_case = mock_use_case

        request = self._make_drf_request(self.factory.patch('', {"priority": "High", "user_role": "Usuario"}))

        response = viewset.change_priority(request, pk=django_ticket.id)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_change_priority_passes_justification_to_use_case(self):
        """Endpoint change_priority pasa justificación al caso de uso."""
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="OPEN"
        )

        viewset = TicketViewSet()

        mock_use_case = Mock()
        mock_domain_ticket = DomainTicket(
            id=django_ticket.id,
            title="Test",
            description="Desc",
            status=DomainTicket.OPEN,
            user_id="1",
            created_at=django_ticket.created_at,
            priority="High",
            priority_justification="Urgente"
        )
        mock_use_case.execute.return_value = mock_domain_ticket
        viewset.change_priority_use_case = mock_use_case

        request = self._make_drf_request(self.factory.patch('', {
            "priority": "High",
            "justification": "Urgente",
            "user_role": "Administrador"
        }))

        response = viewset.change_priority(request, pk=django_ticket.id)

        mock_use_case.execute.assert_called_once()
        call_args = mock_use_case.execute.call_args
        command = call_args[0][0] if call_args[0] else call_args[1].get('command')
        assert command.justification == "Urgente"

    def test_change_priority_returns_updated_priority_in_response(self):
        """Endpoint change_priority devuelve prioridad actualizada en respuesta."""
        django_ticket = DjangoTicket.objects.create(
            title="Test",
            description="Desc",
            status="OPEN"
        )

        viewset = TicketViewSet()

        mock_use_case = Mock()
        mock_domain_ticket = DomainTicket(
            id=django_ticket.id,
            title="Test",
            description="Desc",
            status=DomainTicket.OPEN,
            user_id="1",
            created_at=django_ticket.created_at,
            priority="High",
            priority_justification="Urgente"
        )
        mock_use_case.execute.return_value = mock_domain_ticket
        viewset.change_priority_use_case = mock_use_case

        request = self._make_drf_request(self.factory.patch('', {"priority": "High", "user_role": "Administrador"}))

        response = viewset.change_priority(request, pk=django_ticket.id)

        assert response.data['priority'] == "High"
        assert response.data.get('priority_justification') == "Urgente"


class TestTicketSerializer(TestCase):
    """Tests del TicketSerializer: validación de campos requeridos e integración de priority."""
    
    def test_serializer_accepts_valid_data(self):
        """Serializer acepta datos válidos."""
        data = {"title": "Test", "description": "Description", "user_id": "1"}
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

    def test_serializer_includes_priority_in_response(self):
        """RED-4.1: Al serializar un ticket con priority, el campo aparece en los datos de salida."""
        ticket = DjangoTicket.objects.create(
            title="Test Priority",
            description="Descripción",
            priority="High",
        )
        serializer = TicketSerializer(instance=ticket)
        assert "priority" in serializer.data
        assert serializer.data["priority"] == "High"

    def test_serializer_includes_priority_justification_in_response(self):
        """RED-4.2: Al serializar un ticket con justificación, el campo aparece en la salida."""
        ticket = DjangoTicket.objects.create(
            title="Test Justification",
            description="Descripción",
            priority="High",
            priority_justification="Urgente",
        )
        serializer = TicketSerializer(instance=ticket)
        assert "priority_justification" in serializer.data
        assert serializer.data["priority_justification"] == "Urgente"

    def test_serializer_ignores_priority_on_creation(self):
        """RED-4.3: Al crear ticket vía POST, el campo priority en el body es ignorado."""
        data = {"title": "Test", "description": "Descripción", "priority": "High", "user_id": "1"}
        serializer = TicketSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert "priority" not in serializer.validated_data

    def test_serializer_ignores_priority_justification_on_creation(self):
        """RED-4.4: Al crear ticket vía POST, el campo priority_justification en el body es ignorado."""
        data = {"title": "Test", "description": "Descripción", "priority_justification": "Reason", "user_id": "1"}
        serializer = TicketSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert "priority_justification" not in serializer.validated_data


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
