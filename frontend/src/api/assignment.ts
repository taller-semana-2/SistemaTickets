import type { Assignment } from '../types/assignment';

// Backend API structure
interface AssignmentApiResponse {
  id: number;
  ticket_id: string;
  priority: 'low' | 'medium' | 'high';
  assigned_at: string;
}

const API_URL = 'http://localhost:8002/api/assignments/';

// Adapter function
const adaptAssignment = (apiData: AssignmentApiResponse): Assignment => ({
  id: apiData.id,
  ticket_id: apiData.ticket_id,
  priority: apiData.priority,
  assigned_at: apiData.assigned_at,
});

export const assignmentsApi = {
  async getAssignments(): Promise<Assignment[]> {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error('Error al obtener asignaciones');
    }

    const data: AssignmentApiResponse[] = await response.json();
    return data.map(adaptAssignment);
  },

  async deleteAssignment(id: number): Promise<void> {
    const response = await fetch(`${API_URL}${id}/`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Error al eliminar la asignación');
    }
  },
};
