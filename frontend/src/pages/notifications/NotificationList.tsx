import { useEffect, useState } from 'react';
import { useFetchOnce } from '../../hooks/useFetchOnce';
import { notificationsApi } from '../../services/notification';
import { useNotifications } from '../../context/NotificacionContext';
import { LoadingState, EmptyState, PageHeader } from '../../components/common';
import ConfirmModal from '../../components/ConfirmModal';
import NotificationItem from './NotificationItem';
import type { Notification } from '../../types/notification';
import './NotificationList.css';

const NotificationList = () => {
  const { trigger, refreshUnread } = useNotifications();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal State
  const [modalState, setModalState] = useState<{
    isOpen: boolean;
    message: string;
    onConfirm: () => void;
  }>({
    isOpen: false,
    message: '',
    onConfirm: () => {},
  });

  /**
   * Carga las notificaciones desde la API
   */
  const loadNotifications = async () => {
    try {
      const data = await notificationsApi.getNotifications();
      setNotifications(data);
    } catch (error) {
      console.error('Error cargando notificaciones', error);
    } finally {
      setLoading(false);
    }
  };

  // Cargar notificaciones una sola vez en el montaje
  useFetchOnce(() => {
    loadNotifications();
  });

  // Recargar notificaciones cuando trigger cambie (por ej. después de acciones del usuario)
  useEffect(() => {
    if (trigger > 0) {
      loadNotifications();
    }
  }, [trigger]);

  const handleMarkAsRead = async (id: string) => {
    try {
      await notificationsApi.markAsRead(id);
      loadNotifications();
      refreshUnread();
    } catch (error) {
      console.error('Error marcando como leída', error);
    }
  };

  const confirmClearAll = () => {
    setModalState({
      isOpen: true,
      message: '¿Seguro que deseas eliminar todas las notificaciones?',
      onConfirm: async () => {
        setModalState((prev) => ({ ...prev, isOpen: false }));
        try {
          await notificationsApi.clearAll();
          setNotifications([]);
          refreshUnread();
        } catch (error) {
          console.error('Error eliminando notificaciones', error);
          alert('No se pudieron eliminar las notificaciones');
        }
      },
    });
  };

  const confirmDelete = (id: string) => {
    setModalState({
      isOpen: true,
      message: '¿Seguro que deseas eliminar esta notificación?',
      onConfirm: async () => {
        setModalState((prev) => ({ ...prev, isOpen: false }));
        try {
          await notificationsApi.deleteNotification(id);
          setNotifications((prev) => prev.filter((n) => n.id !== id));
          refreshUnread();
        } catch (error) {
          console.error('Error eliminando notificación', error);
          alert('No se pudo eliminar la notificación');
        }
      }
    });
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
            <button className="btn-clear" onClick={confirmClearAll}>
              Limpiar todo
            </button>
          )
        }
      />

      {notifications.length === 0 ? (
        <EmptyState message="No tienes notificaciones." />
      ) : (
        <div className="notifications-list">
          {notifications.map((notification) => (
            <NotificationItem
              key={notification.id}
              notification={notification}
              onMarkAsRead={handleMarkAsRead}
              onDelete={confirmDelete}
            />
          ))}
        </div>
      )}

      {modalState.isOpen && (
        <ConfirmModal
          message={modalState.message}
          onConfirm={modalState.onConfirm}
          onCancel={() => setModalState((prev) => ({ ...prev, isOpen: false }))}
        />
      )}
    </div>
  );
};

export default NotificationList;
