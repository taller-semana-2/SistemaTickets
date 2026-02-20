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
  role?: UserRole;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  user: User;
  tokens: TokenPair;
}

export interface AuthError {
  error: string;
}
