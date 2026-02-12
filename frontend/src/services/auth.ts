import type { User, LoginRequest, RegisterRequest, AuthResponse } from '../types/auth';
import { usersApiClient } from './axiosConfig';

const AUTH_STORAGE_KEY = 'ticketSystem_user';

export const authService = {
  /**
   * Iniciar sesión
   */
  login: async (credentials: LoginRequest): Promise<User> => {
    const { data } = await usersApiClient.post<AuthResponse>('/auth/login/', credentials);
    
    // Guardar usuario en localStorage
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data));
    
    return data;
  },

  /**
   * Registrar nuevo usuario
   */
  register: async (userData: RegisterRequest): Promise<User> => {
    const { data } = await usersApiClient.post<AuthResponse>('/auth/', userData);
    
    // Guardar usuario en localStorage después del registro
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data));
    
    return data;
  },

  /**
   * Cerrar sesión
   */
  logout: (): void => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  },

  /**
   * Obtener usuario actual desde localStorage
   */
  getCurrentUser: (): User | null => {
    const userJson = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!userJson) return null;
    
    try {
      return JSON.parse(userJson) as User;
    } catch {
      return null;
    }
  },

  /**
   * Verificar si el usuario está autenticado
   */
  isAuthenticated: (): boolean => {
    return authService.getCurrentUser() !== null;
  },

  /**
   * Verificar si el usuario es admin
   */
  isAdmin: (): boolean => {
    const user = authService.getCurrentUser();
    return user?.role === 'ADMIN';
  },
};
