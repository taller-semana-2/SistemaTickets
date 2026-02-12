import type { Assignment } from '../types/assignment';
import { assignmentApiClient } from './axiosConfig';

// Backend API structure
interface AssignmentApiResponse {
  id: number;
  ticket_id: string;
  priority: 'low' | 'medium' | 'high';
  assigned_at: string;
}

// Adapter function
const adaptAssignment = (apiData: AssignmentApiResponse): Assignment => ({
  id: apiData.id,
  ticket_id: apiData.ticket_id,
  priority: apiData.priority,
  assigned_at: apiData.assigned_at,
});

export const assignmentsApi = {
  async getAssignments(): Promise<Assignment[]> {
    const { data } = await assignmentApiClient.get<AssignmentApiResponse[]>('/assignments/');
    return data.map(adaptAssignment);
  },

  async deleteAssignment(id: number): Promise<void> {
    await assignmentApiClient.delete(`/assignments/${id}/`);
  },
};
