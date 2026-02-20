import type { Ticket, CreateTicketDTO, TicketResponse } from '../types/ticket';
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
   * Obtener un ticket por ID
   */
  getTicket: async (id: number): Promise<Ticket> => {
    const { data } = await ticketApiClient.get<Ticket>(`/tickets/${id}/`);
    return data;
  },

  /**
   * Obtener respuestas de un ticket ordenadas cronológicamente (ascendente)
   */
  getResponses: async (ticketId: number): Promise<TicketResponse[]> => {
    const { data } = await ticketApiClient.get<TicketResponse[]>(
      `/tickets/${ticketId}/responses/`
    );
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

  /**
   * Crear una respuesta de administrador a un ticket.
   * POST /tickets/:id/responses/
   */
  createResponse: async (ticketId: number, text: string): Promise<TicketResponse> => {
    const { data } = await ticketApiClient.post<TicketResponse>(
      `/tickets/${ticketId}/responses/`,
      { text }
    );
    return data;
  },
};