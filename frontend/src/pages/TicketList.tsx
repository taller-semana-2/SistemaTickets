import { useEffect, useState } from 'react';
import { ticketApi } from '../api/ticketApi';
import type { Ticket } from '../types/ticket';
import TicketItem from '../components/TicketItem';
import './TicketList.css'; // ¡No olvides crear este archivo!

const TicketList = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    ticketApi.getTickets().then((data) => {
      setTickets(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="status-container">
        <p className="loading-text">Cargando tickets...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <header className="list-header">
        <h1>Panel de Tickets</h1>
        <span className="ticket-count">{tickets.length} tickets encontrados</span>
      </header>

      {tickets.length === 0 ? (
        <div className="status-container">
          <p>No hay tickets registrados</p>
        </div>
      ) : (
        <div className="tickets-grid">
          {tickets.map((ticket) => (
            <TicketItem key={ticket.id} ticket={ticket} />
          ))}
        </div>
      )}
    </div>
  );
};

export default TicketList;