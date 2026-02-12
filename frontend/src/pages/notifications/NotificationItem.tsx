import type { Notification } from '../../types/notification';
import './NotificationItem.css';

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: string) => void;
  onDelete: (id: string) => void;
}

const NotificationItem = ({
  notification,
  onMarkAsRead,
  onDelete,
}: NotificationItemProps) => {
  const { id, title, message, read, createdAt } = notification;

  return (
    <div className={`notification-item ${read ? 'read' : 'unread'}`}>
      <div className="notification-content">
        <div className="notification-header">
          <h4 className="notification-title">{title}</h4>
        </div>

        <p className="notification-description">{message}</p>

        <div className="notification-footer">
          <div className="time-info">
            <span className="calendar-icon">📅</span>
            <small className="time-text">
              {new Date(createdAt).toLocaleString([], {
                hour: '2-digit',
                minute: '2-digit',
                day: '2-digit',
                month: '2-digit',
              })}
            </small>
          </div>

          <div className="actions">
            {!read && (
              <button
                className="btn-read"
                onClick={() => onMarkAsRead(id)}
              >
                Marcar como leída
              </button>
            )}

            <button
              className="btn-delete"
              onClick={() => onDelete(id)}
            >
              Eliminar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationItem;
