import { describe, it, expect } from 'vitest';
import * as authModule from '../services/auth';
import {
  ticketApiClient,
  notificationApiClient,
  assignmentApiClient,
  usersApiClient,
} from '../services/axiosConfig';

describe('Auth Security — No localStorage', () => {
  it('auth module does not export getAccessToken', () => {
    expect('getAccessToken' in authModule).toBe(false);
  });

  it('auth module does not export getRefreshToken', () => {
    expect('getRefreshToken' in authModule).toBe(false);
  });

  it('auth module does not export setTokens', () => {
    expect('setTokens' in authModule).toBe(false);
  });

  it('auth module does not export clearTokens', () => {
    expect('clearTokens' in authModule).toBe(false);
  });

  it('auth module does not export refreshAccessToken', () => {
    expect('refreshAccessToken' in authModule).toBe(false);
  });

  it('authService does not have getCurrentUser method', () => {
    expect('getCurrentUser' in authModule.authService).toBe(false);
  });

  it('authService does not have isAuthenticated method', () => {
    expect('isAuthenticated' in authModule.authService).toBe(false);
  });

  it('authService does not have isAdmin method', () => {
    expect('isAdmin' in authModule.authService).toBe(false);
  });
});

describe('Axios Config — withCredentials', () => {
  it('ticketApiClient has withCredentials: true', () => {
    expect(ticketApiClient.defaults.withCredentials).toBe(true);
  });

  it('notificationApiClient has withCredentials: true', () => {
    expect(notificationApiClient.defaults.withCredentials).toBe(true);
  });

  it('assignmentApiClient has withCredentials: true', () => {
    expect(assignmentApiClient.defaults.withCredentials).toBe(true);
  });

  it('usersApiClient has withCredentials: true', () => {
    expect(usersApiClient.defaults.withCredentials).toBe(true);
  });
});

describe('Auth Service API', () => {
  it('authService exports login method', () => {
    expect(typeof authModule.authService.login).toBe('function');
  });

  it('authService exports register method', () => {
    expect(typeof authModule.authService.register).toBe('function');
  });

  it('authService exports logout method', () => {
    expect(typeof authModule.authService.logout).toBe('function');
  });

  it('authService exports me method', () => {
    expect(typeof authModule.authService.me).toBe('function');
  });
});
