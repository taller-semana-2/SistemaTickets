import { useEffect, useState } from 'react';
import { ticketApi } from '../../services/ticketApi';
import { authService } from '../../services/auth';
import type { Ticket, TicketPriority } from '../../types/ticket';
import TicketItem from './TicketItem';
import { LoadingState, EmptyState, PageHeader } from '../../components/common';
import './TicketList.css';

const TicketList = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    ticketApi.getTickets()
      .then((data) => {
        // Obtener usuario actual
        const currentUser = authService.getCurrentUser();
        
        // Si es USER, filtrar solo sus tickets
        if (currentUser && currentUser.role === 'USER') {
          const userTickets = data.filter(ticket => ticket.user_id === currentUser.id);
          setTickets(userTickets);
        } else {
          // ADMIN ve todos los tickets
          setTickets(data);
        }
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

  const handleUpdatePriority = async (
    id: number,
    priority: TicketPriority
  ) => {
    try {
      const updated = await ticketApi.updatePriority(id, { priority });
      setTickets((prev) =>
        prev.map((t) => (t.id === id ? updated : t))
      );
    } catch (error) {
      console.error('Error actualizando prioridad', error);
      alert('No se pudo actualizar la prioridad');
    }
  };

  if (loading) {
    return <LoadingState message="Cargando tickets..." />;
  }

  // Determinar título según rol
  const currentUser = authService.getCurrentUser();
  const isUser = currentUser?.role === 'USER';
  const pageTitle = isUser ? 'Mis Tickets' : 'Panel de Tickets';

  return (
    <div className="page-container">
      <PageHeader 
        title={pageTitle}
        subtitle={`${tickets.length} tickets encontrados`}
      />

      {tickets.length === 0 ? (
        <EmptyState message={isUser ? "No tienes tickets creados" : "No hay tickets registrados"} />
      ) : (
        <div className="tickets-grid">
          {tickets.map((ticket) => (
            <TicketItem
              key={ticket.id}
              ticket={ticket}
              onDelete={handleDelete}
              onUpdateStatus={handleUpdateStatus}
              onUpdatePriority={handleUpdatePriority}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default TicketList;
