import type { Ticket, TicketPriority } from '../../types/ticket';
import './TicketItem.css';

const PRIORITY_LABELS: Record<TicketPriority, string> = {
  UNASSIGNED: 'Unassigned',
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
};

/**
 * Devuelve la etiqueta legible para una prioridad.
 * Si no hay prioridad definida, retorna 'Unassigned'.
 */
function getPriorityLabel(priority: TicketPriority | undefined): string {
  if (!priority) return 'Unassigned';
  return PRIORITY_LABELS[priority] ?? 'Unassigned';
}

interface Props {
  ticket: Ticket;
  onDelete: (id: number) => void;
  onUpdateStatus: (id: number, status: Ticket['status']) => void;
}

const STATUS_ORDER: Ticket['status'][] = [
  'OPEN',
  'IN_PROGRESS',
  'CLOSED',
];

const TicketItem = ({ ticket, onDelete, onUpdateStatus }: Props) => {
  const getNextStatus = () => {
    const currentIndex = STATUS_ORDER.indexOf(ticket.status);
    return STATUS_ORDER[(currentIndex + 1) % STATUS_ORDER.length];
  };

  const handleStatusClick = () => {
    const nextStatus = getNextStatus();
    onUpdateStatus(ticket.id, nextStatus);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Sin fecha';
    
    const date = new Date(dateString);
    
    // Verificar si la fecha es válida
    if (isNaN(date.getTime())) return 'Fecha inválida';
    
    return new Intl.DateTimeFormat('es-ES', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  return (
    <div className="ticket-item">
      <div className="ticket-content">
        <div className="ticket-header">
          <span className="ticket-number">#{ticket.id}</span>
          <h3 className="ticket-title">{ticket.title}</h3>
        </div>
        <p className="ticket-description">{ticket.description}</p>
        <div className="ticket-date">
          <span className="calendar-icon">📅</span>
          <small className="created-at">{formatDate(ticket.created_at)}</small>
        </div>
      </div>

      <div className="ticket-footer">
        {/* Badge clickeable */}
        <span
          className={`status-badge ${ticket.status.toLowerCase()}`}
          onClick={handleStatusClick}
          title="Cambiar estado"
          style={{ cursor: 'pointer' }}
        >
          {ticket.status}
        </span>

        <span
          className={`priority-badge priority-${(ticket.priority ?? 'UNASSIGNED').toLowerCase()}`}
          title="Prioridad"
        >
          {getPriorityLabel(ticket.priority)}
        </span>

        <button
          className="delete-button"
          onClick={() => onDelete(ticket.id)}
          title="Eliminar ticket"
        >
          <span className="icon">🗑️</span>
          Eliminar
        </button>
      </div>
    </div>
  );
};

export default TicketItem;
