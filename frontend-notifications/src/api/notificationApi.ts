import type NotificationApi from '../interface/NotificationApi';
import type Notification from '../interface/Notification';
import { adaptNotification } from '../adapters/notificationAdapter';

const API_URL = 'http://localhost:8001/api/notifications/';

export const notificationsApi = {
  /**
   * Obtiene todas las notificaciones
   */
  async getNotifications(): Promise<Notification[]> {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error('Error al obtener las notificaciones');
    }

    const data: NotificationApi[] = await response.json();

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
