export default interface AssignmentApi {
  id: number;
  ticket_id: string;
  priority: 'low' | 'medium' | 'high';
  assigned_at: string;
}