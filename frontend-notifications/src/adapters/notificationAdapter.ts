import type NotificationApi from '../interface/NotificationApi';
import type Notification from '../interface/Notification';


export function adaptNotification(
  apiNotification: NotificationApi
): Notification {
  return {
    id: apiNotification.id.toString(),
    title: `Ticket #${apiNotification.ticket_id}`,
    message: apiNotification.message,
    read: apiNotification.read,
    createdAt: apiNotification.sent_at,
  };
}
