import { authService } from '../../services/auth';
import type { Ticket, TicketPriority } from '../../types/ticket';
import { formatDate } from '../../utils/dateFormat';
import { formatPriority } from './priorityUtils';
import {
  canManagePriority,
  ASSIGNABLE_PRIORITY_OPTIONS,
} from './priorityRules';
import './TicketItem.css';

interface Props {
  ticket: Ticket;
  onDelete: (id: number) => void;
  onUpdateStatus: (id: number, status: Ticket['status']) => void;
  onUpdatePriority?: (id: number, priority: TicketPriority) => void;
}

const STATUS_ORDER: Ticket['status'][] = [
  'OPEN',
  'IN_PROGRESS',
  'CLOSED',
];

const TicketItem = ({ ticket, onDelete, onUpdateStatus, onUpdatePriority }: Props) => {
  const currentUser = authService.getCurrentUser();
  const isAdminEditable = canManagePriority(currentUser, ticket);

  const getNextStatus = () => {
    const currentIndex = STATUS_ORDER.indexOf(ticket.status);
    return STATUS_ORDER[(currentIndex + 1) % STATUS_ORDER.length];
  };

  const handleStatusClick = () => {
    const nextStatus = getNextStatus();
    onUpdateStatus(ticket.id, nextStatus);
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

        {isAdminEditable && onUpdatePriority ? (
          <select
            className={`priority-select priority-select--${(ticket.priority ?? 'Unassigned').toLowerCase()}`}
            value={ticket.priority ?? 'Unassigned'}
            onChange={(e) => onUpdatePriority(ticket.id, e.target.value as TicketPriority)}
            title="Cambiar prioridad"
          >
            <option value="Unassigned" disabled>Sin prioridad</option>
            {ASSIGNABLE_PRIORITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : (
          <span
            className={`priority-badge priority-${(ticket.priority ?? 'Unassigned').toLowerCase()}`}
            title="Prioridad"
          >
            {formatPriority(ticket.priority)}
          </span>
        )}

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
