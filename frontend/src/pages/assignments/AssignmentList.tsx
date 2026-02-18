import { useEffect, useState } from 'react';
import { assignmentsApi } from '../../services/assignment';
import {LoadingState, EmptyState, PageHeader } from '../../components/common';
import type { Assignment } from '../../types/assignment';
import TicketAssign from '../../components/TicketAssign';
import './AssignmentList.css';

/**
 * Extensión de la interfaz {@link Assignment} con campos de estado de UI.
 *
 * Agrega propiedades efímeras que controlan el comportamiento visual
 * de cada tarjeta de asignación en la interfaz, sin modificar los datos
 * persistidos en el backend.
 *
 * @interface UIAssignment
 * @extends {Assignment}
 * @property {boolean} [managing] - Indica si el panel de gestión (reasignar,
 *   completar, eliminar) está visible para esta asignación.
 * @property {boolean} [completed] - Indica si la asignación fue marcada
 *   como completada en la sesión actual (estado local, no persistido).
 */
interface UIAssignment extends Assignment {
  managing?: boolean;
  completed?: boolean;
}

/**
 * Componente de página que muestra y gestiona las asignaciones del usuario.
 *
 * Carga la lista de asignaciones desde el backend (`assignmentsApi`) y
 * permite al usuario:
 * - **Ver** todas sus asignaciones con prioridad y fecha.
 * - **Gestionar** cada asignación (toggle del panel de acciones).
 * - **Reasignar** un ticket a otro usuario mediante {@link TicketAssign}.
 * - **Completar** una asignación (marcado visual local).
 * - **Eliminar** una asignación con confirmación previa.
 *
 * @example
 * ```tsx
 * <Route path="/assignments" element={<AssignmentList />} />
 * ```
 *
 * @returns {JSX.Element} Grid de tarjetas de asignación con estados de
 *   carga, vacío y error manejados internamente.
 */
const AssignmentList = () => {
  const [assignments, setAssignments] = useState<UIAssignment[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      const data = await assignmentsApi.getAssignments();

      setAssignments(
        data.map((a) => ({
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
      
      // Actualizar en el estado local
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

  const handleDelete = async (id: number) => {
    const confirmed = window.confirm(
      '¿Seguro que deseas eliminar esta asignación?'
    );
    if (!confirmed) return;

    try {
      await assignmentsApi.deleteAssignment(id);
      setAssignments((prev) => prev.filter((a) => a.id !== id));
    } catch (error) {
      console.error('Error eliminando asignación', error);
      alert('No se pudo eliminar la asignación');
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
    </div>
  );
};

export default AssignmentList;
