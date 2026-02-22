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

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}
/** Auth response from server — tokens are in HttpOnly cookies, not in body */
export interface AuthResponse {
  user: User;
}

export interface AuthError {
  error: string;
}
