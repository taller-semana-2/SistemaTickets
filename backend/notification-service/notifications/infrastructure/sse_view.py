"""
Vista SSE (Server-Sent Events) para notificaciones en tiempo real.

Adaptador de infraestructura que expone un endpoint de streaming
para entregar notificaciones filtradas por user_id.

Issue #50: HU-2.2, EP23
"""

import json

from django.http import StreamingHttpResponse

from notifications.models import Notification


def _notification_stream(user_id: str):
    """Generador que emite notificaciones en formato SSE para un usuario específico.

    Args:
        user_id: Identificador del usuario destinatario de las notificaciones.

    Yields:
        str: Eventos SSE con formato 'event: notification\\ndata: {json}\\n\\n'.
    """
    notifications = Notification.objects.filter(
        user_id=user_id
    ).order_by('sent_at')

    for notification in notifications:
        data = {
            'id': notification.id,
            'ticket_id': notification.ticket_id,
            'message': notification.message,
            'created_at': notification.sent_at.isoformat(),
        }
        yield f"event: notification\ndata: {json.dumps(data)}\n\n"


def sse_notifications_view(request, user_id: str) -> StreamingHttpResponse:
    """Endpoint SSE que mantiene una conexión abierta para un usuario.

    Retorna un StreamingHttpResponse con content-type text/event-stream
    que emite las notificaciones del usuario en formato SSE.

    Args:
        request: Django HTTP request.
        user_id: Identificador del usuario.

    Returns:
        StreamingHttpResponse con las notificaciones del usuario.
    """
    response = StreamingHttpResponse(
        _notification_stream(user_id),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
