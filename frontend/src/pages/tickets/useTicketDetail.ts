import { useEffect, useState, useCallback } from 'react';
import { ticketApi } from '../../services/ticketApi';
import { sortByDateAsc } from '../../utils/dateFormat';
import type { Ticket, TicketResponse } from '../../types/ticket';

interface UseTicketDetailResult {
  ticket: Ticket | null;
  responses: TicketResponse[];
  loading: boolean;
  error: string | null;
  appendResponse: (response: TicketResponse) => void;
  /** Actualiza el ticket en el estado local (ej. tras cambio de prioridad). */
  updateTicket: (ticket: Ticket) => void;
  /** Re-fetch solo las respuestas del ticket (sin recargar el ticket en sí). */
  fetchResponses: () => Promise<void>;
}

/**
 * Hook que encapsula la carga de datos de un ticket y su lista de respuestas.
 * Expone:
 *  - appendResponse: inserta optimistamente una respuesta tras un submit exitoso.
 *  - fetchResponses: re-carga respuestas desde la API (usado por SSE para
 *    actualizar la lista cuando llega una notificación del ticket activo).
 */
export const useTicketDetail = (id: string | undefined): UseTicketDetailResult => {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [responses, setResponses] = useState<TicketResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Re-fetch estable de respuestas. Identidad estable gracias a useCallback;
   * no provoca reconexiones SSE aunque el componente re-renderice.
   */
  const fetchResponses = useCallback(async () => {
    if (!id) return;
    try {
      const responsesData = await ticketApi.getResponses(Number(id));
      setResponses(sortByDateAsc(responsesData, 'created_at'));
    } catch (err) {
      console.error('[useTicketDetail] Error al refrescar respuestas:', err);
    }
  }, [id]);

  useEffect(() => {
    if (!id) return;

    const ticketId = Number(id);

    const fetchData = async () => {
      try {
        setLoading(true);
        const [ticketData, responsesData] = await Promise.all([
          ticketApi.getTicket(ticketId),
          ticketApi.getResponses(ticketId),
        ]);
        setTicket(ticketData);
        setResponses(sortByDateAsc(responsesData, 'created_at'));
      } catch (err) {
        console.error('Error loading ticket detail:', err);
        setError('No se pudo cargar el ticket');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  const appendResponse = (response: TicketResponse) => {
    setResponses((prev) => sortByDateAsc([...prev, response], 'created_at'));
  };

  return { ticket, responses, loading, error, appendResponse, fetchResponses, updateTicket: setTicket };
};
