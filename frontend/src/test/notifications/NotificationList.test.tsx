import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import NotificationList from '../../pages/notifications/NotificationList';
import { notificationsApi } from '../../services/notification';

// Mock the API
vi.mock('../../services/notification', () => ({
  notificationsApi: {
    getNotifications: vi.fn(),
    markAsRead: vi.fn(),
    deleteNotification: vi.fn(),
  },
}));

// Mock common components to simplify testing
vi.mock('../../components/common', () => ({
  LoadingState: ({ message }: { message?: string }) => <div data-testid="loading-state">{message || 'Loading...'}</div>,
  EmptyState: ({ message }: { message: string }) => <div data-testid="empty-state">{message}</div>,
  PageHeader: ({ title, subtitle }: { title: string; subtitle?: React.ReactNode }) => (
    <div data-testid="page-header">
      <h1>{title}</h1>
      {subtitle}
    </div>
  ),
}));

const mockNotifications = [
  {
    id: '1',
    title: 'New ticket assigned',
    message: 'New ticket assigned',
    read: false,
    createdAt: '2024-01-15T10:00:00Z',
  },
  {
    id: '2',
    title: 'Ticket status changed',
    message: 'Ticket status changed',
    read: true,
    createdAt: '2024-01-14T10:00:00Z',
  },
];

describe('NotificationList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    vi.mocked(notificationsApi.getNotifications).mockImplementation(() => new Promise(() => {}));
    
    render(
      <BrowserRouter>
        <NotificationList />
      </BrowserRouter>
    );

    expect(screen.getByTestId('loading-state')).toBeInTheDocument();
  });

  it('displays notifications after loading', async () => {
    vi.mocked(notificationsApi.getNotifications).mockResolvedValue(mockNotifications);

    render(
      <BrowserRouter>
        <NotificationList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('New ticket assigned').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Ticket status changed').length).toBeGreaterThan(0);
    });
  });

  it('shows empty state when no notifications', async () => {
    vi.mocked(notificationsApi.getNotifications).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <NotificationList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });
  });

  it('displays correct notification count in header', async () => {
    vi.mocked(notificationsApi.getNotifications).mockResolvedValue(mockNotifications);

    render(
      <BrowserRouter>
        <NotificationList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/2 mensajes/i)).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(notificationsApi.getNotifications).mockRejectedValue(new Error('API Error'));

    render(
      <BrowserRouter>
        <NotificationList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });
});
