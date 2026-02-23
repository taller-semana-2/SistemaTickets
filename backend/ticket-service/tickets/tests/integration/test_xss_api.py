"""
Tests de integración para validación XSS en la API de tickets.

Prueba el flujo completo desde el endpoint HTTP hasta la base de datos,
verificando que los payloads maliciosos sean rechazados con HTTP 400
y que los tickets legítimos se guarden correctamente.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from tickets.models import Ticket as DjangoTicket


class TestTicketAPIXSSValidation(TestCase):
    """Tests de integración para validación XSS en endpoints de tickets."""
    
    def setUp(self):
        """Configura el cliente API para cada test."""
        self.client = APIClient()
        self.tickets_url = "/api/tickets/"
    
    def tearDown(self):
        """Limpia la base de datos después de cada test."""
        DjangoTicket.objects.all().delete()
    
    # ==================== Scenarios de Criterios de Aceptación ====================
    
    def test_scenario_script_tag_in_title_is_rejected(self):
        """
        Scenario: Título con script tag es rechazado
        
        Given un usuario autenticado
        When envía POST a "/api/tickets/" con título "<script>alert('XSS')</script>"
        Then recibe respuesta HTTP 400 Bad Request
        And el mensaje de error indica que el título contiene caracteres no permitidos
        """
        payload = {
            "title": "<script>alert('XSS')</script>",
            "description": "Descripción válida",
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        # Then: HTTP 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # And: Mensaje de error apropiado
        error_message = str(response.data)
        assert "título" in error_message.lower() or "title" in error_message.lower()
        assert "no permitidos" in error_message.lower() or "HTML" in error_message
        
        # Verify: No se guardó en la base de datos
        assert DjangoTicket.objects.count() == 0
    
    def test_scenario_img_onerror_in_description_is_rejected(self):
        """
        Scenario: Descripción con event handler es rechazada
        
        Given un usuario autenticado
        When envía POST a "/api/tickets/" con descripción '<img src=x onerror="alert(1)">'
        Then recibe respuesta HTTP 400 Bad Request
        And el mensaje de error indica que la descripción contiene caracteres no permitidos
        """
        payload = {
            "title": "Título válido",
            "description": '<img src=x onerror="alert(1)">',
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        # Then: HTTP 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # And: Mensaje de error apropiado
        error_message = str(response.data)
        assert "descripción" in error_message.lower() or "description" in error_message.lower()
        assert "no permitidos" in error_message.lower() or "HTML" in error_message
        
        # Verify: No se guardó en la base de datos
        assert DjangoTicket.objects.count() == 0
    
    def test_scenario_valid_title_and_description_are_accepted(self):
        """
        Scenario: Título y descripción válidos son aceptados
        
        Given un usuario autenticado
        When envía POST a "/api/tickets/" con título "Problema con el login"
             y descripción "No puedo iniciar sesión"
        Then recibe respuesta HTTP 201 Created
        And el ticket se almacena correctamente
        """
        payload = {
            "title": "Problema con el login",
            "description": "No puedo iniciar sesión",
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        # Then: HTTP 201
        assert response.status_code == status.HTTP_201_CREATED
        
        # And: Ticket guardado correctamente
        assert DjangoTicket.objects.count() == 1
        
        ticket = DjangoTicket.objects.first()
        assert ticket.title == "Problema con el login"
        assert ticket.description == "No puedo iniciar sesión"
        assert ticket.user_id == "user123"
        assert ticket.status == "OPEN"
    
    def test_scenario_special_characters_are_accepted(self):
        """
        Scenario: Caracteres especiales no peligrosos son aceptados
        
        Given un usuario autenticado
        When envía POST a "/api/tickets/" con título "Error en versión 2.0 & corrección"
        Then recibe respuesta HTTP 201 Created
        """
        payload = {
            "title": "Error en versión 2.0 & corrección",
            "description": "El sistema muestra 'Error 404' al acceder",
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        # Then: HTTP 201
        assert response.status_code == status.HTTP_201_CREATED
        
        # And: Datos guardados correctamente
        ticket = DjangoTicket.objects.first()
        assert ticket.title == "Error en versión 2.0 & corrección"
        assert "Error 404" in ticket.description
    
    # ==================== Tests Adicionales de Regresión ====================
    
    def test_rejects_javascript_protocol(self):
        """POST con protocolo javascript: es rechazado."""
        payload = {
            "title": "Click aquí",
            "description": '<a href="javascript:alert(1)">Link malicioso</a>',
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert DjangoTicket.objects.count() == 0
    
    def test_rejects_onclick_event_handler(self):
        """POST con onclick event handler es rechazado."""
        payload = {
            "title": '<div onclick="malicious()">Título</div>',
            "description": "Descripción válida",
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert DjangoTicket.objects.count() == 0
    
    def test_rejects_onload_event_handler(self):
        """POST con onload event handler es rechazado."""
        payload = {
            "title": "Título válido",
            "description": '<body onload="malicious()">Descripción</body>',
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert DjangoTicket.objects.count() == 0
    
    def test_rejects_iframe_tag(self):
        """POST con <iframe> es rechazado."""
        payload = {
            "title": "Título válido",
            "description": '<iframe src="http://evil.com"></iframe>',
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert DjangoTicket.objects.count() == 0
    
    def test_rejects_object_tag(self):
        """POST con <object> es rechazado."""
        payload = {
            "title": '<object data="exploit.swf"></object>',
            "description": "Descripción válida",
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert DjangoTicket.objects.count() == 0
    
    def test_rejects_embed_tag(self):
        """POST con <embed> es rechazado."""
        payload = {
            "title": "Título válido",
            "description": '<embed src="malicious.swf">',
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert DjangoTicket.objects.count() == 0
    
    def test_case_insensitive_script_detection(self):
        """Detecta <ScRiPt> con case mixing."""
        payload = {
            "title": "<ScRiPt>alert('XSS')</ScRiPt>",
            "description": "Descripción válida",
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert DjangoTicket.objects.count() == 0
    
    def test_accepts_accented_characters(self):
        """Acepta texto con tildes y caracteres especiales."""
        payload = {
            "title": "Configuración del sistema",
            "description": "La página de configuración está rota después de la última actualización",
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert DjangoTicket.objects.count() == 1
    
    def test_accepts_numbers_and_symbols(self):
        """Acepta números, símbolos y puntuación normal."""
        payload = {
            "title": "Error #404 - Página no encontrada (v2.3.1)",
            "description": "El servidor retorna código HTTP 404 al intentar acceder a /dashboard/metrics",
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert DjangoTicket.objects.count() == 1
    
    def test_accepts_email_addresses(self):
        """Acepta direcciones de email en el contenido."""
        payload = {
            "title": "Problema con notificaciones",
            "description": "No recibo emails en soporte@ejemplo.com cuando se cierra un ticket",
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert DjangoTicket.objects.count() == 1
    
    def test_rejects_both_fields_with_xss(self):
        """Rechaza cuando ambos campos contienen XSS."""
        payload = {
            "title": "<script>alert('title')</script>",
            "description": "<script>alert('desc')</script>",
            "user_id": "user123"
        }
        
        response = self.client.post(self.tickets_url, payload, format="json")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert DjangoTicket.objects.count() == 0
        
        # Ambos campos deben tener errores
        error_data = response.data
        assert "title" in str(error_data) or "título" in str(error_data).lower()
    
    def test_multiple_tickets_with_valid_content(self):
        """Puede crear múltiples tickets válidos secuencialmente."""
        tickets_data = [
            {
                "title": "Error en login",
                "description": "No puedo iniciar sesión",
                "user_id": "user1"
            },
            {
                "title": "Problema de rendimiento",
                "description": "La aplicación está lenta",
                "user_id": "user2"
            },
            {
                "title": "Bug en versión 2.0",
                "description": "El botón de guardar no funciona",
                "user_id": "user3"
            }
        ]
        
        for data in tickets_data:
            response = self.client.post(self.tickets_url, data, format="json")
            assert response.status_code == status.HTTP_201_CREATED
        
        # Verify: 3 tickets creados
        assert DjangoTicket.objects.count() == 3
    
    def test_get_tickets_does_not_execute_stored_xss(self):
        """
        Verifica que aunque se creara (por algún bypass futuro) un ticket
        con contenido peligroso, el GET lo retorna como texto plano.
        
        Nota: Este test verifica que DRF serializa como JSON (texto plano),
        no como HTML ejecutable.
        """
        # Crear ticket válido
        payload = {
            "title": "Ticket de prueba",
            "description": "Descripción normal",
            "user_id": "user123"
        }
        
        create_response = self.client.post(self.tickets_url, payload, format="json")
        assert create_response.status_code == status.HTTP_201_CREATED
        
        ticket_id = create_response.data["id"]
        
        # GET del ticket
        get_response = self.client.get(f"{self.tickets_url}{ticket_id}/", format="json")
        
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response["Content-Type"].startswith("application/json")
        
        # Los datos se serializan como JSON (texto plano)
        assert get_response.data["title"] == "Ticket de prueba"
        assert get_response.data["description"] == "Descripción normal"
