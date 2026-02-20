import { useEffect, useState } from 'react';
import { assignmentsApi } from '../../services/assignment';
import { ticketApi } from '../../services/ticketApi';
import { LoadingState, EmptyState, PageHeader } from '../../components/common';
import type { Assignment } from '../../types/assignment';
import TicketAssign from '../../components/TicketAssign';
import ConfirmModal from '../../components/ConfirmModal';
import './AssignmentList.css';

/**
 * Extensión de la interfaz {@link Assignment} con campos de estado de UI.
 */
interface UIAssignment extends Assignment {
  managing?: boolean;
  completed?: boolean;
}

const AssignmentList = () => {
  const [assignments, setAssignments] = useState<UIAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      
      // Fetch both assignments and active tickets concurrently
      const [assignmentsData, ticketsData] = await Promise.all([
        assignmentsApi.getAssignments(),
        ticketApi.getTickets()
      ]);

      // Filter out assignments for tickets that don't exist anymore
      const activeTicketIds = new Set(ticketsData.map(t => t.id.toString()));
      const validAssignments = assignmentsData.filter(a => activeTicketIds.has(a.ticket_id.toString()));

      setAssignments(
        validAssignments.map((a) => ({
          ...a,
          managing: false,
          completed: false,
        }))
      );
    } catch (error) {
      console.error('Error cargando asignaciones', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssignments();
  }, []);

  const handleManage = (id: number) => {
    setAssignments((prev) =>
      prev.map((a) => (a.id === id ? { ...a, managing: !a.managing } : a))
    );
  };

  const handleComplete = (id: number) => {
    setAssignments((prev) =>
      prev.map((a) =>
        a.id === id ? { ...a, completed: true, managing: false } : a
      )
    );
  };

  const handleAssign = async (assignmentId: number, userId: string) => {
    try {
      const updatedAssignment = await assignmentsApi.assignUser(assignmentId, userId);
      
      setAssignments((prev) =>
        prev.map((a) =>
          a.id === assignmentId
            ? { ...a, assigned_to: updatedAssignment.assigned_to }
            : a
        )
      );
      
      alert(`✅ Ticket asignado exitosamente`);
    } catch (error) {
      console.error('Error asignando usuario:', error);
      alert('❌ No se pudo asignar el ticket');
    }
  };

  const handleDelete = (id: number) => {
    setDeleteId(id);
  };

  const confirmDelete = async () => {
    if (deleteId === null) return;
    try {
      await assignmentsApi.deleteAssignment(deleteId);
      setAssignments((prev) => prev.filter((a) => a.id !== deleteId));
    } catch (error) {
      console.error('Error eliminando asignación', error);
      alert('No se pudo eliminar la asignación');
    } finally {
      setDeleteId(null);
    }
  };

  if (loading) {
    return <LoadingState message="Cargando tus tareas..." />;
  }

  return (
    <div className="page-container">
      <PageHeader
        title="Mis Asignaciones"
        subtitle={
          <p className="ticket-count">
            Tienes {assignments.length} tareas bajo tu cargo
          </p>
        }
      />

      {assignments.length === 0 ? (
        <EmptyState
          message="¡Estás al día! No tienes asignaciones pendientes."
          icon="check_circle"
        />
      ) : (
        <div className="assignments-grid">
          {assignments.map((item) => (
            <div
              key={item.id}
              className={`assignment-card ${item.completed ? 'completed' : ''}`}
            >
              <div className="assignment-badge">{item.priority}</div>

              <div className="assignment-content">
                <h3 className="assignment-title">Ticket #{item.ticket_id}</h3>
                <p className="assignment-message">
                  <strong>Prioridad:</strong> {item.priority}
                </p>
              </div>

              <div className="assignment-footer">
                <div className="assignment-date">
                  🕒 {new Date(item.assigned_at).toLocaleDateString()}
                </div>

                <button
                  className="btn-action"
                  onClick={() => handleManage(item.id)}
                >
                  Gestionar
                </button>
              </div>

              {item.managing && (
                <div className="assignment-actions">
                  <TicketAssign
                    ticketId={item.ticket_id}
                    currentAssignedId={item.assigned_to}
                    onAssign={(userId) => handleAssign(item.id, userId)}
                  />

                  {!item.completed && (
                    <button
                      className="btn-complete"
                      onClick={() => handleComplete(item.id)}
                    >
                      Marcar como realizada
                    </button>
                  )}

                  <button
                    className="btn-delete"
                    onClick={() => handleDelete(item.id)}
                  >
                    Eliminar
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {deleteId !== null && (
        <ConfirmModal
          message="¿Seguro que deseas eliminar esta asignación?"
          onConfirm={confirmDelete}
          onCancel={() => setDeleteId(null)}
        />
      )}
    </div>
  );
};

export default AssignmentList;
