let notifications = [
  {
    id: 1,
    title: 'Ticket asignado',
    message: 'Se te asignó el ticket #123',
    read: false,
    createdAt: new Date().toISOString(),
  },
  {
    id: 2,
    title: 'Ticket actualizado',
    message: 'El ticket #122 cambió de estado',
    read: true,
    createdAt: new Date().toISOString(),
  },
];

// simulador de latencia real
const delay = (ms = 500) =>
  new Promise((resolve) => setTimeout(resolve, ms));

export const notificationApi = {
  async getNotifications() {
    await delay();
    return [...notifications];
  },

  async markAsRead(id: number) {
    await delay();

    notifications = notifications.map((n) =>
      n.id === id ? { ...n, read: true } : n
    );

    return { success: true };
  },

  async clearAll() {
    await delay();
    notifications = [];
    return { success: true };
  },
};
