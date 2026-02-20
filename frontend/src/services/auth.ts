import axios from 'axios';
import type { User, LoginRequest, RegisterRequest, AuthResponse, TokenPair } from '../types/auth';

const AUTH_STORAGE_KEY = 'ticketSystem_user';

// MVP: localStorage para tokens (tech debt - migrar a HttpOnly cookies)
const ACCESS_TOKEN_KEY = 'accessToken';
const REFRESH_TOKEN_KEY = 'refreshToken';

const authApiClient = axios.create({
  baseURL: 'http://localhost:8003/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Obtener access token persistido en cliente.
 */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Obtener refresh token persistido en cliente.
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Persistir par de tokens en almacenamiento local.
 */
export function setTokens(tokens: TokenPair): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
}

/**
 * Eliminar tokens persistidos del almacenamiento local.
 */
export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Refrescar access token usando refresh token actual.
 */
export async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();

  if (!refreshToken) {
    return null;
  }

  try {
    const { data } = await authApiClient.post<TokenPair>('/auth/refresh/', {
      refresh: refreshToken,
    });

    setTokens(data);
    return data.access;
  } catch {
    clearTokens();
    return null;
  }
}

export const authService = {
  /**
   * Iniciar sesión
   */
  login: async (credentials: LoginRequest): Promise<User> => {
    const { data } = await authApiClient.post<AuthResponse>('/auth/login/', credentials);
    
    // MVP: persistencia local de sesión (tech debt - migrar a cookies HttpOnly)
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data.user));
    setTokens(data.tokens);
    
    return data.user;
  },

  /**
   * Registrar nuevo usuario
   */
  register: async (userData: RegisterRequest): Promise<User> => {
    const { data } = await authApiClient.post<AuthResponse>('/auth/', userData);
    
    // MVP: persistencia local de sesión (tech debt - migrar a cookies HttpOnly)
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(data.user));
    setTokens(data.tokens);
    
    return data.user;
  },

  /**
   * Cerrar sesión
   */
  logout: (): void => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    clearTokens();
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
    return authService.getCurrentUser() !== null && getAccessToken() !== null;
  },

  /**
   * Verificar si el usuario es admin
   */
  isAdmin: (): boolean => {
    const user = authService.getCurrentUser();
    return user?.role === 'ADMIN';
  },
};
