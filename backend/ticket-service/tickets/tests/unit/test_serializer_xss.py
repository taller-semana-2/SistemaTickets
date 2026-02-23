"""
Tests unitarios para validación XSS en TicketSerializer.

Verifica que el serializer rechaza inputs con HTML/scripts peligrosos
antes de que lleguen a la capa de dominio (defensa en profundidad).
"""

import pytest

from tickets.serializer import TicketSerializer


class TestTicketSerializerXSSValidation:
    """Tests de validación XSS en TicketSerializer."""
    
    def test_rejects_script_tag_in_title(self):
        """Serializer rechaza <script> en título."""
        data = {
            "title": "<script>alert('XSS')</script>",
            "description": "Descripción válida",
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is False
        assert "title" in serializer.errors
        assert "caracteres HTML o scripts no permitidos" in str(serializer.errors["title"][0])
    
    def test_rejects_img_onerror_in_description(self):
        """Serializer rechaza <img onerror> en descripción."""
        data = {
            "title": "Título válido",
            "description": '<img src=x onerror="alert(1)">',
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is False
        assert "description" in serializer.errors
        assert "caracteres HTML o scripts no permitidos" in str(serializer.errors["description"][0])
    
    def test_rejects_javascript_protocol_in_title(self):
        """Serializer rechaza protocolo javascript: en título."""
        data = {
            "title": 'Click <a href="javascript:alert(1)">aquí</a>',
            "description": "Descripción válida",
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is False
        assert "title" in serializer.errors
    
    def test_rejects_onclick_in_description(self):
        """Serializer rechaza event handler onclick."""
        data = {
            "title": "Título válido",
            "description": '<div onclick="malicious()">Click aquí</div>',
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is False
        assert "description" in serializer.errors
    
    def test_rejects_onload_in_title(self):
        """Serializer rechaza event handler onload."""
        data = {
            "title": '<body onload="malicious()">Título</body>',
            "description": "Descripción válida",
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is False
        assert "title" in serializer.errors
    
    def test_rejects_iframe_tag(self):
        """Serializer rechaza tags <iframe>."""
        data = {
            "title": "Título válido",
            "description": '<iframe src="http://evil.com"></iframe>',
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is False
        assert "description" in serializer.errors
    
    def test_rejects_object_tag(self):
        """Serializer rechaza tags <object>."""
        data = {
            "title": '<object data="exploit.swf"></object>',
            "description": "Descripción válida",
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is False
        assert "title" in serializer.errors
    
    def test_rejects_embed_tag(self):
        """Serializer rechaza tags <embed>."""
        data = {
            "title": "Título válido",
            "description": '<embed src="exploit.swf">',
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is False
        assert "description" in serializer.errors
    
    def test_accepts_valid_plain_text(self):
        """Serializer acepta texto plano válido."""
        data = {
            "title": "Problema con el login",
            "description": "No puedo iniciar sesión en el sistema",
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is True
        assert serializer.validated_data["title"] == "Problema con el login"
        assert serializer.validated_data["description"] == "No puedo iniciar sesión en el sistema"
    
    def test_accepts_text_with_special_characters(self):
        """Serializer acepta caracteres especiales seguros."""
        data = {
            "title": "Error en versión 2.0 & corrección",
            "description": "El sistema muestra 'Error 404' al acceder",
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is True
    
    def test_accepts_accented_text(self):
        """Serializer acepta texto con tildes."""
        data = {
            "title": "Configuración no funciona",
            "description": "La página de configuración está rota",
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is True
    
    def test_accepts_text_with_numbers_and_symbols(self):
        """Serializer acepta números y símbolos comunes."""
        data = {
            "title": "Error #404 - Página no encontrada",
            "description": "Versión 2.3.1 muestra error (código: 404)",
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is True
    
    def test_accepts_email_addresses(self):
        """Serializer acepta direcciones de email."""
        data = {
            "title": "Problema con notificaciones",
            "description": "No recibo emails en soporte@ejemplo.com",
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is True
    
    def test_rejects_both_title_and_description_with_xss(self):
        """Serializer puede rechazar ambos campos simultáneamente."""
        data = {
            "title": "<script>alert('title')</script>",
            "description": "<script>alert('desc')</script>",
            "user_id": "user123",
            "status": "OPEN"
        }
        
        serializer = TicketSerializer(data=data)
        
        assert serializer.is_valid() is False
        assert "title" in serializer.errors
        assert "description" in serializer.errors
    
    def test_case_insensitive_detection(self):
        """Serializer detecta XSS independientemente del case."""
        test_cases = [
            "<SCRIPT>alert(1)</SCRIPT>",
            "<ScRiPt>alert(1)</ScRiPt>",
            "<script>alert(1)</script>",
            "<IMG SRC=x ONERROR=alert(1)>",
            '<img src=x OnError="alert(1)">',
        ]
        
        for malicious_input in test_cases:
            data = {
                "title": malicious_input,
                "description": "Descripción válida",
                "user_id": "user123",
                "status": "OPEN"
            }
            
            serializer = TicketSerializer(data=data)
            
            assert serializer.is_valid() is False, f"Debería rechazar: {malicious_input}"
            assert "title" in serializer.errors
