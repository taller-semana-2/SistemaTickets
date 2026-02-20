import { useEffect, useState } from 'react';
import { ticketApi } from '../../services/ticketApi';
import { useAuth } from '../../context/AuthContext';
import type { Ticket } from '../../types/ticket';
import TicketItem from './TicketItem';
import { LoadingState, EmptyState, PageHeader } from '../../components/common';
import './TicketList.css';

const TicketList = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const { user } = useAuth();

  useEffect(() => {
    ticketApi
      .getTickets()
      .then((data) => {
        if (user && user.role === 'USER') {
          const userTickets = data.filter((ticket) => ticket.user_id === user.id);
          setTickets(userTickets);
        } else {
          setTickets(data);
        }
      })
      .catch((error) => {
        console.error('Error al cargar tickets:', error);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [user]);

  const handleDelete = async (id: number) => {
    const confirmed = window.confirm('¿Estás seguro de que deseas eliminar este ticket?');
    if (!confirmed) return;
    try {
      await ticketApi.deleteTicket(id);
      setTickets((prevTickets) => prevTickets.filter((ticket) => ticket.id !== id));
    } catch (error) {
      console.error('Error al eliminar el ticket:', error);
      alert('No se pudo eliminar el ticket');
    }
  };

  const handleUpdateStatus = async (id: number, newStatus: Ticket['status']) => {
    try {
      const updated = await ticketApi.updateStatus(id, newStatus);
      setTickets((prev) => prev.map((t) => (t.id === id ? updated : t)));
    } catch (error) {
      console.error('Error actualizando estado', error);
      alert('No se pudo actualizar el estado');
    }
  };

  if (loading) return <LoadingState message="Cargando tickets..." />;

  const isUser = user?.role === 'USER';
  const pageTitle = isUser ? 'Mis Tickets' : 'Panel de Tickets';

  return (
    <div className="page-container">
      <PageHeader title={pageTitle} subtitle={`${tickets.length} tickets encontrados`} />
      {tickets.length === 0 ? (
        <EmptyState
          message={isUser ? 'No tienes tickets creados' : 'No hay tickets registrados'}
        />
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
