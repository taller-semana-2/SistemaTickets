"""
Tests unitarios para validación XSS en la capa de dominio.

Verifica que la función _contains_dangerous_html detecta correctamente
patrones peligrosos y que el TicketFactory rechaza inputs maliciosos.
"""

import pytest

from tickets.domain.factories import TicketFactory, _contains_dangerous_html
from tickets.domain.exceptions import DangerousInputError, InvalidTicketData


class TestDangerousHtmlDetection:
    """Tests de la función de detección de HTML peligroso."""
    
    def test_detects_script_tag_lowercase(self):
        """Detecta tags <script> en minúsculas."""
        assert _contains_dangerous_html("<script>alert('XSS')</script>") is True
    
    def test_detects_script_tag_uppercase(self):
        """Detecta tags <SCRIPT> en mayúsculas (bypass común)."""
        assert _contains_dangerous_html("<SCRIPT>alert('XSS')</SCRIPT>") is True
    
    def test_detects_script_tag_mixed_case(self):
        """Detecta tags <ScRiPt> con case mixing (bypass común)."""
        assert _contains_dangerous_html("<ScRiPt>alert('XSS')</ScRiPt>") is True
    
    def test_detects_img_with_onerror(self):
        """Detecta <img> con atributo onerror."""
        assert _contains_dangerous_html('<img src=x onerror="alert(1)">') is True
    
    def test_detects_onerror_with_spaces(self):
        """Detecta onerror con espacios adicionales."""
        assert _contains_dangerous_html('<img src=x  onerror = "alert(1)">') is True
    
    def test_detects_onclick_event_handler(self):
        """Detecta otros event handlers como onclick."""
        assert _contains_dangerous_html('<div onclick="malicious()">Click</div>') is True
    
    def test_detects_onload_event_handler(self):
        """Detecta event handler onload."""
        assert _contains_dangerous_html('<body onload="malicious()">') is True
    
    def test_detects_javascript_protocol(self):
        """Detecta protocolo javascript:."""
        assert _contains_dangerous_html('<a href="javascript:alert(1)">link</a>') is True
    
    def test_detects_iframe_tag(self):
        """Detecta tags <iframe> peligrosos."""
        assert _contains_dangerous_html('<iframe src="http://evil.com"></iframe>') is True
    
    def test_detects_object_tag(self):
        """Detecta tags <object> peligrosos."""
        assert _contains_dangerous_html('<object data="exploit.swf"></object>') is True
    
    def test_detects_embed_tag(self):
        """Detecta tags <embed> peligrosos."""
        assert _contains_dangerous_html('<embed src="exploit.swf">') is True
    
    def test_accepts_plain_text(self):
        """Acepta texto plano sin HTML."""
        assert _contains_dangerous_html("Problema con el login") is False
    
    def test_accepts_text_with_ampersand(self):
        """Acepta caracteres especiales seguros como &."""
        assert _contains_dangerous_html("Error en versión 2.0 & corrección") is False
    
    def test_accepts_text_with_accents(self):
        """Acepta texto con tildes y caracteres especiales."""
        assert _contains_dangerous_html("No puedo iniciar sesión con mi contraseña") is False
    
    def test_accepts_text_with_numbers(self):
        """Acepta texto con números y símbolos comunes."""
        assert _contains_dangerous_html("Error #404 - Página no encontrada (v2.3.1)") is False
    
    def test_accepts_text_with_quotes(self):
        """Acepta texto con comillas normales (no en contexto HTML)."""
        assert _contains_dangerous_html('El sistema dice "Error de conexión"') is False
    
    def test_accepts_email_addresses(self):
        """Acepta direcciones de email."""
        assert _contains_dangerous_html("Contactar a soporte@ejemplo.com para ayuda") is False


class TestTicketFactoryXSSValidation:
    """Tests de validación XSS en TicketFactory."""
    
    def test_rejects_script_tag_in_title(self):
        """Rechaza <script> en el título."""
        with pytest.raises(DangerousInputError) as exc_info:
            TicketFactory.create(
                title="<script>alert('XSS')</script>",
                description="Descripción válida",
                user_id="user123"
            )
        
        assert exc_info.value.field == "título"
        assert "título" in str(exc_info.value)
        assert "caracteres HTML o scripts no permitidos" in str(exc_info.value)
    
    def test_rejects_img_onerror_in_description(self):
        """Rechaza <img onerror> en la descripción."""
        with pytest.raises(DangerousInputError) as exc_info:
            TicketFactory.create(
                title="Título válido",
                description='<img src=x onerror="alert(1)">',
                user_id="user123"
            )
        
        assert exc_info.value.field == "descripción"
        assert "descripción" in str(exc_info.value)
    
    def test_rejects_javascript_protocol_in_title(self):
        """Rechaza protocolo javascript: en título."""
        with pytest.raises(DangerousInputError):
            TicketFactory.create(
                title='<a href="javascript:alert(1)">Click</a>',
                description="Descripción válida",
                user_id="user123"
            )
    
    def test_rejects_onclick_in_description(self):
        """Rechaza event handler onclick en descripción."""
        with pytest.raises(DangerousInputError):
            TicketFactory.create(
                title="Título válido",
                description='<div onclick="malicious()">Hacer click</div>',
                user_id="user123"
            )
    
    def test_rejects_iframe_in_title(self):
        """Rechaza <iframe> en título."""
        with pytest.raises(DangerousInputError):
            TicketFactory.create(
                title='<iframe src="http://evil.com"></iframe>',
                description="Descripción válida",
                user_id="user123"
            )
    
    def test_accepts_valid_title_and_description(self):
        """Acepta título y descripción válidos."""
        ticket = TicketFactory.create(
            title="Problema con el login",
            description="No puedo iniciar sesión en el sistema",
            user_id="user123"
        )
        
        assert ticket.title == "Problema con el login"
        assert ticket.description == "No puedo iniciar sesión en el sistema"
        assert ticket.user_id == "user123"
        assert ticket.status == "OPEN"
    
    def test_accepts_special_characters(self):
        """Acepta caracteres especiales no peligrosos."""
        ticket = TicketFactory.create(
            title="Error en versión 2.0 & corrección",
            description="El sistema muestra 'Error 404' al acceder a la página principal",
            user_id="user123"
        )
        
        assert ticket.title == "Error en versión 2.0 & corrección"
        assert "Error 404" in ticket.description
    
    def test_accepts_accented_text(self):
        """Acepta texto con tildes."""
        ticket = TicketFactory.create(
            title="Configuración no funciona",
            description="La página de configuración está rota",
            user_id="user123"
        )
        
        assert ticket is not None
    
    def test_dangerous_input_error_inherits_from_invalid_ticket_data(self):
        """DangerousInputError hereda de InvalidTicketData."""
        with pytest.raises(InvalidTicketData):
            TicketFactory.create(
                title="<script>XSS</script>",
                description="Descripción válida",
                user_id="user123"
            )


class TestDangerousInputErrorException:
    """Tests de la excepción DangerousInputError."""
    
    def test_creates_with_field_name(self):
        """Puede crearse con nombre de campo."""
        exc = DangerousInputError("título")
        
        assert exc.field == "título"
        assert "título" in str(exc)
    
    def test_message_includes_field_and_reason(self):
        """El mensaje incluye el campo y la razón."""
        exc = DangerousInputError("descripción")
        
        message = str(exc)
        assert "descripción" in message
        assert "caracteres HTML o scripts no permitidos" in message
    
    def test_is_domain_exception(self):
        """DangerousInputError es una excepción de dominio."""
        from tickets.domain.exceptions import DomainException
        
        exc = DangerousInputError("título")
        assert isinstance(exc, DomainException)
    
    def test_is_invalid_ticket_data(self):
        """DangerousInputError hereda de InvalidTicketData."""
        exc = DangerousInputError("título")
        assert isinstance(exc, InvalidTicketData)
