/**
 * Tests para TicketAssign - Bug Fix #015
 * 
 * Objetivo: Verificar que la asignación de tickets requiere confirmación explícita
 * antes de ejecutar el callback onAssign.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TicketAssign from '../../components/TicketAssign';
import { userService } from '../../services/user';
import type { AdminUser } from '../../services/user';

// Mock del servicio de usuarios
vi.mock('../../services/user', () => ({
  userService: {
    getAdminUsers: vi.fn(),
  },
}));

const mockAdminUsers: AdminUser[] = [
  { id: '1', username: 'admin1', email: 'admin1@test.com', role: 'ADMIN', is_active: true },
  { id: '2', username: 'admin2', email: 'admin2@test.com', role: 'ADMIN', is_active: true },
  { id: '3', username: 'admin3', email: 'admin3@test.com', role: 'ADMIN', is_active: true },
];

describe('TicketAssign - Confirmación de asignación (Bug #015)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(userService.getAdminUsers).mockResolvedValue(mockAdminUsers);
  });

  it('NO asigna inmediatamente al cambiar el dropdown', async () => {
    const onAssignMock = vi.fn();
    const user = userEvent.setup();

    render(
      <TicketAssign
        ticketId={1}
        onAssign={onAssignMock}
      />
    );

    // Esperar a que carguen los usuarios
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    // Seleccionar un administrador
    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '1');

    // Verificar que onAssign NO fue llamado inmediatamente
    expect(onAssignMock).not.toHaveBeenCalled();
  });

  it('muestra botón "Confirmar asignación" después de seleccionar un usuario', async () => {
    const onAssignMock = vi.fn();
    const user = userEvent.setup();

    render(
      <TicketAssign
        ticketId={1}
        onAssign={onAssignMock}
      />
    );

    // Esperar a que carguen los usuarios
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    // Inicialmente, no debe estar visible el botón
    expect(screen.queryByRole('button', { name: /confirmar asignación/i })).not.toBeInTheDocument();

    // Seleccionar un administrador
    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '1');

    // Ahora debe aparecer el botón de confirmación
    expect(screen.getByRole('button', { name: /confirmar asignación/i })).toBeInTheDocument();
  });

  it('ejecuta onAssign con userId correcto al hacer clic en Confirmar', async () => {
    const onAssignMock = vi.fn();
    const user = userEvent.setup();

    render(
      <TicketAssign
        ticketId={1}
        onAssign={onAssignMock}
      />
    );

    // Esperar a que carguen los usuarios
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    // Seleccionar un administrador
    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '2'); // Seleccionar admin2

    // Click en confirmar
    const confirmButton = screen.getByRole('button', { name: /confirmar asignación/i });
    await user.click(confirmButton);

    // Verificar que onAssign fue llamado con el ID correcto
    expect(onAssignMock).toHaveBeenCalledTimes(1);
    expect(onAssignMock).toHaveBeenCalledWith('2');
  });

  it('permite cambiar selección antes de confirmar y usa el último valor', async () => {
    const onAssignMock = vi.fn();
    const user = userEvent.setup();

    render(
      <TicketAssign
        ticketId={1}
        onAssign={onAssignMock}
      />
    );

    // Esperar a que carguen los usuarios
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');

    // Seleccionar admin1
    await user.selectOptions(select, '1');
    expect(onAssignMock).not.toHaveBeenCalled();

    // Cambiar selección a admin3
    await user.selectOptions(select, '3');
    expect(onAssignMock).not.toHaveBeenCalled();

    // Confirmar
    const confirmButton = screen.getByRole('button', { name: /confirmar asignación/i });
    await user.click(confirmButton);

    // Debe enviar el último valor seleccionado (admin3)
    expect(onAssignMock).toHaveBeenCalledTimes(1);
    expect(onAssignMock).toHaveBeenCalledWith('3');
  });

  it('deshabilita botón de confirmar si no hay selección válida', async () => {
    const onAssignMock = vi.fn();
    const user = userEvent.setup();

    render(
      <TicketAssign
        ticketId={1}
        onAssign={onAssignMock}
      />
    );

    // Esperar a que carguen los usuarios
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');

    // Seleccionar un administrador
    await user.selectOptions(select, '1');

    const confirmButton = screen.getByRole('button', { name: /confirmar asignación/i });
    expect(confirmButton).not.toBeDisabled();

    // Volver a "Seleccionar administrador"
    await user.selectOptions(select, '');

    // El botón de confirmar no debe estar visible cuando no hay selección
    expect(screen.queryByRole('button', { name: /confirmar asignación/i })).not.toBeInTheDocument();
  });

  it('muestra botón Cancelar y resetea la selección al hacer clic', async () => {
    const onAssignMock = vi.fn();
    const user = userEvent.setup();

    render(
      <TicketAssign
        ticketId={1}
        currentAssignedId="2"
        onAssign={onAssignMock}
      />
    );

    // Esperar a que carguen los usuarios
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox') as HTMLSelectElement;

    // Estado inicial debe ser el currentAssignedId
    expect(select.value).toBe('2');

    // Cambiar selección
    await user.selectOptions(select, '1');
    expect(select.value).toBe('1');

    // Click en Cancelar
    const cancelButton = screen.getByRole('button', { name: /cancelar/i });
    await user.click(cancelButton);

    // Debe volver al valor original
    expect(select.value).toBe('2');

    // No debe haber llamado a onAssign
    expect(onAssignMock).not.toHaveBeenCalled();
  });

  it('oculta botones después de confirmar', async () => {
    const onAssignMock = vi.fn();
    const user = userEvent.setup();

    render(
      <TicketAssign
        ticketId={1}
        onAssign={onAssignMock}
      />
    );

    // Esperar a que carguen los usuarios
    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    // Seleccionar y confirmar
    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '1');

    const confirmButton = screen.getByRole('button', { name: /confirmar asignación/i });
    await user.click(confirmButton);

    // Los botones deben ocultarse
    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /confirmar asignación/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /cancelar/i })).not.toBeInTheDocument();
    });
  });

  it('muestra estado de carga mientras se obtienen usuarios', () => {
    vi.mocked(userService.getAdminUsers).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<TicketAssign ticketId={1} />);

    expect(screen.getByText('Cargando usuarios...')).toBeInTheDocument();
  });

  it('muestra mensaje de error si falla la carga de usuarios', async () => {
    vi.mocked(userService.getAdminUsers).mockRejectedValue(
      new Error('Network error')
    );

    render(<TicketAssign ticketId={1} />);

    await waitFor(() => {
      expect(screen.getByText('No se pudieron cargar los administradores')).toBeInTheDocument();
    });
  });
});
