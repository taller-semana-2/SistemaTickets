import axios from 'axios';
import type { User, LoginRequest, RegisterRequest } from '../types/auth';

/**
 * Axios client for users-service auth endpoints.
 * Uses withCredentials to send/receive HttpOnly cookies automatically.
 */
const authApiClient = axios.create({
  baseURL: 'http://localhost:8003/api',
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Auth service — lightweight wrapper for auth API calls.
 *
 * NOTE: Primary auth state management is in AuthContext.
 * This service provides the API call layer.
 * Tokens are managed via HttpOnly cookies — never exposed to JS.
 */
export const authService = {
  /**
   * Log in with email and password.
   * Cookies are set automatically by the backend response.
   */
  login: async (credentials: LoginRequest): Promise<User> => {
    const { data } = await authApiClient.post<{ user: User }>('/auth/login/', credentials);
    return data.user;
  },

  /**
   * Register a new user.
   * Cookies are set automatically by the backend response.
   */
  register: async (userData: RegisterRequest): Promise<User> => {
    const { data } = await authApiClient.post<{ user: User }>('/auth/', userData);
    return data.user;
  },

  /**
   * Log out — clears HttpOnly cookies server-side.
   */
  logout: async (): Promise<void> => {
    await authApiClient.post('/auth/logout/');
  },

  /**
   * Get current authenticated user from the server.
   * Returns null if not authenticated.
   */
  me: async (): Promise<User | null> => {
    try {
      const { data } = await authApiClient.get<User>('/auth/me/');
      return data;
    } catch {
      return null;
    }
  },
};
