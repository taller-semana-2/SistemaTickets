import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { ticketApi } from '../../services/ticketApi';
import { authService } from '../../services/auth';
import { LoadingState } from '../../components/common';
import { formatDate, sortByDateAsc } from '../../utils/dateFormat';
import type { Ticket, TicketResponse } from '../../types/ticket';
import './TicketDetail.css';

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface ResponseItemProps {
  response: TicketResponse;
}

/** Renderiza una respuesta individual de un administrador. */
const ResponseItem = ({ response }: ResponseItemProps) => (
  <div className="response-item" data-testid="response-item">
    <div className="response-header">
      <span className="response-admin">{response.admin_name}</span>
      <span className="response-date">{formatDate(response.created_at)}</span>
    </div>
    <p className="response-text">{response.text}</p>
  </div>
);

interface ResponseListProps {
  responses: TicketResponse[];
}

/** Lista de respuestas con empty state incluido. */
const ResponseList = ({ responses }: ResponseListProps) => (
  <section className="responses-section">
    <h2 className="responses-title">Respuestas</h2>

    {responses.length === 0 ? (
      <p className="responses-empty">Aún no hay respuestas para este ticket</p>
    ) : (
      <div className="responses-list">
        {responses.map((r) => (
          <ResponseItem key={r.id} response={r} />
        ))}
      </div>
    )}
  </section>
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Determina si el usuario actual puede ver las respuestas del ticket. */
const canUserViewResponses = (ticket: Ticket): boolean => {
  const currentUser = authService.getCurrentUser();
  const isAdmin = authService.isAdmin();
  return isAdmin || currentUser?.id === ticket.user_id;
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const TicketDetail = () => {
  const { id } = useParams<{ id: string }>();
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

  if (loading) {
    return <LoadingState message="Cargando ticket..." />;
  }

  if (error || !ticket) {
    return <div className="ticket-detail-error">{error ?? 'Ticket no encontrado'}</div>;
  }

  const hasAccess = canUserViewResponses(ticket);

  return (
    <div className="ticket-detail-container">
      <div className="ticket-detail-card">
        <div className="ticket-detail-header">
          <span className="ticket-detail-number">#{ticket.id}</span>
          <h1 className="ticket-detail-title">{ticket.title}</h1>
          <span className={`ticket-detail-status status-${ticket.status.toLowerCase()}`}>
            {ticket.status}
          </span>
        </div>

        <p className="ticket-detail-description">{ticket.description}</p>

        <div className="ticket-detail-meta">
          <span>Creado: {formatDate(ticket.created_at)}</span>
        </div>
      </div>

      {hasAccess ? (
        <ResponseList responses={responses} />
      ) : (
        <div className="access-restricted">
          <p>Acceso restringido</p>
        </div>
      )}
    </div>
  );
};

export default TicketDetail;