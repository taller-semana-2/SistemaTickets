/**
 * RED tests — HU-1.2: Visualizar prioridad en listado (TicketItem)
 *
 * Estos tests deben fallar hasta que TicketItem implemente la
 * visualización de prioridad.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import TicketItem from '../../pages/tickets/TicketItem';
import type { Ticket } from '../../types/ticket';

/** Ticket base sin prioridad (campo ausente) */
const baseTicket: Ticket = {
  id: 1,
  title: 'Test ticket',
  description: 'Test description',
  status: 'OPEN',
  user_id: '42',
  created_at: '2026-02-20T10:00:00Z',
};

const noop = vi.fn();

describe('TicketItem – visualización de prioridad (HU-1.2)', () => {
  it('muestra "Unassigned" cuando el ticket no tiene prioridad', () => {
    // El ticket NO incluye el campo priority
    render(
      <TicketItem
        ticket={baseTicket}
        onDelete={noop}
        onUpdateStatus={noop}
      />
    );

    expect(screen.getByText('Unassigned')).toBeInTheDocument();
  });

  it('muestra "High" cuando priority === "HIGH"', () => {
    const ticketWithPriority = {
      ...baseTicket,
      priority: 'HIGH',
    } as Ticket & { priority: string };

    render(
      <TicketItem
        ticket={ticketWithPriority as unknown as Ticket}
        onDelete={noop}
        onUpdateStatus={noop}
      />
    );

    expect(screen.getByText('High')).toBeInTheDocument();
  });

  it('muestra "Low" cuando priority === "LOW"', () => {
    const ticketWithPriority = {
      ...baseTicket,
      priority: 'LOW',
    } as Ticket & { priority: string };

    render(
      <TicketItem
        ticket={ticketWithPriority as unknown as Ticket}
        onDelete={noop}
        onUpdateStatus={noop}
      />
    );

    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  it('muestra "Medium" cuando priority === "MEDIUM"', () => {
    const ticketWithPriority = {
      ...baseTicket,
      priority: 'MEDIUM',
    } as Ticket & { priority: string };

    render(
      <TicketItem
        ticket={ticketWithPriority as unknown as Ticket}
        onDelete={noop}
        onUpdateStatus={noop}
      />
    );

    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('muestra "Unassigned" cuando priority === "UNASSIGNED"', () => {
    const ticketWithPriority = {
      ...baseTicket,
      priority: 'UNASSIGNED',
    } as Ticket & { priority: string };

    render(
      <TicketItem
        ticket={ticketWithPriority as unknown as Ticket}
        onDelete={noop}
        onUpdateStatus={noop}
      />
    );

    expect(screen.getByText('Unassigned')).toBeInTheDocument();
  });
});
