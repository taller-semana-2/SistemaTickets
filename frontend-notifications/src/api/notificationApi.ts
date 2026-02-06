const API_URL = 'http://localhost:8001/api/notifications/';

export const notificationApi = {
  async getNotifications() {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error('Error obteniendo notificaciones');
    }

    return await response.json();
  },

  async markAsRead(id: string | number) {
    const response = await fetch(`${API_URL}${id}/`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ read: true }),
    });

    if (!response.ok) {
      throw new Error('Error marcando notificación como leída');
    }

    return await response.json();
  },

  async clearAll() {
    const response = await fetch(API_URL, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Error eliminando notificaciones');
    }

    return { success: true };
  },
};
