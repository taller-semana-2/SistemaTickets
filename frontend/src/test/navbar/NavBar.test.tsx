/**
 * Tests para NavBar - Bug Fix #016
 * 
 * Objetivo: Verificar que el NavBar NO hace peticiones a la API de notificaciones
 * cuando el usuario NO está autenticado.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import NavBar from '../../pages/navbar/NavBar';
import { notificationsApi } from '../../services/notification';
import type { User } from '../../types/auth';

// Mock de los contextos
vi.mock('../../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../../context/NotificacionContext', () => ({
  useNotifications: vi.fn(),
}));

// Mock del servicio de notificaciones
vi.mock('../../services/notification', () => ({
  notificationsApi: {
    getNotifications: vi.fn(),
  },
}));

// Import de los hooks mockeados para poder modificarlos en cada test
import { useAuth } from '../../context/AuthContext';
import { useNotifications } from '../../context/NotificacionContext';

// Helper para crear un mock user completo
const createMockUser = (overrides: Partial<User> = {}): User => ({
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  role: 'USER',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  ...overrides,
});

// Helper para renderizar NavBar con BrowserRouter
const renderNavBar = () => {
  return render(
    <BrowserRouter>
      <NavBar />
    </BrowserRouter>
  );
};

describe('NavBar - Prevención de fetch sin autenticación (Bug #016)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default para useNotifications
    vi.mocked(useNotifications).mockReturnValue({
      trigger: 0,
      refreshUnread: vi.fn(),
    });
  });

  it('NO hace fetch de notificaciones cuando el usuario NO está autenticado', async () => {
    // Mock de usuario no autenticado
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      isAuthenticated: false,
      isAdmin: false,
    });

    renderNavBar();

    // Esperar un poco para asegurar que no se hizo ninguna llamada
    await waitFor(() => {
      expect(notificationsApi.getNotifications).not.toHaveBeenCalled();
    }, { timeout: 500 });

    // Verificar que el NavBar se renderizó
    expect(screen.getByText('TicketSystem')).toBeInTheDocument();
  });

  it('NO hace fetch de notificaciones cuando está en estado de carga (loading)', async () => {
    // Mock de estado de carga
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: true, // Estado de carga
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      isAuthenticated: false,
      isAdmin: false,
    });

    renderNavBar();

    await waitFor(() => {
      expect(notificationsApi.getNotifications).not.toHaveBeenCalled();
    }, { timeout: 500 });
  });

  it('SÍ hace fetch de notificaciones cuando el usuario ESTÁ autenticado', async () => {
    const mockUser = createMockUser();

    const mockNotifications = [
      { id: '1', title: 'Ticket #1', message: 'Test', read: false, createdAt: '2026-02-23T10:00:00Z' },
      { id: '2', title: 'Ticket #2', message: 'Test 2', read: true, createdAt: '2026-02-23T11:00:00Z' },
    ];

    vi.mocked(notificationsApi.getNotifications).mockResolvedValue(mockNotifications);

    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      isAuthenticated: true,
      isAdmin: false,
    });

    renderNavBar();

    // Verificar que se llamó a getNotifications
    await waitFor(() => {
      expect(notificationsApi.getNotifications).toHaveBeenCalledTimes(1);
    });
  });

  it('muestra el badge de notificaciones con el conteo correcto para usuarios autenticados ADMIN', async () => {
    const mockUser = createMockUser({
      username: 'adminuser',
      email: 'admin@example.com',
      role: 'ADMIN',
    });

    const mockNotifications = [
      { id: '1', title: 'Ticket #1', message: 'Unread 1', read: false, createdAt: '2026-02-23T10:00:00Z' },
      { id: '2', title: 'Ticket #2', message: 'Read', read: true, createdAt: '2026-02-23T11:00:00Z' },
      { id: '3', title: 'Ticket #3', message: 'Unread 2', read: false, createdAt: '2026-02-23T12:00:00Z' },
    ];

    vi.mocked(notificationsApi.getNotifications).mockResolvedValue(mockNotifications);

    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      isAuthenticated: true,
      isAdmin: true,
    });

    renderNavBar();

    // Esperar a que aparezca el badge con el conteo de no leídas (2)
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    // Verificar que se hizo la llamada
    expect(notificationsApi.getNotifications).toHaveBeenCalledTimes(1);
  });

  it('NO muestra el link de notificaciones para usuarios no ADMIN', async () => {
    const mockUser = createMockUser({
      role: 'USER',
    });

    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      isAuthenticated: true,
      isAdmin: false,
    });

    renderNavBar();

    // El link de notificaciones solo es visible para ADMIN
    expect(screen.queryByText(/🔔 Notificaciones/)).not.toBeInTheDocument();
  });

  it('NO hace fetch si isAuthenticated es true pero loading es true', async () => {
    const mockUser = createMockUser();

    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      loading: true, // Aunque está autenticado, aún está cargando
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      isAuthenticated: true,
      isAdmin: false,
    });

    renderNavBar();

    await waitFor(() => {
      expect(notificationsApi.getNotifications).not.toHaveBeenCalled();
    }, { timeout: 500 });
  });

  it('maneja errores en la carga de notificaciones sin romper el componente', async () => {
    const mockUser = createMockUser({
      role: 'ADMIN',
    });

    // Mock de consola para evitar ruido en los tests
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    vi.mocked(notificationsApi.getNotifications).mockRejectedValue(
      new Error('Network error')
    );

    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      isAuthenticated: true,
      isAdmin: true,
    });

    renderNavBar();

    // El componente debe renderizarse sin errores
    expect(screen.getByText('TicketSystem')).toBeInTheDocument();
    expect(screen.getByText(/🔔 Notificaciones/)).toBeInTheDocument();

    // Debe haber intentado cargar
    await waitFor(() => {
      expect(notificationsApi.getNotifications).toHaveBeenCalledTimes(1);
    });

    // Debe haber logueado el error
    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error cargando notificaciones',
        expect.any(Error)
      );
    });

    consoleErrorSpy.mockRestore();
  });

  it('NO hace llamadas duplicadas al montar el componente', async () => {
    const mockUser = createMockUser({
      role: 'ADMIN',
    });

    const mockNotifications = [
      { id: '1', title: 'Ticket #1', message: 'Test', read: false, createdAt: '2026-02-23T10:00:00Z' },
    ];

    vi.mocked(notificationsApi.getNotifications).mockResolvedValue(mockNotifications);

    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      isAuthenticated: true,
      isAdmin: true,
    });

    renderNavBar();

    // Esperar a que termine la carga
    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument();
    });

    // Debe haberse llamado solo una vez durante el mount
    expect(notificationsApi.getNotifications).toHaveBeenCalledTimes(1);
  });
});

