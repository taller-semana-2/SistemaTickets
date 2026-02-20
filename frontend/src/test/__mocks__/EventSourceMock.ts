/**
 * MockEventSource — mock reutilizable de EventSource para tests SSE.
 *
 * Uso:
 *   import { MockEventSource, installEventSourceMock } from '../__mocks__/EventSourceMock';
 *
 *   installEventSourceMock();  // en la suite — instala/resetea antes/después de cada test
 *
 *   // En el test, después de montar el componente/hook:
 *   const es = MockEventSource.latest();
 *   act(() => es.emit('notification', { ticket_id: 5 }));
 */

import { vi, beforeEach, afterEach } from 'vitest';

type MessageHandler = (evt: MessageEvent) => void;

export class MockEventSource {
  /** Historial de todas las instancias creadas en el test actual. */
  static instances: MockEventSource[] = [];

  readonly url: string;

  /** Asignado directamente por el código bajo test si usa `es.onerror = ...` */
  onerror: ((evt: Event) => void) | null = null;

  readonly close = vi.fn<[], void>();

  private readonly listeners: Record<string, MessageHandler[]> = {};

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  /**
   * Implementa la misma firma que EventTarget.addEventListener (solo el subconjunto
   * relevante para SSE: tipo de evento + handler).
   */
  addEventListener(type: string, handler: MessageHandler): void {
    if (!this.listeners[type]) {
      this.listeners[type] = [];
    }
    this.listeners[type].push(handler);
  }

  // ---------------------------------------------------------------------------
  // Helpers de test
  // ---------------------------------------------------------------------------

  /**
   * Simula la recepción de un evento SSE del tipo indicado.
   * Serializa `data` como JSON, igual que haría el servidor.
   */
  emit(type: string, data: unknown): void {
    const event = new MessageEvent(type, { data: JSON.stringify(data) });
    this.listeners[type]?.forEach((handler) => handler(event));
  }

  /** Simula un error de transporte (dispara `onerror` si está asignado). */
  triggerError(): void {
    this.onerror?.(new Event('error'));
  }

  /** Devuelve la instancia más reciente (la última creada). */
  static latest(): MockEventSource {
    const last = MockEventSource.instances.at(-1);
    if (!last) {
      throw new Error(
        'MockEventSource: no hay instancias. ¿Se montó el componente/hook antes de llamar latest()?',
      );
    }
    return last;
  }

  /** Limpia el registro de instancias. Llamado automáticamente por installEventSourceMock(). */
  static reset(): void {
    MockEventSource.instances = [];
  }
}

// ---------------------------------------------------------------------------
// Helper de instalación para suites de test
// ---------------------------------------------------------------------------

/**
 * Registra beforeEach/afterEach para instalar y desinstalar el mock de EventSource
 * automáticamente en la suite que lo llame.
 *
 * @returns La clase MockEventSource para usarla directamente en los tests.
 */
export const installEventSourceMock = (): typeof MockEventSource => {
  const originalEventSource =
    typeof globalThis.EventSource !== 'undefined' ? globalThis.EventSource : undefined;

  beforeEach(() => {
    MockEventSource.reset();
    vi.clearAllMocks();
    globalThis.EventSource = MockEventSource as unknown as typeof EventSource;
  });

  afterEach(() => {
    if (originalEventSource !== undefined) {
      globalThis.EventSource = originalEventSource;
    } else {
      // jsdom no tiene EventSource nativo; simplemente limpiar
      delete (globalThis as Record<string, unknown>).EventSource;
    }
  });

  return MockEventSource;
};
