import { useState } from 'react';
import { useFetchOnce } from '../../hooks/useFetchOnce';
import { ticketApi } from '../../services/ticketApi';
import { authService } from '../../services/auth';
import type { Ticket, TicketPriority } from '../../types/ticket';
import TicketItem from './TicketItem';
import ConfirmModal from '../../components/ConfirmModal';
import { LoadingState, EmptyState, PageHeader } from '../../components/common';
import './TicketList.css';

const TicketList = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  useFetchOnce(async () => {
    try {
      const data = await ticketApi.getTickets();
      const currentUser = authService.getCurrentUser();
      if (currentUser && currentUser.role === 'USER') {
        const userTickets = data.filter(ticket => ticket.user_id === currentUser.id);
        setTickets(userTickets);
      } else {
        setTickets(data);
      }
    } catch (error) {
      console.error('Error al cargar tickets:', error);
    } finally {
      setLoading(false);
    }
  });

  const handleDelete = (id: number) => {
    setDeleteId(id);
  };

  const confirmDelete = async () => {
    if (deleteId === null) return;
    try {
      await ticketApi.deleteTicket(deleteId);
      setTickets((prev) => prev.filter((t) => t.id !== deleteId));
    } catch (error) {
      console.error('Error al eliminar el ticket:', error);
      alert('No se pudo eliminar el ticket');
    } finally {
      setDeleteId(null);
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

      {deleteId !== null && (
        <ConfirmModal
          message="¿Estás seguro de que deseas eliminar este ticket? Esta acción no se puede deshacer."
          onConfirm={confirmDelete}
          onCancel={() => setDeleteId(null)}
        />
      )}
    </div>
  );
};

export default TicketList;

