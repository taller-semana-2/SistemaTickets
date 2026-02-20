"""
Vista SSE (Server-Sent Events) para notificaciones en tiempo real.

Adaptador de infraestructura que expone un endpoint de streaming
para entregar notificaciones filtradas por user_id.

Issue #50: HU-2.2, EP23
"""

import json
import logging
from typing import Generator

from django.http import StreamingHttpResponse

from notifications.models import Notification

logger = logging.getLogger(__name__)


def _format_sse_event(notification: Notification) -> str:
    """Formatea una notificación como evento SSE estándar.

    Args:
        notification: Instancia del modelo Notification.

    Returns:
        Cadena con formato SSE: 'event: notification\\ndata: {json}\\n\\n'.
    """
    data = {
        'id': notification.id,
        'ticket_id': notification.ticket_id,
        'message': notification.message,
        'created_at': notification.sent_at.isoformat(),
        'response_id': notification.response_id,
    }
    return f"event: notification\ndata: {json.dumps(data)}\n\n"


def _notification_stream(user_id: str) -> Generator[str, None, None]:
    """Generador que emite notificaciones en formato SSE para un usuario.

    Usa .only() para seleccionar únicamente los campos necesarios
    y .iterator() para eficiencia de memoria en conjuntos grandes.

    Args:
        user_id: Identificador del usuario destinatario.

    Yields:
        Eventos SSE formateados como cadenas de texto.
    """
    # Heartbeat inicial para confirmar conexión activa (EP23)
    yield ": heartbeat\n\n"

    notifications = (
        Notification.objects
        .filter(user_id=user_id)
        .only('id', 'ticket_id', 'message', 'sent_at', 'user_id', 'response_id')
        .order_by('sent_at')
        .iterator()
    )

    count = 0
    for notification in notifications:
        yield _format_sse_event(notification)
        count += 1

    logger.info(
        "SSE stream completed for user=%s, notifications_sent=%d",
        user_id,
        count,
    )


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
    logger.info("SSE connection opened for user=%s", user_id)

    response = StreamingHttpResponse(
        _notification_stream(user_id),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Connection'] = 'keep-alive'
    return response
