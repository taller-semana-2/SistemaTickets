/**
 * RED tests — HU-1.2: Visualizar prioridad en listado (TicketItem)
 *
 * Estos tests deben fallar hasta que TicketItem implemente la
 * visualización de prioridad.
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import TicketItem from '../../pages/tickets/TicketItem';
import type { Ticket, TicketPriority } from '../../types/ticket';

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
    const ticketWithPriority: Ticket = { ...baseTicket, priority: 'HIGH' as TicketPriority };

    render(
      <TicketItem
        ticket={ticketWithPriority}
        onDelete={noop}
        onUpdateStatus={noop}
      />
    );

    expect(screen.getByText('High')).toBeInTheDocument();
  });

  it('muestra "Low" cuando priority === "LOW"', () => {
    const ticketWithPriority: Ticket = { ...baseTicket, priority: 'LOW' as TicketPriority };

    render(
      <TicketItem
        ticket={ticketWithPriority}
        onDelete={noop}
        onUpdateStatus={noop}
      />
    );

    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  it('muestra "Medium" cuando priority === "MEDIUM"', () => {
    const ticketWithPriority: Ticket = { ...baseTicket, priority: 'MEDIUM' as TicketPriority };

    render(
      <TicketItem
        ticket={ticketWithPriority}
        onDelete={noop}
        onUpdateStatus={noop}
      />
    );

    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('muestra "Unassigned" cuando priority === "UNASSIGNED"', () => {
    const ticketWithPriority: Ticket = { ...baseTicket, priority: 'UNASSIGNED' as TicketPriority };

    render(
      <TicketItem
        ticket={ticketWithPriority}
        onDelete={noop}
        onUpdateStatus={noop}
      />
    );

    expect(screen.getByText('Unassigned')).toBeInTheDocument();
  });
});
