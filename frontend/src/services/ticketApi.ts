import type { Ticket, CreateTicketDTO, TicketPriority } from '../types/ticket';
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
   * Obtener un ticket por id
   */
  getTicket: async (id: number): Promise<Ticket> => {
    const { data } = await ticketApiClient.get<Ticket>(`/tickets/${id}/`);
    return data;
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
};