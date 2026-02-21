export type UserRole = 'ADMIN' | 'USER';

export interface User {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Request body para registro público de usuarios.
 * SEGURIDAD: No incluye campo 'role'. El registro público siempre
 * asigna rol USER server-side.
 */
export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthError {
  error: string;
}
