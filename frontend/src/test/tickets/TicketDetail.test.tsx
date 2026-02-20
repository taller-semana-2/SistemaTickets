import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import TicketDetail from '../../pages/tickets/TicketDetail';
import { ticketApi } from '../../services/ticketApi';
import { authService } from '../../services/auth';
import type { Ticket, TicketResponse } from '../../types/ticket';

// ---------------------------------------------------------------------------
// Mocks — same pattern as NotificationList.test.tsx / AssignmentList.test.tsx
// ---------------------------------------------------------------------------

vi.mock('../../services/ticketApi', () => ({
  ticketApi: {
    getTickets: vi.fn(),
    getTicket: vi.fn(),
    getResponses: vi.fn(),
    createTicket: vi.fn(),
    deleteTicket: vi.fn(),
    updateStatus: vi.fn(),
  },
}));

vi.mock('../../services/auth', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    isAuthenticated: vi.fn(),
    isAdmin: vi.fn(),
  },
}));

vi.mock('../../components/common', () => ({
  LoadingState: ({ message }: { message?: string }) => (
    <div data-testid="loading-state">{message || 'Loading...'}</div>
  ),
  EmptyState: ({ message }: { message: string }) => (
    <div data-testid="empty-state">{message}</div>
  ),
  PageHeader: ({ title, subtitle }: { title: string; subtitle?: React.ReactNode }) => (
    <div data-testid="page-header">
      <h1>{title}</h1>
      {subtitle}
    </div>
  ),
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const mockTicket: Ticket = {
  id: 42,
  title: 'Bug en el login',
  description: 'No puedo iniciar sesión',
  status: 'OPEN',
  user_id: 'user-123',
  created_at: '2026-02-10T08:00:00Z',
};

const mockResponses: TicketResponse[] = [
  {
    id: 1,
    ticket_id: 42,
    admin_id: 'admin-001',
    admin_name: 'Admin Uno',
    text: 'Estamos revisando tu caso',
    created_at: '2026-02-11T09:00:00Z',
  },
  {
    id: 2,
    ticket_id: 42,
    admin_id: 'admin-002',
    admin_name: 'Admin Dos',
    text: 'El problema ha sido identificado',
    created_at: '2026-02-12T14:30:00Z',
  },
];

// ---------------------------------------------------------------------------
// Helper — render component inside the /tickets/:id route
// ---------------------------------------------------------------------------

const renderTicketDetail = (ticketId = '42') => {
  return render(
    <MemoryRouter initialEntries={[`/tickets/${ticketId}`]}>
      <Routes>
        <Route path="/tickets/:id" element={<TicketDetail />} />
      </Routes>
    </MemoryRouter>,
  );
};

// ---------------------------------------------------------------------------
// Tests — RED phase (TDD)
// ---------------------------------------------------------------------------

describe('TicketDetail — HU-3.1: Sección Respuestas', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default: authenticated user is the ticket creator
    vi.mocked(authService.getCurrentUser).mockReturnValue({
      id: 'user-123',
      email: 'user@test.com',
      username: 'testuser',
      role: 'USER',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
    });
    vi.mocked(authService.isAuthenticated).mockReturnValue(true);
    vi.mocked(authService.isAdmin).mockReturnValue(false);
  });

  // -----------------------------------------------------------------------
  // Scenario: Detalle muestra respuestas existentes (2 respuestas)
  // -----------------------------------------------------------------------
  describe('cuando hay respuestas', () => {
    beforeEach(() => {
      vi.mocked(ticketApi.getTicket).mockResolvedValue(mockTicket);
      vi.mocked(ticketApi.getResponses).mockResolvedValue(mockResponses);
    });

    it('muestra la sección "Respuestas" con las 2 respuestas', async () => {
      renderTicketDetail();

      await waitFor(() => {
        expect(screen.getByText('Respuestas')).toBeInTheDocument();
      });

      expect(screen.getByText('Estamos revisando tu caso')).toBeInTheDocument();
      expect(screen.getByText('El problema ha sido identificado')).toBeInTheDocument();
    });

    it('muestra el nombre del admin en cada respuesta', async () => {
      renderTicketDetail();

      await waitFor(() => {
        expect(screen.getByText('Admin Uno')).toBeInTheDocument();
        expect(screen.getByText('Admin Dos')).toBeInTheDocument();
      });
    });

    it('muestra las respuestas en orden cronológico ascendente (más antigua primero)', async () => {
      renderTicketDetail();

      await waitFor(() => {
        expect(screen.getByText('Estamos revisando tu caso')).toBeInTheDocument();
      });

      const responseTexts = screen
        .getAllByTestId('response-item')
        .map((el) => el.textContent);

      // La primera respuesta renderizada debe ser la más antigua
      expect(responseTexts[0]).toContain('Estamos revisando tu caso');
      expect(responseTexts[1]).toContain('El problema ha sido identificado');
    });

    it('muestra la fecha de cada respuesta', async () => {
      renderTicketDetail();

      await waitFor(() => {
        // We expect formatted dates to appear — the component may format them,
        // so we check for the year as a minimal assertion.
        const items = screen.getAllByTestId('response-item');
        expect(items[0]).toHaveTextContent(/2026/);
        expect(items[1]).toHaveTextContent(/2026/);
      });
    });
  });

  // -----------------------------------------------------------------------
  // Scenario: Detalle sin respuestas (empty state)
  // -----------------------------------------------------------------------
  describe('cuando no hay respuestas', () => {
    beforeEach(() => {
      vi.mocked(ticketApi.getTicket).mockResolvedValue(mockTicket);
      vi.mocked(ticketApi.getResponses).mockResolvedValue([]);
    });

    it('muestra mensaje de empty state', async () => {
      renderTicketDetail();

      await waitFor(() => {
        expect(
          screen.getByText('Aún no hay respuestas para este ticket'),
        ).toBeInTheDocument();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Scenario: Usuario no creador y no admin → acceso restringido
  // -----------------------------------------------------------------------
  describe('cuando el usuario no es creador ni admin', () => {
    beforeEach(() => {
      vi.mocked(authService.getCurrentUser).mockReturnValue({
        id: 'user-999',
        email: 'otro@test.com',
        username: 'otrousuario',
        role: 'USER',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      });
      vi.mocked(authService.isAdmin).mockReturnValue(false);

      vi.mocked(ticketApi.getTicket).mockResolvedValue(mockTicket);
      // The API might reject, or the component might hide — either way, responses should NOT show
      vi.mocked(ticketApi.getResponses).mockResolvedValue(mockResponses);
    });

    it('no muestra la sección de respuestas', async () => {
      renderTicketDetail();

      await waitFor(() => {
        expect(screen.queryByText('Estamos revisando tu caso')).not.toBeInTheDocument();
        expect(screen.queryByText('El problema ha sido identificado')).not.toBeInTheDocument();
      });
    });

    it('muestra un mensaje de acceso restringido', async () => {
      renderTicketDetail();

      await waitFor(() => {
        expect(
          screen.getByText(/acceso restringido|no tienes permiso/i),
        ).toBeInTheDocument();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Scenario: Admin puede ver respuestas de cualquier ticket
  // -----------------------------------------------------------------------
  describe('cuando el usuario es ADMIN (no creador)', () => {
    beforeEach(() => {
      vi.mocked(authService.getCurrentUser).mockReturnValue({
        id: 'admin-001',
        email: 'admin@test.com',
        username: 'adminuser',
        role: 'ADMIN',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
      });
      vi.mocked(authService.isAdmin).mockReturnValue(true);

      vi.mocked(ticketApi.getTicket).mockResolvedValue(mockTicket);
      vi.mocked(ticketApi.getResponses).mockResolvedValue(mockResponses);
    });

    it('muestra las respuestas aunque no sea el creador', async () => {
      renderTicketDetail();

      await waitFor(() => {
        expect(screen.getByText('Respuestas')).toBeInTheDocument();
        expect(screen.getByText('Estamos revisando tu caso')).toBeInTheDocument();
        expect(screen.getByText('El problema ha sido identificado')).toBeInTheDocument();
      });
    });
  });

  // -----------------------------------------------------------------------
  // Scenario: Loading state mientras carga
  // -----------------------------------------------------------------------
  describe('estado de carga', () => {
    it('muestra loading mientras se obtiene el ticket', () => {
      vi.mocked(ticketApi.getTicket).mockImplementation(() => new Promise(() => {}));
      vi.mocked(ticketApi.getResponses).mockImplementation(() => new Promise(() => {}));

      renderTicketDetail();

      expect(screen.getByTestId('loading-state')).toBeInTheDocument();
    });
  });
});
