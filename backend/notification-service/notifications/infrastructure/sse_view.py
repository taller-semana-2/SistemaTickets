"""
Vista SSE (Server-Sent Events) para notificaciones en tiempo real.

Adaptador de infraestructura que expone un endpoint de streaming
para entregar notificaciones filtradas por user_id.

Issue #50: HU-2.2, EP23
"""

import json
import logging
import time
from typing import Generator

from django.http import StreamingHttpResponse

from notifications.models import Notification

logger = logging.getLogger(__name__)

# Intervalo de polling en segundos (cada 2 s se consulta la BD por nuevas notifs)
_POLL_INTERVAL_SECONDS = 2
# Cada cuántos ciclos se emite un heartbeat para mantener la conexión viva
_HEARTBEAT_EVERY_N_CYCLES = 15


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
    """Generador persistente que emite notificaciones SSE para un usuario.

    Flujo:
    1. Emite un heartbeat inicial para confirmar la conexión.
    2. Emite todas las notificaciones existentes del usuario.
    3. Entra en un bucle de polling cada 2 segundos buscando notificaciones
       nuevas (id > last_seen_id).  Emite un heartbeat cada 30 segundos para
       evitar que proxies intermedios cierren la conexión inactiva.

    El generador es infinito — el cliente (EventSource) controla el ciclo
    de vida de la conexión. Cuando el cliente se desconecta, el servidor
    deja de escribir al socket y el proceso de streaming termina.

    Args:
        user_id: Identificador del usuario destinatario.

    Yields:
        Eventos SSE formateados como cadenas de texto.
    """
    # Heartbeat inicial para confirmar conexión activa (EP23)
    yield ": heartbeat\n\n"

    # ── Paso 1: emitir notificaciones existentes ────────────────────────────
    last_seen_id = 0
    existing = (
        Notification.objects
        .filter(user_id=user_id)
        .only('id', 'ticket_id', 'message', 'sent_at', 'user_id', 'response_id')
        .order_by('sent_at')
    )
    for notification in existing:
        yield _format_sse_event(notification)
        if notification.id > last_seen_id:
            last_seen_id = notification.id

    logger.info(
        "SSE initial batch sent for user=%s, last_seen_id=%d",
        user_id,
        last_seen_id,
    )

    # ── Paso 2: bucle de polling por nuevas notificaciones ──────────────────
    heartbeat_cycle = 0
    while True:
        time.sleep(_POLL_INTERVAL_SECONDS)

        heartbeat_cycle += 1
        if heartbeat_cycle >= _HEARTBEAT_EVERY_N_CYCLES:
            yield ": heartbeat\n\n"
            heartbeat_cycle = 0

        new_notifications = (
            Notification.objects
            .filter(user_id=user_id, id__gt=last_seen_id)
            .only('id', 'ticket_id', 'message', 'sent_at', 'user_id', 'response_id')
            .order_by('id')
        )
        for notification in new_notifications:
            yield _format_sse_event(notification)
            last_seen_id = notification.id
            logger.debug(
                "SSE new notification delivered: user=%s notification_id=%d",
                user_id,
                notification.id,
            )


def sse_notifications_view(request, user_id: str) -> StreamingHttpResponse:
    """Endpoint SSE que mantiene una conexión abierta para un usuario.

    Valida que el ``user_id`` del path esté presente y no sea vacío antes
    de abrir el stream. Retorna un StreamingHttpResponse con content-type
    text/event-stream que emite las notificaciones del usuario en formato SSE.

    Args:
        request: Django HTTP request.
        user_id: Identificador del usuario (del path de la URL).

    Returns:
        StreamingHttpResponse con las notificaciones del usuario, o
        HttpResponse 401 si el user_id no está identificado.
    """
    # B5 — Validar que user_id es válido antes de abrir el stream.
    # EventSource no soporta cabeceras personalizadas, por lo que el user_id
    # viaja en el path. Validamos que sea no vacío; en producción se
    # recomienda reemplazar por una cookie HttpOnly o un token de corta
    # duración en el query string.
    if not user_id or not user_id.strip():
        from django.http import HttpResponse
        logger.warning("SSE connection attempt with empty user_id")
        return HttpResponse(
            '{"error": "user_id requerido para conectarse al canal SSE"}',
            content_type='application/json',
            status=401,
        )

    logger.info("SSE connection opened for user=%s", user_id)

    response = StreamingHttpResponse(
        _notification_stream(user_id),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
