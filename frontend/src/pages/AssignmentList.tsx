import { useEffect, useState } from 'react';
import { assignmentsApi } from '../api/assignment';
import {LoadingState, EmptyState, PageHeader } from '../components/common';
import type { Assignment } from '../types/assignment';
import './AssignmentList.css';

interface UIAssignment extends Assignment {
  managing?: boolean;
  completed?: boolean;
}

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
                <p className="assignment-message">Prioridad: {item.priority}</p>
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
