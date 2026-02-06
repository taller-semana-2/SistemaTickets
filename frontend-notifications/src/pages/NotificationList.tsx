import { useEffect, useState } from 'react';
import { notificationApi } from '../api/notificationApi';
import NotificationItem from '../components/NotificationItem';
import type Notification from '../interface/Notification';
import './NotificationList.css'

const NotificationList = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const data = await notificationApi.getNotifications();
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
    await notificationApi.markAsRead(Number(id));
    loadNotifications();
  };

  const handleClearAll = async () => {
    await notificationApi.clearAll(); 
    setNotifications([]);
  };

  if (loading) {
    return (
      <div className="status-container">
        <p className="loading-text">Cargando notificaciones...</p>
      </div>
    );
  }

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
            />
          ))}
        </div>
      )}
      
    </div>
  );
};

export default NotificationList;