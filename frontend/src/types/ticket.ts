export type TicketStatus = 'OPEN' | 'IN_PROGRESS' | 'CLOSED';

export type TicketPriority = 'Unassigned' | 'Low' | 'Medium' | 'High';

export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: TicketStatus;
  user_id: string;
  created_at: string;
  priority?: TicketPriority;
  priority_justification?: string | null;
}

export interface CreateTicketDTO {
  title: string;
  description: string;
  user_id: string;
}


/**
 * Respuesta de un administrador a un ticket.
 * Contrato alineado con el evento ticket.response_added (ver USER_STORY_NOTIFICATION.md §6.1).
 */
export interface TicketResponse {
  id: number;
  ticket_id: number;
  admin_id: string;
  admin_name: string;
  text: string;
  created_at: string;
}