/**
 * RED tests — HU-1.2: Visualizar prioridad en detalle (TicketDetail)
 *
 * Estos tests deben fallar hasta que TicketDetail implemente la carga
 * del ticket mediante ticketApi.getTicket y muestre la prioridad.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import TicketDetail from '../../pages/tickets/TicketDetail';
import * as ticketApiModule from '../../services/ticketApi';
import type { TicketPriority } from '../../types/ticket';

// ---------------------------------------------------------------------------
// Mock ticketApi completo — getTicket aún no existe en producción
// ---------------------------------------------------------------------------
vi.mock('../../services/ticketApi', () => ({
  ticketApi: {
    getTickets: vi.fn(),
    createTicket: vi.fn(),
    deleteTicket: vi.fn(),
    updateStatus: vi.fn(),
    getTicket: vi.fn(),   // método que se debe añadir en fase GREEN
  },
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------
const makeTicket = (priority?: TicketPriority) => ({
  id: 7,
  title: 'Fallo en login',
  description: 'El usuario no puede iniciar sesión después del deploy',
  status: 'OPEN' as const,
  user_id: '99',
  created_at: '2026-02-20T09:00:00Z',
  ...(priority !== undefined ? { priority } : {}),
});

/** Helper: renderiza TicketDetail dentro de un router con params */
const renderDetail = () =>
  render(
    <MemoryRouter initialEntries={['/tickets/7']}>
      <Routes>
        <Route path="/tickets/:id" element={<TicketDetail />} />
      </Routes>
    </MemoryRouter>
  );

describe('TicketDetail – visualización de prioridad (HU-1.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('llama a ticketApi.getTicket con el id del ticket', async () => {
    const mockedGetTicket = vi.mocked(ticketApiModule.ticketApi.getTicket);
    mockedGetTicket.mockResolvedValue(makeTicket('HIGH'));

    renderDetail();

    await waitFor(() => {
      expect(mockedGetTicket).toHaveBeenCalledWith(7);
    });
  });

  it('muestra "High" cuando el ticket tiene priority === "HIGH"', async () => {
    vi.mocked(ticketApiModule.ticketApi.getTicket).mockResolvedValue(
      makeTicket('HIGH')
    );

    renderDetail();

    await waitFor(() => {
      expect(screen.getByText('High')).toBeInTheDocument();
    });
  });

  it('muestra "Unassigned" cuando el ticket no tiene prioridad', async () => {
    vi.mocked(ticketApiModule.ticketApi.getTicket).mockResolvedValue(
      makeTicket()
    );

    renderDetail();

    await waitFor(() => {
      expect(screen.getByText('Unassigned')).toBeInTheDocument();
    });
  });

  it('muestra "Low" cuando priority === "LOW"', async () => {
    vi.mocked(ticketApiModule.ticketApi.getTicket).mockResolvedValue(
      makeTicket('LOW')
    );

    renderDetail();

    await waitFor(() => {
      expect(screen.getByText('Low')).toBeInTheDocument();
    });
  });

  it('muestra "Medium" cuando priority === "MEDIUM"', async () => {
    vi.mocked(ticketApiModule.ticketApi.getTicket).mockResolvedValue(
      makeTicket('MEDIUM')
    );

    renderDetail();

    await waitFor(() => {
      expect(screen.getByText('Medium')).toBeInTheDocument();
    });
  });
});
