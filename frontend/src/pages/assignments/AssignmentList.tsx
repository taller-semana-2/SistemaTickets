import { useEffect, useState } from 'react';
import { assignmentsApi } from '../../services/assignment';
import { ticketApi } from '../../services/ticketApi';
import { userService } from '../../services/user';
import { LoadingState, EmptyState, PageHeader } from '../../components/common';
import type { Assignment } from '../../types/assignment';
import type { TicketPriority } from '../../types/ticket';
import { formatPriority } from '../tickets/priorityUtils';
import TicketAssign from '../../components/TicketAssign';
import ConfirmModal from '../../components/ConfirmModal';
import './AssignmentList.css';

/**
 * Extensión de la interfaz {@link Assignment} con campos de estado de UI.
 */
interface UIAssignment extends Assignment {
  managing?: boolean;
  completed?: boolean;
  /** Título del ticket asociado, resuelto en tiempo de carga. */
  ticket_title?: string;
}

/**
 * Normaliza un string de prioridad arbitrario al tipo {@link TicketPriority}.
 * Acepta cualquier casing ('HIGH', 'high', 'High' → 'High').
 *
 * @param raw - Valor de prioridad crudo proveniente de la API
 * @returns Valor normalizado compatible con {@link TicketPriority}
 */
function toPriorityKey(raw: string | undefined): TicketPriority {
  if (!raw) return 'Unassigned';
  const normalized = (raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase()) as TicketPriority;
  const valid: TicketPriority[] = ['Unassigned', 'Low', 'Medium', 'High'];
  return valid.includes(normalized) ? normalized : 'Unassigned';
}

const AssignmentList = () => {
  const [assignments, setAssignments] = useState<UIAssignment[]>([]);
  const [agentMap, setAgentMap] = useState<Map<string, string>>(new Map());
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const loadAssignments = async () => {
    try {
      setLoading(true);

      // Fetch assignments, tickets y agentes concurrentemente
      const [assignmentsData, ticketsData, adminUsers] = await Promise.all([
        assignmentsApi.getAssignments(),
        ticketApi.getTickets(),
        userService.getAdminUsers().catch(() => []),
      ]);

      // Mapa de id → título de ticket para enriquecer las tarjetas
      const ticketTitleMap = new Map(ticketsData.map(t => [t.id.toString(), t.title]));

      // Mapa de id → username de agente para resolver nombre en descripción
      const newAgentMap = new Map(adminUsers.map(u => [u.id, u.username]));
      setAgentMap(newAgentMap);

      // Filter out assignments for tickets that don't exist anymore
      const activeTicketIds = new Set(ticketsData.map(t => t.id.toString()));
      const validAssignments = assignmentsData.filter(a => activeTicketIds.has(a.ticket_id.toString()));

      // Build a set of closed ticket IDs to pre-mark as completed
      const closedTicketIds = new Set(
        ticketsData
          .filter(t => t.status === 'CLOSED')
          .map(t => t.id.toString())
      );

      setAssignments(
        validAssignments.map((a) => ({
          ...a,
          managing: false,
          completed: closedTicketIds.has(a.ticket_id.toString()),
          ticket_title: ticketTitleMap.get(a.ticket_id.toString()),
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

  const handleComplete = async (id: number) => {
    const assignment = assignments.find((a) => a.id === id);
    if (!assignment) return;

    try {
      const { ticket_id } = assignment;

      // Fetch current ticket to check its status
      const ticket = await ticketApi.getTicket(ticket_id);

      // Domain rule: OPEN → IN_PROGRESS → CLOSED (must follow this order)
      if (ticket.status === 'OPEN') {
        await ticketApi.updateStatus(ticket_id, 'IN_PROGRESS');
      }

      if (ticket.status !== 'CLOSED') {
        await ticketApi.updateStatus(ticket_id, 'CLOSED');
      }

      setAssignments((prev) =>
        prev.map((a) =>
          a.id === id ? { ...a, completed: true, managing: false } : a
        )
      );
    } catch (error) {
      console.error('Error al marcar como realizada:', error);
      alert('No se pudo cerrar el ticket asociado. Intenta de nuevo.');
    }
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
              <div className={`assignment-badge priority-${(item.priority || 'unassigned').toLowerCase()}`}>
                {formatPriority(toPriorityKey(item.priority))}
              </div>

              <div className="assignment-content">
                <div className="assignment-ticket-header">
                  <span className="assignment-ticket-id">#{item.ticket_id}</span>
                  <h3 className="assignment-title">
                    {item.ticket_title ?? `Ticket #${item.ticket_id}`}
                  </h3>
                </div>
                <p className="assignment-message">
                  {item.assigned_to
                    ? `Asignación: ${agentMap.get(item.assigned_to) ?? item.assigned_to}`
                    : 'No asignado'}
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
