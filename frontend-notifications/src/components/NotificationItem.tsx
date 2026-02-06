import type Notification from '../interface/Notification';
import './NotificationItem.css';

const NotificationItem = ({ notification, onMarkAsRead }: { notification: Notification; onMarkAsRead: (id: string) => void }) => {
  const { id, title, message, read, createdAt } = notification;

  return (
    <div className={`notification-item ${read ? 'read' : 'unread'}`}>
      <div className="notification-content">
        <div className="notification-header">
          <h4 className="ticket-title">{title}</h4>
        </div>
        
        <p className="ticket-description">{message}</p>

        <div className="ticket-footer">
          <div className="time-info">
            <span className="calendar-icon">📅</span>
            <small className="ticket-status">
              {new Date(createdAt).toLocaleString([], { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })}
            </small>
          </div>
          
          {!read && (
            <button
              className="btn-read"
              onClick={() => onMarkAsRead(id)}
            >
              Marcar como leída
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationItem;
