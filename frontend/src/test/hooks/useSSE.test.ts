/**
 * Tests TDD (fase RED → GREEN) para el hook useSSE.
 *
 * Cubre los requisitos de HU-2.2 y la parte de HU-3.1
 * "Nueva respuesta aparece automáticamente".
 *
 * Estrategia:
 *  - MockEventSource simula la API nativa de EventSource.
 *  - useNotifications se mockea para aislar el hook de cualquier Provider.
 *  - Cada test verifica un comportamiento discreto.
 */

import { describe, it, expect, vi, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { MockEventSource, installEventSourceMock } from '../__mocks__/EventSourceMock';
import { useSSE } from '../../hooks/useSSE';

// ---------------------------------------------------------------------------
// Mock del NotificationContext — aísla el hook del Provider real
// ---------------------------------------------------------------------------

const mockRefreshUnread = vi.fn();

vi.mock('../../context/NotificacionContext', () => ({
  useNotifications: () => ({ trigger: 0, refreshUnread: mockRefreshUnread }),
}));

// ---------------------------------------------------------------------------
// Instala/desinstala el mock de EventSource automáticamente en cada test
// ---------------------------------------------------------------------------

installEventSourceMock();

afterEach(() => {
  mockRefreshUnread.mockClear();
});

// ---------------------------------------------------------------------------
// Suite de tests
// ---------------------------------------------------------------------------

describe('useSSE — HU-2.2: Conexión SSE de notificaciones', () => {
  // -------------------------------------------------------------------------
  // HU-2.2 — Conexión SSE
  // -------------------------------------------------------------------------

  it('crea una conexión EventSource al montar el hook', () => {
    renderHook(() => useSSE());

    expect(MockEventSource.instances).toHaveLength(1);
  });

  it('conecta al endpoint SSE del notification-service', () => {
    renderHook(() => useSSE());

    const url = MockEventSource.latest().url;
    expect(url).toMatch(/\/notifications\/stream\//);
  });

  it('cierra la conexión EventSource al desmontar el hook', () => {
    const { unmount } = renderHook(() => useSSE());

    unmount();

    expect(MockEventSource.latest().close).toHaveBeenCalledTimes(1);
  });

  it('registra el handler de onerror sin lanzar excepciones', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);

    const { unmount } = renderHook(() => useSSE());

    expect(() => {
      act(() => {
        MockEventSource.latest().triggerError();
      });
    }).not.toThrow();

    expect(consoleSpy).toHaveBeenCalled();

    consoleSpy.mockRestore();
    unmount();
  });

  // -------------------------------------------------------------------------
  // HU-2.2 — Actualización del contador de no leídas
  // -------------------------------------------------------------------------

  it('llama refreshUnread al recibir el evento "notification"', () => {
    renderHook(() => useSSE());

    act(() => {
      MockEventSource.latest().emit('notification', { ticket_id: 7, message: 'nuevo' });
    });

    expect(mockRefreshUnread).toHaveBeenCalledTimes(1);
  });

  it('incrementa el contador ante múltiples eventos consecutivos', () => {
    renderHook(() => useSSE());
    const es = MockEventSource.latest();

    act(() => {
      es.emit('notification', { ticket_id: 1 });
      es.emit('notification', { ticket_id: 2 });
      es.emit('notification', { ticket_id: 3 });
    });

    expect(mockRefreshUnread).toHaveBeenCalledTimes(3);
  });
});

// ---------------------------------------------------------------------------

describe('useSSE — HU-3.1: Refresco automático de respuestas en TicketDetail', () => {
  it('llama onRefreshResponses cuando ticket_id coincide con currentTicketId', () => {
    const onRefreshResponses = vi.fn();

    renderHook(() => useSSE({ currentTicketId: 42, onRefreshResponses }));

    act(() => {
      MockEventSource.latest().emit('notification', { ticket_id: 42 });
    });

    expect(onRefreshResponses).toHaveBeenCalledTimes(1);
  });

  it('NO llama onRefreshResponses cuando el ticket_id es diferente al actual', () => {
    const onRefreshResponses = vi.fn();

    renderHook(() => useSSE({ currentTicketId: 42, onRefreshResponses }));

    act(() => {
      MockEventSource.latest().emit('notification', { ticket_id: 99 });
    });

    expect(onRefreshResponses).not.toHaveBeenCalled();
    // pero sí incrementa el contador global
    expect(mockRefreshUnread).toHaveBeenCalledTimes(1);
  });

  it('funciona sin currentTicketId (no explota cuando es undefined)', () => {
    // Caso: hook montado fuera de TicketDetail, sin opción de refresco
    renderHook(() => useSSE());

    expect(() => {
      act(() => {
        MockEventSource.latest().emit('notification', { ticket_id: 5 });
      });
    }).not.toThrow();

    expect(mockRefreshUnread).toHaveBeenCalledTimes(1);
  });

  it('NO llama onRefreshResponses si no se provee la función (solo refreshUnread)', () => {
    // Caso: currentTicketId presente pero sin callback de refresco
    renderHook(() => useSSE({ currentTicketId: 5 }));

    expect(() => {
      act(() => {
        MockEventSource.latest().emit('notification', { ticket_id: 5 });
      });
    }).not.toThrow();

    expect(mockRefreshUnread).toHaveBeenCalledTimes(1);
  });

  it('sigue siempre llamando refreshUnread incluso cuando coincide ticket_id', () => {
    const onRefreshResponses = vi.fn();

    renderHook(() => useSSE({ currentTicketId: 42, onRefreshResponses }));

    act(() => {
      MockEventSource.latest().emit('notification', { ticket_id: 42 });
    });

    // Ambas deben haberse llamado
    expect(mockRefreshUnread).toHaveBeenCalledTimes(1);
    expect(onRefreshResponses).toHaveBeenCalledTimes(1);
  });
});
