import type { Ticket } from '../types/ticket';
import './ticketItem.css';

interface Props {
  ticket: Ticket;
}

const TicketItem = ({ ticket }: Props) => {
  return (
    <div className="ticket-item">
      <h3 className="ticket-title">{ticket.title}</h3>
      <p className="ticket-description">{ticket.description}</p>
      <small className="ticket-status">Estado: {ticket.status}</small>
    </div>
  );
};

export default TicketItem;
