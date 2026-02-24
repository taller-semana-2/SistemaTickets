import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AssignmentList from '../../pages/assignments/AssignmentList';
import { assignmentsApi } from '../../services/assignment';
import { ticketApi } from '../../services/ticketApi';
import { userService } from '../../services/user';

// Mock de la API de asignaciones
vi.mock('../../services/assignment', () => ({
  assignmentsApi: {
    getAssignments: vi.fn(),
    assignUser: vi.fn(),
    deleteAssignment: vi.fn(),
  },
}));

// Mock de la API de tickets
vi.mock('../../services/ticketApi', () => ({
  ticketApi: {
    getTickets: vi.fn(),
    getTicket: vi.fn(),
    updateStatus: vi.fn(),
  },
}));

// Mock del servicio de usuarios
vi.mock('../../services/user', () => ({
  userService: {
    getAdminUsers: vi.fn(),
  },
}));

// Mock de componentes comunes
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

// Mock de componentes secundarios
vi.mock('../../components/TicketAssign', () => ({
  default: () => <div data-testid="ticket-assign" />,
}));
vi.mock('../../components/ConfirmModal', () => ({
  default: () => <div data-testid="confirm-modal" />,
}));

const mockAssignments = [
  {
    id: 1,
    ticket_id: '100',
    priority: 'HIGH',
    assigned_at: '2024-01-15T10:00:00Z',
    assigned_to: 'agent-1',
  },
  {
    id: 2,
    ticket_id: '101',
    priority: 'MEDIUM',
    assigned_at: '2024-01-14T10:00:00Z',
    assigned_to: undefined,
  },
];

const mockTickets = [
  { id: 100, title: 'Error en login', description: 'desc', status: 'OPEN', user_id: '1', created_at: '2024-01-15T10:00:00Z' },
  { id: 101, title: 'Pérdida de datos', description: 'desc', status: 'IN_PROGRESS', user_id: '2', created_at: '2024-01-14T10:00:00Z' },
];

const mockAdminUsers = [
  { id: 'agent-1', username: 'carlos.gomez', email: 'c@test.com', role: 'ADMIN', is_active: true },
];

const renderComponent = () =>
  render(
    <BrowserRouter>
      <AssignmentList />
    </BrowserRouter>
  );

describe('AssignmentList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(ticketApi.getTickets).mockResolvedValue(mockTickets as never);
    vi.mocked(userService.getAdminUsers).mockResolvedValue(mockAdminUsers);
  });

  it('muestra estado de carga inicialmente', () => {
    vi.mocked(assignmentsApi.getAssignments).mockImplementation(() => new Promise(() => {}));
    renderComponent();
    expect(screen.getByTestId('loading-state')).toBeInTheDocument();
  });

  it('muestra el título del ticket en la tarjeta (no solo el ID)', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue(mockAssignments);
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Error en login')).toBeInTheDocument();
      expect(screen.getByText('Pérdida de datos')).toBeInTheDocument();
    });
  });

  it('muestra el badge #id junto al título', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue(mockAssignments);
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('#100')).toBeInTheDocument();
      expect(screen.getByText('#101')).toBeInTheDocument();
    });
  });

  it('muestra prioridad en español (Alta, Media)', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue(mockAssignments);
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Alta')).toBeInTheDocument();
      expect(screen.getByText('Media')).toBeInTheDocument();
    });
  });

  it('muestra nombre del agente cuando el ticket está asignado', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue(mockAssignments);
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('Asignación: carlos.gomez')).toBeInTheDocument();
    });
  });

  it('muestra "No asignado" cuando el ticket no tiene agente', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue(mockAssignments);
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText('No asignado')).toBeInTheDocument();
    });
  });

  it('muestra estado vacío cuando no hay asignaciones', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue([]);
    renderComponent();
    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });
  });

  it('muestra el contador correcto de tareas en el header', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue(mockAssignments);
    renderComponent();
    await waitFor(() => {
      expect(screen.getByText(/2 tareas/i)).toBeInTheDocument();
    });
  });

  it('maneja errores de API sin crashear', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(assignmentsApi.getAssignments).mockRejectedValue(new Error('API Error'));
    renderComponent();
    await waitFor(() => {
      expect(screen.queryByTestId('loading-state')).not.toBeInTheDocument();
    });
    consoleSpy.mockRestore();
  });

  it('sigue funcionando si el servicio de usuarios falla', async () => {
    vi.mocked(assignmentsApi.getAssignments).mockResolvedValue(mockAssignments);
    vi.mocked(userService.getAdminUsers).mockRejectedValue(new Error('Users service down'));
    renderComponent();
    // Debe mostrar los tickets aunque no se resuelva el nombre del agente
    await waitFor(() => {
      expect(screen.getByText('Error en login')).toBeInTheDocument();
    });
  });
});
