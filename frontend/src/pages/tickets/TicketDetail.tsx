import { useParams } from 'react-router-dom';
import { authService } from '../../services/auth';
import { LoadingState } from '../../components/common';
import { formatDate } from '../../utils/dateFormat';
import type { Ticket, TicketResponse } from '../../types/ticket';
import { useTicketDetail } from './useTicketDetail';
import { useSSE } from '../../hooks/useSSE';
import AdminResponseForm from './AdminResponseForm';
import { formatPriority } from './priorityUtils';
import TicketPriorityManager from './TicketPriorityManager';
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
// AdminPanel — decide si mostrar el formulario o el aviso de ticket cerrado
// ---------------------------------------------------------------------------

interface AdminPanelProps {
  ticketId: number;
  isClosed: boolean;
  onResponseCreated: (response: TicketResponse) => void;
}

const AdminPanel = ({ ticketId, isClosed, onResponseCreated }: AdminPanelProps) =>
  isClosed ? (
    <div className="ticket-closed-notice">
      <p>Ticket cerrado — no se pueden añadir más respuestas</p>
    </div>
  ) : (
    <AdminResponseForm ticketId={ticketId} onResponseCreated={onResponseCreated} />
  );

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const TicketDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { ticket, responses, loading, error, appendResponse, fetchResponses, updateTicket } =
    useTicketDetail(id);

  /**
   * HU-2.2 + HU-3.1: conexión SSE scoped a este ticket.
   * - fetchResponses()     → re-carga respuestas cuando llega un evento del
   *                          ticket actualmente visible, sin recargar la página.
   * El Layout global NO monta useSSE mientras esta ruta esté activa, por lo que
   * sólo existe una única conexión EventSource en todo momento.
   */
  useSSE({
    currentTicketId: id ? Number(id) : undefined,
    onRefreshResponses: fetchResponses,
  });

  if (loading) {
    return <LoadingState message="Cargando ticket..." />;
  }

  if (error || !ticket) {
    return <div className="ticket-detail-error">{error ?? 'Ticket no encontrado'}</div>;
  }

  const hasAccess = canUserViewResponses(ticket);
  const isAdmin = authService.isAdmin();

  return (
    <div className="ticket-detail-container">
      <div className="ticket-detail-card">
        <div className="ticket-detail-header">
          <span className="ticket-detail-number">#{ticket.id}</span>
          <h1 className="ticket-detail-title">{ticket.title}</h1>
          <span className={`ticket-detail-status status-${ticket.status.toLowerCase()}`}>
            {ticket.status}
          </span>
          <span
            className={`priority-badge priority-${(ticket.priority ?? 'Unassigned').toLowerCase()}`}
          >
            {formatPriority(ticket.priority)}
          </span>
        </div>

        <p className="ticket-detail-description">{ticket.description}</p>

        <div className="ticket-detail-meta">
          <span>Creado: {formatDate(ticket.created_at)}</span>
        </div>

        {ticket.priority_justification && (
          <p className="ticket-detail-justification">
            <strong>Justificación de prioridad:</strong>{' '}
            {ticket.priority_justification}
          </p>
        )}
      </div>

      {isAdmin && (
        <TicketPriorityManager
          ticket={ticket}
          onUpdate={(updated) => updateTicket(updated)}
        />
      )}

      {hasAccess ? (
        <ResponseList responses={responses} />
      ) : (
        <div className="access-restricted">
          <p>Acceso restringido</p>
        </div>
      )}

      {isAdmin && (
        <AdminPanel
          ticketId={ticket.id}
          isClosed={ticket.status === 'CLOSED'}
          onResponseCreated={appendResponse}
        />
      )}
    </div>
  );
};

export default TicketDetail;
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

      {isAdmin && (
        <AdminPanel
          ticketId={ticket.id}
          isClosed={ticket.status === 'CLOSED'}
          onResponseCreated={appendResponse}
        />
      )}
    </div>
  );
};

export default TicketDetail;
