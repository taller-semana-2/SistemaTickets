import type { Ticket, CreateTicketDTO } from '../types/ticket';

const API_URL = 'http://localhost:8000/api/tickets/';

export const ticketApi = {
  /**
   * Obtener todos los tickets
   */
  getTickets: async (): Promise<Ticket[]> => {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error('Error al obtener los tickets');
    }

    const data: Ticket[] = await response.json();
    return data;
  },

  /**
   * Crear un nuevo ticket
   */
  createTicket: async (data: CreateTicketDTO): Promise<Ticket> => {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Error al crear el ticket');
    }

    const newTicket: Ticket = await response.json();
    return newTicket;
  },
};
