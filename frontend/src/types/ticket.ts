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


// tener en cuenta que este tipo es un placeholder, ya que depende de lo que se cree en el backend