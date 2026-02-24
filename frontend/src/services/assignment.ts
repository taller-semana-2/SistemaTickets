import type { Assignment, UpdateAssignedUserDTO } from '../types/assignment';
import { assignmentApiClient } from './axiosConfig';

// Backend API structure
interface AssignmentApiResponse {
  id: number;
  ticket_id: string;
  priority: 'low' | 'medium' | 'high';
  assigned_at: string;
  assigned_to?: string;
}

// Adapter function
const adaptAssignment = (apiData: AssignmentApiResponse): Assignment => ({
  id: apiData.id,
  ticket_id: apiData.ticket_id,
  priority: apiData.priority,
  assigned_at: apiData.assigned_at,
  assigned_to: apiData.assigned_to,
});

export const assignmentsApi = {
  async getAssignments(signal?: AbortSignal): Promise<Assignment[]> {
    const { data } = await assignmentApiClient.get<AssignmentApiResponse[]>('/assignments/', { signal });
    return data.map(adaptAssignment);
  },

  async deleteAssignment(id: number, signal?: AbortSignal): Promise<void> {
    await assignmentApiClient.delete(`/assignments/${id}/`, { signal });
  },

  async assignUser(assignmentId: number, userId: string, signal?: AbortSignal): Promise<Assignment> {
    const payload: UpdateAssignedUserDTO = { assigned_to: userId };
    const { data } = await assignmentApiClient.patch<AssignmentApiResponse>(
      `/assignments/${assignmentId}/assign-user/`,
      payload,
      { signal }
    );
    return adaptAssignment(data);
  },
};
