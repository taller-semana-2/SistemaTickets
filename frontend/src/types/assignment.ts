export interface Assignment {
  id: number;
  ticket_id: string;
  priority: string;
  assigned_at: string;
  assigned_to?: string;
}

export interface CreateAssignmentDTO {
  ticket_id: string;
  priority: string;
  assigned_to?: string;
}

export interface UpdateAssignedUserDTO {
  assigned_to: string;
}
