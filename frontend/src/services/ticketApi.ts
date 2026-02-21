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
  getTickets: async (signal?: AbortSignal): Promise<Ticket[]> => {
    const { data } = await ticketApiClient.get<Ticket[]>('/tickets/', { signal });
    return data;
  },

  /**
   * Obtener un ticket por ID
   */
  getTicket: async (id: number, signal?: AbortSignal): Promise<Ticket> => {
    const { data } = await ticketApiClient.get<Ticket>(`/tickets/${id}/`, { signal });
    return data;
  },

  /**
   * Obtener respuestas de un ticket ordenadas cronológicamente (ascendente)
   */
  getResponses: async (ticketId: number, signal?: AbortSignal): Promise<TicketResponse[]> => {
    const { data } = await ticketApiClient.get<TicketResponse[]>(
      `/tickets/${ticketId}/responses/`,
      { signal }
    );
    return data;
  },

  /**
   * Crear un nuevo ticket
   */
  createTicket: async (ticketData: CreateTicketDTO, signal?: AbortSignal): Promise<Ticket> => {
    const { data } = await ticketApiClient.post<Ticket>('/tickets/', ticketData, { signal });
    return data;
  },

  /**
   * Eliminar un ticket
   */
  deleteTicket: async (id: number, signal?: AbortSignal): Promise<void> => {
    await ticketApiClient.delete(`/tickets/${id}/`, { signal });
  },

  /**
   * Actualizar el estado de un ticket
   */
  updateStatus: async (id: number, status: string, signal?: AbortSignal): Promise<Ticket> => {
    const { data } = await ticketApiClient.patch<Ticket>(
      `/tickets/${id}/status/`,
      { status },
      { signal }
    );
    return data;
  },

  /**
   * Actualizar la prioridad de un ticket (solo ADMIN, estado OPEN o IN_PROGRESS).
   *
   * @param id      - ID del ticket
   * @param payload - Prioridad nueva y justificación opcional
   */
  updatePriority: async (id: number, payload: UpdatePriorityDTO, signal?: AbortSignal): Promise<Ticket> => {
    const { data } = await ticketApiClient.patch<Ticket>(
      `/tickets/${id}/priority/`,
      payload,
      { signal }
    );
    return data;
  },

  /**
   * Crear una respuesta de administrador a un ticket.
   * POST /tickets/:id/responses/
   * Incluye admin_id desde la sesión activa para respetar el contrato del
   * serializer del backend (`admin_id` requerido).
   */
  createResponse: async (ticketId: number, text: string, signal?: AbortSignal): Promise<TicketResponse> => {
    // El admin_id viene de la sesión activa; el backend también lo recibe
    // vía cabecera X-User-Id pero el serializer lo espera en el cuerpo.
    const raw = localStorage.getItem('ticketSystem_user');
    const adminId: string = raw ? (JSON.parse(raw) as { id?: string }).id ?? '' : '';
    const { data } = await ticketApiClient.post<TicketResponse>(
      `/tickets/${ticketId}/responses/`,
      { text, admin_id: adminId },
      { signal }
    );
    return data;
  },
};