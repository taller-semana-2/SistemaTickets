import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { ticketApi } from '../../services/ticketApi';
import { authService } from '../../services/auth';
import { LoadingState } from '../../components/common';
import type { Ticket, TicketResponse } from '../../types/ticket';
import './TicketDetail.css';

/**
 * Formatea una fecha ISO 8601 a un string legible.
 */
const formatDate = (iso: string): string => {
  const date = new Date(iso);
  return date.toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const TicketDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [responses, setResponses] = useState<TicketResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const currentUser = authService.getCurrentUser();
  const isAdmin = authService.isAdmin();

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const [ticketData, responsesData] = await Promise.all([
          ticketApi.getTicket(Number(id)),
          ticketApi.getResponses(Number(id)),
        ]);
        setTicket(ticketData);
        setResponses(
          [...responsesData].sort(
            (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
          ),
        );
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

  const canViewResponses = isAdmin || currentUser?.id === ticket.user_id;

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

      {canViewResponses ? (
        <section className="responses-section">
          <h2 className="responses-title">Respuestas</h2>

          {responses.length === 0 ? (
            <p className="responses-empty">Aún no hay respuestas para este ticket</p>
          ) : (
            <div className="responses-list">
              {responses.map((response) => (
                <div key={response.id} className="response-item" data-testid="response-item">
                  <div className="response-header">
                    <span className="response-admin">{response.admin_name}</span>
                    <span className="response-date">{formatDate(response.created_at)}</span>
                  </div>
                  <p className="response-text">{response.text}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      ) : (
        <div className="access-restricted">
          <p>Acceso restringido</p>
        </div>
      )}
    </div>
  );
};

export default TicketDetail;