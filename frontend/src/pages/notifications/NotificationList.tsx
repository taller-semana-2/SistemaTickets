import { useEffect, useState } from 'react';
import { notificationsApi } from '../../services/notification';
import { LoadingState, EmptyState, PageHeader } from '../../components/common';
import NotificationItem from './NotificationItem';
import type { Notification } from '../../types/notification';
import './NotificationList.css';

const NotificationList = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const data = await notificationsApi.getNotifications();
      setNotifications(data);
    } catch (error) {
      console.error('Error cargando notificaciones', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const handleMarkAsRead = async (id: string) => {
    try {
      await notificationsApi.markAsRead(id);
      loadNotifications();
    } catch (error) {
      console.error('Error marcando como leída', error);
    }
  };

  const handleClearAll = async () => {
    const confirmed = window.confirm(
      '¿Seguro que deseas eliminar todas las notificaciones?'
    );

    if (!confirmed) return;

    try {
      await notificationsApi.clearAll();
      setNotifications([]);
    } catch (error) {
      console.error('Error eliminando notificaciones', error);
      alert('No se pudieron eliminar las notificaciones');
    }
  };

  const handleDelete = async (id: string) => {
    const confirmed = window.confirm(
      '¿Seguro que deseas eliminar esta notificación?'
    );

    if (!confirmed) return;

    try {
      await notificationsApi.deleteNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    } catch (error) {
      console.error('Error eliminando notificación', error);
      alert('No se pudo eliminar la notificación');
    }
  };

  if (loading) {
    return <LoadingState message="Cargando notificaciones..." />;
  }

  return (
    <div className="page-container">
      <PageHeader
        title="Notificaciones"
        subtitle={`${notifications.length} mensajes`}
        action={
          notifications.length > 0 && (
            <button className="btn-clear" onClick={handleClearAll}>
              Limpiar todo
            </button>
          )
        }
      />

      {notifications.length === 0 ? (
        <EmptyState message="No tienes notificaciones." />
      ) : (
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
