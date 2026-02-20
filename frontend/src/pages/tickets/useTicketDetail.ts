import { useEffect, useState } from 'react';
import { ticketApi } from '../../services/ticketApi';
import { sortByDateAsc } from '../../utils/dateFormat';
import type { Ticket, TicketResponse } from '../../types/ticket';

interface UseTicketDetailResult {
  ticket: Ticket | null;
  responses: TicketResponse[];
  loading: boolean;
  error: string | null;
  appendResponse: (response: TicketResponse) => void;
}

/**
 * Hook que encapsula la carga de datos de un ticket y su lista de respuestas.
 * Expone appendResponse para agregar optimistamente tras un submit exitoso.
 */
export const useTicketDetail = (id: string | undefined): UseTicketDetailResult => {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [responses, setResponses] = useState<TicketResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  return { ticket, responses, loading, error, appendResponse };
};
