import type { Ticket, CreateTicketDTO } from '../types/ticket';
import { ticketApiClient } from './axiosConfig';

export const ticketApi = {
  /**
   * Obtener todos los tickets
   */
  getTickets: async (): Promise<Ticket[]> => {
    const { data } = await ticketApiClient.get<Ticket[]>('/tickets/');
    return data;
  },

  /**
   * Crear un nuevo ticket
   */
  createTicket: async (ticketData: CreateTicketDTO): Promise<Ticket> => {
    const { data } = await ticketApiClient.post<Ticket>('/tickets/', ticketData);
    return data;
  },

  /**
   * Eliminar un ticket
   */
  deleteTicket: async (id: number): Promise<void> => {
    await ticketApiClient.delete(`/tickets/${id}/`);
  },

  /**
   * Actualizar el estado de un ticket
   */
  updateStatus: async (id: number, status: string): Promise<Ticket> => {
    const { data } = await ticketApiClient.patch<Ticket>(
      `/tickets/${id}/status/`,
      { status }
    );
    return data;
  },
};