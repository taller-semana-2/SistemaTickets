import { useEffect, useState } from 'react';
import { ticketApi } from '../api/ticketApi';
import type { Ticket } from '../types/ticket';
import TicketItem from '../components/TicketItem';
import './TicketList.css';

const TicketList = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    ticketApi.getTickets()
      .then((data) => {
        setTickets(data);
      })
      .catch((error) => {
        console.error('Error al cargar tickets:', error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleDelete = async (id: number) => {
    const confirmed = window.confirm(
      '¿Estás seguro de que deseas eliminar este ticket? Esta acción no se puede deshacer.'
    );

    if (!confirmed) return;

    try {
      await ticketApi.deleteTicket(id);

      setTickets((prevTickets) =>
        prevTickets.filter((ticket) => ticket.id !== id)
      );
    } catch (error) {
      console.error('Error al eliminar el ticket:', error);
      alert('No se pudo eliminar el ticket');
    }
  };

  const handleUpdateStatus = async (
  id: number,
  status: Ticket['status']
) => {
  try {
    const updated = await ticketApi.updateStatus(id, status);

    setTickets((prev) =>
      prev.map((t) =>
        t.id === id ? updated : t
      )
    );
  } catch (error) {
    console.error('Error actualizando estado', error);
    alert('No se pudo actualizar el estado');
  }
};

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
        <span className="ticket-count">
          {tickets.length} tickets encontrados
        </span>
      </header>

      {tickets.length === 0 ? (
        <div className="status-container">
          <p>No hay tickets registrados</p>
        </div>
      ) : (
        <div className="tickets-grid">
          {tickets.map((ticket) => (
            <TicketItem
              key={ticket.id}
              ticket={ticket}
              onDelete={handleDelete}
              onUpdateStatus={handleUpdateStatus}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default TicketList;
