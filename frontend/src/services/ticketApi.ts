import type { Ticket, CreateTicketDTO, TicketPriority, TicketResponse } from '../types/ticket';
import { ticketApiClient } from './axiosConfig';

/** Payload para actualizar la prioridad de un ticket. */
export interface UpdatePriorityDTO {
  priority: TicketPriority;
  justification?: string;
}

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
  getTicket: async (id: string | number): Promise<Ticket> => {
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
  updateStatus: async (id: string | number, status: string): Promise<Ticket> => {
    const { data } = await ticketApiClient.patch<Ticket>(
      `/tickets/${id}/status/`,
      { status }
    );
    return data;
  },

  /**
   * Actualizar la prioridad de un ticket (solo ADMIN, estado OPEN o IN_PROGRESS).
   *
   * @param id      - ID del ticket
   * @param payload - Prioridad nueva y justificación opcional
   */
  updatePriority: async (id: number, payload: UpdatePriorityDTO): Promise<Ticket> => {
    const { data } = await ticketApiClient.patch<Ticket>(
      `/tickets/${id}/priority/`,
      payload
    );
    return data;
  },

  /**
   * Create an admin response on a ticket.
   * @param ticketId - Target ticket ID
   * @param text - Response text
   * @param adminId - Admin user ID (from useAuth context)
   */
  createResponse: async (ticketId: number, text: string, adminId: string): Promise<TicketResponse> => {
    const { data } = await ticketApiClient.post<TicketResponse>(
      `/tickets/${ticketId}/responses/`,
      { text, admin_id: adminId }
    );
    return data;
  },
};