export type TicketStatus = 'OPEN' | 'IN_PROGRESS' | 'CLOSED';

export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: TicketStatus;
  createdAt: string;
}

export interface CreateTicketDTO {
  title: string;
  description: string;
}


// tener en cuenta que este tipo es un placeholder, ya que depende de lo que se cree en el backend