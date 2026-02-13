import type { User } from '../types/auth';
import { usersApiClient } from './axiosConfig';

export interface AdminUser {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
}

export const userService = {
  /**
   * Obtener usuarios por rol
   */
  getUsersByRole: async (role: 'ADMIN' | 'USER'): Promise<AdminUser[]> => {
    const { data } = await usersApiClient.get<AdminUser[]>(`/auth/by-role/${role}/`);
    return data;
  },

  /**
   * Obtener solo usuarios con rol ADMIN
   */
  getAdminUsers: async (): Promise<AdminUser[]> => {
    return userService.getUsersByRole('ADMIN');
  },
};
