import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
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
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const isAdmin = currentUser?.role === 'ADMIN';
  const isAdminEditable = canManagePriority(currentUser, ticket);
  const isClosed = ticket.status === 'CLOSED';
  const canChangeStatus = isAdmin && !isClosed;

  const getNextStatus = () => {
    const currentIndex = STATUS_ORDER.indexOf(ticket.status);
    return STATUS_ORDER[(currentIndex + 1) % STATUS_ORDER.length];
  };

  const handleStatusClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!canChangeStatus) return;
    const nextStatus = getNextStatus();
    onUpdateStatus(ticket.id, nextStatus);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(ticket.id);
  };

  const handlePriorityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    e.stopPropagation();
    if (onUpdatePriority) {
      onUpdatePriority(ticket.id, e.target.value as TicketPriority);
    }
  };

  const handleCardClick = () => {
    navigate(`/tickets/${ticket.id}`);
  };

  return (
    <div
      className="ticket-item ticket-item--clickable"
      onClick={handleCardClick}
      role="link"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') handleCardClick(); }}
    >
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
        <span
          className={`status-badge ${ticket.status.toLowerCase()}${canChangeStatus ? ' status-badge--clickable' : ''}`}
          onClick={canChangeStatus ? handleStatusClick : (e) => e.stopPropagation()}
          title={canChangeStatus ? 'Cambiar estado' : ticket.status}
          style={{ cursor: canChangeStatus ? 'pointer' : 'default' }}
        >
          {ticket.status}
        </span>

        {isAdminEditable && onUpdatePriority ? (
          <select
            className={`priority-select priority-select--${(ticket.priority ?? 'Unassigned').toLowerCase()}`}
            value={ticket.priority ?? 'Unassigned'}
            onChange={handlePriorityChange}
            onClick={(e) => e.stopPropagation()}
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
          onClick={handleDeleteClick}
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
