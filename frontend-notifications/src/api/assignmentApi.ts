import type AssignmentApi from '../interface/AssignmentApi';
import type Assignment from '../interface/Assignment';
import { adaptAssignment } from '../adapters/assignmentAdapter';

const API_URL = 'http://localhost:8002/api/assignments/';

export const assignmentsApi = {
  async getAssignments(): Promise<Assignment[]> {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error('Error al obtener asignaciones');
    }

    const data: AssignmentApi[] = await response.json();
    return data.map(adaptAssignment);
  },

  async deleteAssignment(id: number): Promise<void> {
  const response = await fetch(`${API_URL}${id}/`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Error al eliminar la asignación');
  }
}

};
