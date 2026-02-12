import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AssignmentList from '../../pages/assignments/AssignmentList';
import { assignmentsApi } from '../../services/assignment';

// Mock the API
vi.mock('../../services/assignment', () => ({
  assignmentsApi: {
    getAssignments: vi.fn(),
    deleteAssignment: vi.fn(),
  },
}));

// Mock common components
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

const mockAssignments = [
  {
    id: 1,
    ticket_id: 100,
    user_id: 1,
    priority: 'HIGH',
    assigned_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 2,
    ticket_id: 101,
    user_id: 1,
    priority: 'MEDIUM',
    assigned_at: '2024-01-14T10:00:00Z',
  },
];

describe('AssignmentList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    vi.mocked(assignmentsApi.getAssignments).mockImplementation(() => new Promise(() => {}));

    render(
      <BrowserRouter>
        <AssignmentList />
      </BrowserRouter>
    );

    expect(screen.getByTestId('loading-state')).toBeInTheDocument();
  });

  it('displays assignments after loading', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue(mockAssignments);

    render(
      <BrowserRouter>
        <AssignmentList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Ticket #100')).toBeInTheDocument();
      expect(screen.getByText('Ticket #101')).toBeInTheDocument();
    });
  });

  it('shows empty state when no assignments', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue([]);

    render(
      <BrowserRouter>
        <AssignmentList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });
  });

  it('displays correct assignment count in header', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue(mockAssignments);

    render(
      <BrowserRouter>
        <AssignmentList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/2 tareas/i)).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(assignmentsApi.getAssignments).mockRejectedValue(new Error('API Error'));

    render(
      <BrowserRouter>
        <AssignmentList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('displays priority badges correctly', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue(mockAssignments);

    render(
      <BrowserRouter>
        <AssignmentList />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('HIGH')).toBeInTheDocument();
      expect(screen.getByText('MEDIUM')).toBeInTheDocument();
    });
  });
});
