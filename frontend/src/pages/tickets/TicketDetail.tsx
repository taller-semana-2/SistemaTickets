import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { ticketApi } from '../../services/ticketApi';
import type { Ticket, TicketPriority } from '../../types/ticket';

const PRIORITY_LABELS: Record<TicketPriority, string> = {
  UNASSIGNED: 'Unassigned',
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
};

function getPriorityLabel(priority: TicketPriority | undefined): string {
  if (!priority) return 'Unassigned';
  return PRIORITY_LABELS[priority] ?? 'Unassigned';
}

const TicketDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    setLoading(true);
    setError(null);

    ticketApi
      .getTicket(parseInt(id, 10))
      .then((data) => setTicket(data))
      .catch(() => setError('No se pudo cargar el ticket. Intenta de nuevo.'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="ticket-detail-loading">
        Cargando ticket…
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="ticket-detail-error"
        style={{
          color: '#dc2626',
          background: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          padding: '1rem 1.5rem',
          margin: '1rem 0',
        }}
      >
        {error}
      </div>
    );
  }

  if (!ticket) return null;

  return (
    <div className="ticket-detail">
      <h1>#{ticket.id} — {ticket.title}</h1>
      <p>{ticket.description}</p>

      <div className="ticket-detail-meta">
        <span
          className={`status-badge ${ticket.status.toLowerCase()}`}
        >
          {ticket.status}
        </span>

        <span
          className={`priority-badge priority-${(ticket.priority ?? 'UNASSIGNED').toLowerCase()}`}
        >
          {getPriorityLabel(ticket.priority)}
        </span>
      </div>

      {ticket.priority_justification && (
        <p className="ticket-detail-justification">
          <strong>Justificación de prioridad:</strong>{' '}
          {ticket.priority_justification}
        </p>
      )}
    </div>
  );
};

export default TicketDetail;
