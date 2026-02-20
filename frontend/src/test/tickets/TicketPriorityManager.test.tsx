/**
 * RED tests — HU-2.x: Gestión manual de prioridad por Administrador
 *
 * Tests escritos ANTES de implementar el componente TicketPriorityManager.
 * TODOS deben fallar hasta que el componente esté creado (fase GREEN).
 *
 * Componente esperado : TicketPriorityManager
 * Ruta esperada       : frontend/src/pages/tickets/TicketPriorityManager.tsx
 *
 * Props esperadas:
 *   - ticket   : Ticket
 *   - onUpdate : (updated: Ticket) => void
 *
 * API nueva requerida : ticketApi.updatePriority(id, { priority, justification? })
 *
 * Mocks:
 *   - ticketApi.getTicket
 *   - ticketApi.updatePriority
 *   - authService.getCurrentUser
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TicketPriorityManager from '../../pages/tickets/TicketPriorityManager';
import * as ticketApiModule from '../../services/ticketApi';
import * as authModule from '../../services/auth';
import type { Ticket } from '../../types/ticket';
import type { User } from '../../types/auth';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------
vi.mock('../../services/ticketApi', () => ({
  ticketApi: {
    getTickets: vi.fn(),
    createTicket: vi.fn(),
    deleteTicket: vi.fn(),
    updateStatus: vi.fn(),
    getTicket: vi.fn(),
    updatePriority: vi.fn(), // método nuevo — no existe aún en producción
  },
}));

vi.mock('../../services/auth', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    isAdmin: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    isAuthenticated: vi.fn(),
  },
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------
const adminUser: User = {
  id: '1',
  email: 'admin@example.com',
  username: 'admin',
  role: 'ADMIN',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

const regularUser: User = {
  id: '2',
  email: 'user@example.com',
  username: 'regularuser',
  role: 'USER',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
};

const makeTicket = (overrides: Partial<Ticket> = {}): Ticket => ({
  id: 42,
  title: 'Bug crítico en login',
  description: 'Descripción del bug',
  status: 'OPEN',
  user_id: '99',
  created_at: '2026-02-20T09:00:00Z',
  priority: 'UNASSIGNED',
  priority_justification: null,
  ...overrides,
});

const noop = vi.fn();

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe('TicketPriorityManager — gestión manual de prioridad (HU-2.x)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── Test 1 ──────────────────────────────────────────────────────────────
  describe('1. ADMIN + OPEN → cambia a HIGH y la UI actualiza', () => {
    it('llama a ticketApi.updatePriority con la prioridad seleccionada', async () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'UNASSIGNED' });
      const updatedTicket: Ticket = { ...ticket, priority: 'HIGH' };

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);
      vi.mocked(ticketApiModule.ticketApi.updatePriority).mockResolvedValue(updatedTicket);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      // El selector de prioridad debe estar visible para ADMIN
      const select = screen.getByRole('combobox', { name: /prioridad/i });
      await userEvent.selectOptions(select, 'HIGH');

      const submitBtn = screen.getByRole('button', { name: /guardar/i });
      await userEvent.click(submitBtn);

      await waitFor(() => {
        expect(ticketApiModule.ticketApi.updatePriority).toHaveBeenCalledWith(
          42,
          expect.objectContaining({ priority: 'HIGH' })
        );
      });
    });

    it('llama a onUpdate con el ticket actualizado tras respuesta exitosa', async () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'UNASSIGNED' });
      const updatedTicket: Ticket = { ...ticket, priority: 'HIGH' };
      const onUpdate = vi.fn();

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);
      vi.mocked(ticketApiModule.ticketApi.updatePriority).mockResolvedValue(updatedTicket);

      render(<TicketPriorityManager ticket={ticket} onUpdate={onUpdate} />);

      const select = screen.getByRole('combobox', { name: /prioridad/i });
      await userEvent.selectOptions(select, 'HIGH');

      await userEvent.click(screen.getByRole('button', { name: /guardar/i }));

      await waitFor(() => {
        expect(onUpdate).toHaveBeenCalledWith(updatedTicket);
      });
    });
  });

  // ── Test 2 ──────────────────────────────────────────────────────────────
  describe('2. ADMIN + prioridad MEDIUM intenta volver a UNASSIGNED → bloqueado', () => {
    it('no expone UNASSIGNED como opción disponible si la prioridad actual no es UNASSIGNED', () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'MEDIUM' });

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      const select = screen.getByRole('combobox', { name: /prioridad/i });
      const optionValues = Array.from(select.querySelectorAll('option')).map(
        (o) => (o as HTMLOptionElement).value
      );

      expect(optionValues).not.toContain('UNASSIGNED');
    });

    it('no llama a ticketApi.updatePriority si se intenta forzar UNASSIGNED con otra prioridad activa', async () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'MEDIUM' });

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);
      vi.mocked(ticketApiModule.ticketApi.updatePriority).mockResolvedValue(ticket);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      // Intentar forzar el valor UNASSIGNED mediante fireEvent (bypass del DOM)
      const select = screen.getByRole('combobox', { name: /prioridad/i });
      fireEvent.change(select, { target: { value: 'UNASSIGNED' } });

      await userEvent.click(screen.getByRole('button', { name: /guardar/i }));

      expect(ticketApiModule.ticketApi.updatePriority).not.toHaveBeenCalled();
    });
  });

  // ── Test 3 ──────────────────────────────────────────────────────────────
  describe('3. USER normal no puede gestionar la prioridad', () => {
    it('no renderiza el control de prioridad para un usuario con rol USER', () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'UNASSIGNED' });

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(regularUser);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      expect(
        screen.queryByRole('combobox', { name: /prioridad/i })
      ).not.toBeInTheDocument();
    });

    it('no renderiza el botón guardar para un usuario con rol USER', () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'UNASSIGNED' });

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(regularUser);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      expect(
        screen.queryByRole('button', { name: /guardar/i })
      ).not.toBeInTheDocument();
    });

    it('no renderiza el control de prioridad cuando no hay usuario autenticado', () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'UNASSIGNED' });

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(null);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      expect(
        screen.queryByRole('combobox', { name: /prioridad/i })
      ).not.toBeInTheDocument();
    });
  });

  // ── Test 4 ──────────────────────────────────────────────────────────────
  describe('4. Ticket CLOSED bloquea el cambio de prioridad', () => {
    it('no renderiza el control de prioridad si el ticket está CLOSED', () => {
      const ticket = makeTicket({ status: 'CLOSED', priority: 'LOW' });

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      expect(
        screen.queryByRole('combobox', { name: /prioridad/i })
      ).not.toBeInTheDocument();
    });

    it('no renderiza el botón guardar si el ticket está CLOSED', () => {
      const ticket = makeTicket({ status: 'CLOSED', priority: 'LOW' });

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      expect(
        screen.queryByRole('button', { name: /guardar/i })
      ).not.toBeInTheDocument();
    });

    it('no llama a ticketApi.updatePriority cuando el ticket está CLOSED', () => {
      const ticket = makeTicket({ status: 'CLOSED', priority: 'LOW' });

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      expect(ticketApiModule.ticketApi.updatePriority).not.toHaveBeenCalled();
    });
  });

  // ── Test 5 ──────────────────────────────────────────────────────────────
  describe('5. Cambio con justificación → se envía en la petición y se notifica al padre', () => {
    it('incluye la justificación en el payload cuando se rellena el campo', async () => {
      const ticket = makeTicket({ status: 'IN_PROGRESS', priority: 'LOW' });
      const updatedTicket: Ticket = {
        ...ticket,
        priority: 'HIGH',
        priority_justification: 'Impacta a cliente VIP',
      };

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);
      vi.mocked(ticketApiModule.ticketApi.updatePriority).mockResolvedValue(updatedTicket);

      const onUpdate = vi.fn();
      render(<TicketPriorityManager ticket={ticket} onUpdate={onUpdate} />);

      const select = screen.getByRole('combobox', { name: /prioridad/i });
      await userEvent.selectOptions(select, 'HIGH');

      const justificationInput = screen.getByRole('textbox', {
        name: /justificaci[oó]n/i,
      });
      await userEvent.type(justificationInput, 'Impacta a cliente VIP');

      await userEvent.click(screen.getByRole('button', { name: /guardar/i }));

      await waitFor(() => {
        expect(ticketApiModule.ticketApi.updatePriority).toHaveBeenCalledWith(42, {
          priority: 'HIGH',
          justification: 'Impacta a cliente VIP',
        });
      });
    });

    it('notifica al padre con la justificación incluida en el ticket actualizado', async () => {
      const ticket = makeTicket({ status: 'IN_PROGRESS', priority: 'LOW' });
      const updatedTicket: Ticket = {
        ...ticket,
        priority: 'HIGH',
        priority_justification: 'Impacta a cliente VIP',
      };

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);
      vi.mocked(ticketApiModule.ticketApi.updatePriority).mockResolvedValue(updatedTicket);

      const onUpdate = vi.fn();
      render(<TicketPriorityManager ticket={ticket} onUpdate={onUpdate} />);

      const select = screen.getByRole('combobox', { name: /prioridad/i });
      await userEvent.selectOptions(select, 'HIGH');

      const justificationInput = screen.getByRole('textbox', {
        name: /justificaci[oó]n/i,
      });
      await userEvent.type(justificationInput, 'Impacta a cliente VIP');

      await userEvent.click(screen.getByRole('button', { name: /guardar/i }));

      await waitFor(() => {
        expect(onUpdate).toHaveBeenCalledWith(
          expect.objectContaining({
            priority_justification: 'Impacta a cliente VIP',
          })
        );
      });
    });
  });

  // ── Test 6 ──────────────────────────────────────────────────────────────
  describe('6. Cambio sin justificación → funciona correctamente', () => {
    it('llama a updatePriority sin campo justification cuando el textarea está vacío', async () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'UNASSIGNED' });
      const updatedTicket: Ticket = { ...ticket, priority: 'LOW' };

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);
      vi.mocked(ticketApiModule.ticketApi.updatePriority).mockResolvedValue(updatedTicket);

      const onUpdate = vi.fn();
      render(<TicketPriorityManager ticket={ticket} onUpdate={onUpdate} />);

      const select = screen.getByRole('combobox', { name: /prioridad/i });
      await userEvent.selectOptions(select, 'LOW');

      // No rellenar justificación
      await userEvent.click(screen.getByRole('button', { name: /guardar/i }));

      await waitFor(() => {
        expect(ticketApiModule.ticketApi.updatePriority).toHaveBeenCalledWith(42, {
          priority: 'LOW',
        });
      });
    });

    it('llama a onUpdate con el ticket actualizado aunque no haya justificación', async () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'UNASSIGNED' });
      const updatedTicket: Ticket = { ...ticket, priority: 'LOW' };

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);
      vi.mocked(ticketApiModule.ticketApi.updatePriority).mockResolvedValue(updatedTicket);

      const onUpdate = vi.fn();
      render(<TicketPriorityManager ticket={ticket} onUpdate={onUpdate} />);

      const select = screen.getByRole('combobox', { name: /prioridad/i });
      await userEvent.selectOptions(select, 'LOW');

      await userEvent.click(screen.getByRole('button', { name: /guardar/i }));

      await waitFor(() => {
        expect(onUpdate).toHaveBeenCalledWith(updatedTicket);
      });
    });
  });

  // ── Test 7 ──────────────────────────────────────────────────────────────
  describe('7. Manejo de errores HTTP 400 y 403', () => {
    it('muestra un div de error rojo (role=alert) cuando updatePriority responde 403', async () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'UNASSIGNED' });
      const axiosError = Object.assign(new Error('Forbidden'), {
        response: { status: 403 },
      });

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);
      vi.mocked(ticketApiModule.ticketApi.updatePriority).mockRejectedValue(axiosError);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      await userEvent.selectOptions(
        screen.getByRole('combobox', { name: /prioridad/i }),
        'HIGH'
      );
      await userEvent.click(screen.getByRole('button', { name: /guardar/i }));

      await waitFor(() => {
        const errorDiv = screen.getByRole('alert');
        expect(errorDiv).toBeInTheDocument();
        expect(errorDiv).toHaveStyle({ color: '#dc2626' });
      });
    });

    it('muestra un div de error rojo (role=alert) cuando updatePriority responde 400', async () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'UNASSIGNED' });
      const axiosError = Object.assign(new Error('Bad Request'), {
        response: { status: 400 },
      });

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);
      vi.mocked(ticketApiModule.ticketApi.updatePriority).mockRejectedValue(axiosError);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      await userEvent.selectOptions(
        screen.getByRole('combobox', { name: /prioridad/i }),
        'HIGH'
      );
      await userEvent.click(screen.getByRole('button', { name: /guardar/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    it('no muestra div de error cuando la operación es exitosa', async () => {
      const ticket = makeTicket({ status: 'OPEN', priority: 'UNASSIGNED' });
      const updatedTicket: Ticket = { ...ticket, priority: 'HIGH' };

      vi.mocked(authModule.authService.getCurrentUser).mockReturnValue(adminUser);
      vi.mocked(ticketApiModule.ticketApi.updatePriority).mockResolvedValue(updatedTicket);

      render(<TicketPriorityManager ticket={ticket} onUpdate={noop} />);

      await userEvent.selectOptions(
        screen.getByRole('combobox', { name: /prioridad/i }),
        'HIGH'
      );
      await userEvent.click(screen.getByRole('button', { name: /guardar/i }));

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });
});
