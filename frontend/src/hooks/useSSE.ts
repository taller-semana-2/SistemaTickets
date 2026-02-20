import { useEffect, useCallback, useRef } from 'react';
import { useNotifications } from '../context/NotificacionContext';
import { authService } from '../services/auth';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Payload esperado del evento SSE "notification" emitido por el backend. */
interface SSENotificationPayload {
  ticket_id: number;
  message?: string;
  [key: string]: unknown;
}

export interface UseSSEOptions {
  /**
   * ID del ticket actualmente visible en TicketDetail.
   * Cuando el payload del evento coincide con este ID, se invoca
   * `onRefreshResponses` para re-cargar las respuestas.
   */
  currentTicketId?: number;
  /**
   * Callback que re-fetch las respuestas del ticket actual.
   * Sólo se llama si el evento SSE contiene el mismo `ticket_id`
   * que `currentTicketId`.
   */
  onRefreshResponses?: () => void;
}

// ---------------------------------------------------------------------------
// Constante de URL base (permite sobreescribir vía variable de entorno)
// ---------------------------------------------------------------------------

const SSE_BASE_URL =
  (import.meta.env.VITE_NOTIFICATION_BASE_URL as string | undefined) ?? 'http://localhost:8001';

/**
 * Builds the SSE endpoint URL including the authenticated user's ID.
 * Pattern: /api/notifications/sse/<user_id>/
 * The user_id in the path acts as the identity claim for the MVP; the
 * backend filters events for that specific user.
 */
const buildSSEEndpoint = (): string => {
  const currentUser = authService.getCurrentUser();
  const userId = currentUser?.id ?? '';
  return `${SSE_BASE_URL}/api/notifications/sse/${userId}/`;
};

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * useSSE — abre una conexión Server-Sent Events con el notification-service.
 *
 * Responsabilidades:
 *  - Crear la conexión EventSource al montar y cerrarla al desmontar.
 *  - Al recibir el evento "notification": llamar `refreshUnread()` del contexto
 *    global para que el badge de notificaciones se actualice.
 *  - Si `currentTicketId` coincide con el `ticket_id` del evento, invocar
 *    `onRefreshResponses` para re-cargar la lista de respuestas en TicketDetail.
 *  - Registrar errores de transporte en consola sin romper la conexión
 *    (EventSource reintenta automáticamente).
 *
 * @param options - Opciones opcionales para el comportamiento en TicketDetail.
 */
export const useSSE = (options?: UseSSEOptions): void => {
  const { refreshUnread } = useNotifications();

  // Guardamos las últimas opciones en un ref para no necesitar incluirlas
  // como dependencias del effect (evita reconexiones innecesarias).
  const optionsRef = useRef(options);
  optionsRef.current = options;

  // refreshUnread también va en ref para la misma razón.
  const refreshUnreadRef = useRef(refreshUnread);
  refreshUnreadRef.current = refreshUnread;

  const handleNotification = useCallback((event: MessageEvent) => {
    let payload: SSENotificationPayload;

    try {
      payload = JSON.parse(event.data as string) as SSENotificationPayload;
    } catch (err) {
      console.error('[SSE] Error al parsear payload del evento "notification":', err);
      return;
    }

    // Siempre actualizar el contador global de no leídas
    refreshUnreadRef.current();

    // Si estamos en el TicketDetail del ticket que acaba de recibir actividad,
    // disparar un re-fetch de las respuestas.
    const { currentTicketId, onRefreshResponses } = optionsRef.current ?? {};
    if (
      currentTicketId !== undefined &&
      payload.ticket_id === currentTicketId &&
      onRefreshResponses !== undefined
    ) {
      onRefreshResponses();
    }
  }, []);

  useEffect(() => {
    const sseEndpoint = buildSSEEndpoint();
    const es = new EventSource(sseEndpoint);

    es.addEventListener('notification', handleNotification);

    es.onerror = (err: Event) => {
      // EventSource maneja la reconexión automáticamente.
      // Solo registramos el error para visibilidad de diagnóstico.
      console.error('[SSE] Error de conexión — se reintentará automáticamente:', err);
    };

    return () => {
      es.close();
    };
  }, [handleNotification]);
};
