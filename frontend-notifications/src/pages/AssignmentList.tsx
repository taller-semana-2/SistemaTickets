import { useEffect, useState } from 'react';
import { assignmentsApi } from '../api/assignmentApi';
import type Assignment from '../interface/Assignment';
import './AssignmentList.css';

type UIAssignment = Assignment & {
  managing?: boolean;
  completed?: boolean; // solo frontend (ilusión)
};

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

  /* ---- UI handlers ---- */

  const handleManage = (id: number) => {
    setAssignments((prev) =>
      prev.map((a) =>
        a.id === id ? { ...a, managing: !a.managing } : a
      )
    );
  };

  const handleComplete = (id: number) => {
    setAssignments((prev) =>
      prev.map((a) =>
        a.id === id
          ? { ...a, completed: true, managing: false }
          : a
      )
    );
  };

  const handleDelete = async (id: number) => {
    const confirmed = confirm(
      '¿Seguro que deseas eliminar esta asignación?'
    );
    if (!confirmed) return;

    try {
      await assignmentsApi.deleteAssignment(id);

      // Solo quitamos del estado si el backend responde OK
      setAssignments((prev) => prev.filter((a) => a.id !== id));
    } catch (error) {
      console.error('Error eliminando asignación', error);
      alert('No se pudo eliminar la asignación');
    }
  };

  /* ---- Render ---- */

  if (loading) {
    return (
      <div className="status-container">
        <p className="loading-text">Cargando tus tareas...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      <header className="list-header">
        <div>
          <h1>Mis Asignaciones</h1>
          <p className="ticket-count">
            Tienes {assignments.length} tareas bajo tu cargo
          </p>
        </div>
      </header>

      {assignments.length === 0 ? (
        <div className="status-container">
          <div className="empty-state">
            <span className="empty-icon">check_circle</span>
            <p>¡Estás al día! No tienes asignaciones pendientes.</p>
          </div>
        </div>
      ) : (
        <div className="assignments-grid">
          {assignments.map((item) => (
            <div
              key={item.id}
              className={`assignment-card ${
                item.completed ? 'completed' : ''
              }`}
            >
              <div className="assignment-badge">
                {item.priority}
              </div>

              <div className="assignment-content">
                <h3 className="assignment-title">
                  {item.title}
                </h3>
                <p className="assignment-message">
                  Prioridad: {item.priority}
                </p>
              </div>

              <div className="assignment-footer">
                <div className="assignment-date">
                  🕒{' '}
                  {new Date(item.createdAt).toLocaleDateString()}
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
                      onClick={() =>
                        handleComplete(item.id)
                      }
                    >
                      Marcar como realizada
                    </button>
                  )}

                  <button
                    className="btn-delete"
                    onClick={() =>
                      handleDelete(item.id)
                    }
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
