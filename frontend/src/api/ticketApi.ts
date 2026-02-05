import type { Ticket } from '../types/ticket';
import type { CreateTicketDTO } from '../types/ticket';

//para cuando tengamos los endpoints realeas 
// Cambias setTimeout por fetch / axios
// Mantienes mismos métodos y tipos

let tickets: Ticket[] = [
  {
    id: 1,
    title: 'Error en login',
    description: 'El usuario no puede iniciar sesión',
    status: 'open',
    createdAt: new Date().toISOString(),
  },
  {
    id: 2,
    title: 'Pantalla en blanco',
    description: 'La app no carga en producción',
    status: 'in_progress',
    createdAt: new Date().toISOString(),
  },
];

export const ticketApi = {
  getTickets: async (): Promise<Ticket[]> => {
    return new Promise((resolve) => {
      setTimeout(() => resolve(tickets), 500);
    });
  },

  createTicket: async (data: CreateTicketDTO): Promise<Ticket> => {
    return new Promise((resolve) => {
      setTimeout(() => {
        const newTicket: Ticket = {
          id: tickets.length + 1,
          status: 'open',
          createdAt: new Date().toISOString(),
          ...data,
        };

        tickets.push(newTicket);
        resolve(newTicket);
      }, 500);
    });
  },
};
