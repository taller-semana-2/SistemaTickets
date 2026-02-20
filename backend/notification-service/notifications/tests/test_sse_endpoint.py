"""
Tests de integración para el endpoint SSE de notificaciones en tiempo real.

Issue #50: feat: backend sse streaming endpoint for real-time notifications (HU-2.2, EP23)

Estos tests validan:
- Que el endpoint SSE existe y retorna text/event-stream (Test 1)
- Que el stream filtra notificaciones por user_id (Test 2)
- Que el formato SSE es correcto (Test 3)

Fase TDD: RED — Estos tests DEBEN FALLAR porque la vista SSE no existe aún.
"""

import json

from django.test import TestCase, TransactionTestCase
from django.http import StreamingHttpResponse

from notifications.models import Notification


class TestSSEEndpointConnectivity(TransactionTestCase):
    """Tests de conectividad del endpoint SSE (Ciclo 1 - RED).
    
    Validan que el endpoint GET /api/notifications/sse/{user_id}/
    existe, retorna el content-type correcto y es un StreamingHttpResponse.
    """

    def test_sse_endpoint_returns_200_with_event_stream_content_type(self):
        """El endpoint SSE debe existir y retornar 200 con content-type text/event-stream.
        
        Criterio HU-2.2: El usuario tiene una conexión SSE activa al endpoint de notificaciones.
        """
        response = self.client.get('/api/notifications/sse/user-123/')

        assert response.status_code == 200
        assert 'text/event-stream' in response['Content-Type']

    def test_sse_endpoint_returns_streaming_http_response(self):
        """El endpoint SSE debe retornar un StreamingHttpResponse para mantener la conexión abierta."""
        response = self.client.get('/api/notifications/sse/user-123/')

        assert isinstance(response, StreamingHttpResponse)

    def test_sse_endpoint_streams_notifications_for_given_user_id(self):
        """El endpoint SSE debe emitir notificaciones filtradas por user_id.
        
        Criterio EP23: Solo se envían notificaciones al usuario correspondiente.
        """
        # Arrange: crear notificaciones para user-123
        Notification.objects.create(
            ticket_id="42",
            message="Nueva respuesta en Ticket #42",
            user_id="user-123"
        )
        Notification.objects.create(
            ticket_id="99",
            message="Nueva respuesta en Ticket #99",
            user_id="user-456"
        )

        # Act: conectar al SSE para user-123
        response = self.client.get('/api/notifications/sse/user-123/')
        content = b''.join(response.streaming_content).decode('utf-8')

        # Assert: solo debe contener la notificación de user-123
        assert 'Ticket #42' in content
        assert 'Ticket #99' not in content

    def test_sse_endpoint_returns_proper_sse_format(self):
        """Los eventos SSE deben seguir el formato estándar: event: notification\\ndata: {json}\\n\\n.
        
        El JSON debe incluir: id, ticket_id, message, created_at.
        Referencia: Sección 6.2 del USER_STORY_NOTIFICATION.md.
        """
        # Arrange: crear una notificación
        Notification.objects.create(
            ticket_id="42",
            message="Nueva respuesta en Ticket #42",
            user_id="user-123"
        )

        # Act
        response = self.client.get('/api/notifications/sse/user-123/')
        content = b''.join(response.streaming_content).decode('utf-8')

        # Assert: formato SSE correcto
        assert 'event: notification' in content
        assert 'data: ' in content

        # Extraer y validar el JSON del data
        for line in content.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                assert 'id' in data
                assert 'ticket_id' in data
                assert 'message' in data
                assert 'created_at' in data
                break
        else:
            assert False, "No se encontró ninguna línea 'data:' en el stream SSE"


class TestSSEHeartbeatAndFiltering(TransactionTestCase):
    """Tests de heartbeat y filtrado por usuario para el endpoint SSE (Ciclo 2 - RED).
    
    Validan:
    - Envío de heartbeat (comentario SSE) para mantener la conexión viva (EP23).
    - Estricto aislamiento: un user_id nunca ve notificaciones de otro.
    - El payload SSE incluye response_id para identificación en frontend.
    """

    def test_sse_stream_includes_heartbeat_comment(self):
        """EP23: El stream debe incluir un heartbeat (comentario SSE ':ping') 
        para evitar que la conexión sea cerrada por timeouts de infraestructura.
        
        Un heartbeat SSE es un comentario con formato ': ping\\n\\n' o ':heartbeat\\n\\n'.
        """
        response = self.client.get('/api/notifications/sse/user-123/')
        content = b''.join(response.streaming_content).decode('utf-8')

        # El stream debe contener al menos un comentario de heartbeat
        assert ': heartbeat' in content or ':heartbeat' in content

    def test_sse_stream_isolates_users_strictly(self):
        """Solo las notificaciones del user_id solicitado deben aparecer en el stream.
        
        Scenario: Solo se envían notificaciones al usuario correspondiente.
        """
        # Arrange: notificaciones para distintos usuarios
        Notification.objects.create(
            ticket_id="10", message="Notif for user-A", user_id="user-A"
        )
        Notification.objects.create(
            ticket_id="20", message="Notif for user-B", user_id="user-B"
        )
        Notification.objects.create(
            ticket_id="30", message="Another for user-A", user_id="user-A"
        )

        # Act: conectar como user-A
        response = self.client.get('/api/notifications/sse/user-A/')
        content = b''.join(response.streaming_content).decode('utf-8')

        # Assert: solo notificaciones de user-A
        lines_with_data = [l for l in content.split('\n') if l.startswith('data: ')]
        assert len(lines_with_data) == 2

        for line in lines_with_data:
            data = json.loads(line[6:])
            assert 'user-B' not in data.get('message', '')

    def test_sse_event_payload_includes_response_id(self):
        """El payload del evento SSE debe incluir response_id para que el frontend 
        pueda identificar la respuesta asociada.
        
        Referencia: USER_STORY_NOTIFICATION.md sección 6.2.
        """
        # Arrange: crear una notificación con response_id
        Notification.objects.create(
            ticket_id="42",
            message="Nueva respuesta en Ticket #42",
            user_id="user-123",
            response_id=7
        )

        # Act
        response = self.client.get('/api/notifications/sse/user-123/')
        content = b''.join(response.streaming_content).decode('utf-8')

        # Assert: el payload debe tener response_id
        for line in content.split('\n'):
            if line.startswith('data: '):
                data = json.loads(line[6:])
                assert 'response_id' in data
                assert data['response_id'] == 7
                break
        else:
            assert False, "No data line found in SSE stream"

    def test_sse_no_notifications_still_sends_heartbeat(self):
        """Incluso sin notificaciones, el stream debe enviar al menos un heartbeat.
        
        Esto es necesario para confirmar que la conexión SSE está activa.
        """
        response = self.client.get('/api/notifications/sse/user-empty/')
        content = b''.join(response.streaming_content).decode('utf-8')

        # Sin notificaciones, pero el heartbeat debe estar presente
        assert len(content.strip()) > 0, "El stream no debe estar completamente vacío"
        assert ': heartbeat' in content or ':heartbeat' in content
