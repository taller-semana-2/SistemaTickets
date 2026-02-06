import type Assignment from '../interface/Assignment';
import type AssignmentApi from '../interface/AssignmentApi';

export const adaptAssignment = (api: AssignmentApi): Assignment => ({
  id: String(api.id),
  ticketId: api.ticket_id,
  title: `Ticket #${api.ticket_id} asignado`,
  priority: api.priority,
  createdAt: api.assigned_at,
});