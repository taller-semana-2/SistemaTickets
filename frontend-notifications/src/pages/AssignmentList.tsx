import { useEffect, useState } from 'react';
import { notificationApi } from '../api/notificationApi';
import type Notification from '../interface/Notification';
import './AssignmentList.css';

const AssignmentList = () => {
  const [assignments, setAssignments] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAssignments = async () => {
    try {
      setLoading(true);
      const notifications = await notificationApi.getNotifications();
      const filtered = notifications.filter((n) =>
        n.title.toLowerCase().includes('asignado')
      );
      setAssignments(filtered.map(n => ({ ...n, id: String(n.id) })));
    } catch (error) {
      console.error("Error cargando asignaciones", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssignments();
  }, []);

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
          <p className="ticket-count">Tienes {assignments.length} tareas bajo tu cargo</p>
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
            <div key={item.id} className="assignment-card">
              <div className="assignment-badge">Nueva Tarea</div>
              <div className="assignment-content">
                <h3 className="assignment-title">{item.title}</h3>
                <p className="assignment-message">{item.message}</p>
              </div>
              
              <div className="assignment-footer">
                <div className="assignment-date">
                  <span className="icon-clock">🕒</span>
                  {new Date(item.createdAt).toLocaleDateString()}
                </div>
                <button className="btn-action">Gestionar</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AssignmentList;