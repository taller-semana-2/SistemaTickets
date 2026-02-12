import type { Notification } from '../types/notification';

// Backend API structure
interface NotificationApiResponse {
  id: number;
  ticket_id: string;
  message: string;
  sent_at: string;
  read: boolean;
}

const API_URL = 'http://localhost:8001/api/notifications/';

// Adapter function
const adaptNotification = (apiData: NotificationApiResponse): Notification => ({
  id: apiData.id.toString(),
  title: `Ticket #${apiData.ticket_id}`,
  message: apiData.message,
  read: apiData.read,
  createdAt: apiData.sent_at,
});

export const notificationsApi = {
  async getNotifications(): Promise<Notification[]> {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error('Error al obtener las notificaciones');
    }

    const data: NotificationApiResponse[] = await response.json();
    return data.map(adaptNotification);
  },

  async markAsRead(id: string): Promise<void> {
    const response = await fetch(`${API_URL}${id}/read/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Error al marcar la notificación como leída');
    }
  },

  async clearAll(): Promise<void> {
    const response = await fetch(`${API_URL}clear/`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Error al eliminar las notificaciones');
    }
  },

  async deleteNotification(id: string): Promise<void> {
    const response = await fetch(`${API_URL}${id}/`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Error al eliminar la notificación');
    }
  },
};
