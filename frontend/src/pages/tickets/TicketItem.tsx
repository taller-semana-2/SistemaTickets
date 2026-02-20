import type { Ticket } from '../../types/ticket';
import { formatDate } from '../../utils/dateFormat';
import './TicketItem.css';

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
