export interface Assignment {
  id: number;
  ticket_id: string;
  priority: string;
  assigned_at: string;
}

export interface CreateAssignmentDTO {
  ticket_id: string;
  priority: string;
}
