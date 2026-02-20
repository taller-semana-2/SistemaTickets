import type { Notification } from '../types/notification';
import { notificationApiClient } from './axiosConfig';

// Backend API structure
interface NotificationApiResponse {
  id: number;
  ticket_id: string;
  message: string;
  sent_at: string;
  read: boolean;
}

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
    const { data } = await notificationApiClient.get<NotificationApiResponse[]>(`/notifications/?t=${new Date().getTime()}`);
    return data.map(adaptNotification);
  },

  async markAsRead(id: string): Promise<void> {
    await notificationApiClient.patch(`/notifications/${id}/read/`);
  },

  async clearAll(): Promise<void> {
    await notificationApiClient.delete('/notifications/clear/');
  },

  async deleteNotification(id: string): Promise<void> {
    await notificationApiClient.delete(`/notifications/${id}/`);
  },
};
