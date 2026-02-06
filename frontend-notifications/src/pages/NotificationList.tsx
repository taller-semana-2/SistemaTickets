import { useEffect, useState } from 'react';
import { notificationsApi } from '../api/notificationApi';
import NotificationItem from '../components/NotificationItem';
import type Notification from '../interface/Notification';
import './NotificationList.css'

const NotificationList = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const data = await notificationsApi.getNotifications();
      setNotifications(data.map(n => ({ ...n, id: String(n.id) })));
    } catch (error) {
      console.error("Error cargando notificaciones", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const handleMarkAsRead = async (id: string) => {
    await notificationsApi.markAsRead(id);
    loadNotifications();
  };

  const handleClearAll = async () => {
    await notificationsApi.clearAll(); 
    setNotifications([]);
  };

  if (loading) {
    return (
      <div className="status-container">
        <p className="loading-text">Cargando notificaciones...</p>
      </div>
    );
  }

  const handleDelete = async (id: string) => {
  const confirmed = window.confirm(
    '¿Seguro que deseas eliminar esta notificación?'
  );

  if (!confirmed) return;

  try {
    await notificationsApi.deleteNotification(id);

    // actualización optimista
    setNotifications((prev) =>
      prev.filter((n) => n.id !== id)
    );
  } catch (error) {
    console.error('Error eliminando notificación', error);
    alert('No se pudo eliminar la notificación');
  }
};


  return (
    <div className="page-container">
      <div className="list-header">
        <h1>Notificaciones</h1>
        <div className="ticket-count">
          {notifications.length} mensajes
        </div>
      </div>

       {notifications.length > 0 && (
        <button 
          className="btn-clear" 
          onClick={handleClearAll}
          style={{ marginBottom: '1rem', cursor: 'pointer' }}
        >
          Limpiar todo
        </button>
      )}


      {notifications.length === 0 ? (
        <div className="status-container">
          <p>No tienes notificaciones.</p>
        </div>
      ) : (
        /* Cambiamos <ul> por <div> con la clase tickets-grid */
        <div className="tickets-grid">
          {notifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onMarkAsRead={handleMarkAsRead}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
      
    </div>
  );
};

export default NotificationList;