/**
 * priorityRules.ts
 *
 * Reglas de dominio para la gestión de prioridad de tickets.
 * Módulo de funciones puras: sin dependencias de React ni efectos secundarios.
 * Puede testearse de forma completamente aislada del componente.
 */
import type { Ticket, TicketPriority } from '../../types/ticket';
import type { User } from '../../types/auth';

// ---------------------------------------------------------------------------
// Constantes de dominio
// ---------------------------------------------------------------------------

/** Estados en los que un ticket admite cambio de prioridad. */
export const EDITABLE_STATUSES: readonly Ticket['status'][] = ['OPEN', 'IN_PROGRESS'];

/** Opciones de prioridad asignables (Unassigned no se ofrece al usuario). */
export const ASSIGNABLE_PRIORITY_OPTIONS: ReadonlyArray<{
  value: TicketPriority;
  label: string;
}> = [
  { value: 'Low',    label: 'Baja'  },
  { value: 'Medium', label: 'Media' },
  { value: 'High',   label: 'Alta'  },
];

// ---------------------------------------------------------------------------
// Validaciones de acceso
// ---------------------------------------------------------------------------

/**
 * Determina si un usuario puede gestionar la prioridad de un ticket.
 * Requiere rol ADMIN y estado OPEN o IN_PROGRESS.
 *
 * @param user   - Usuario autenticado (o null si no hay sesión)
 * @param ticket - Ticket a gestionar
 */
export function canManagePriority(user: User | null, ticket: Ticket): boolean {
  return user?.role === 'ADMIN' && EDITABLE_STATUSES.includes(ticket.status);
}

// ---------------------------------------------------------------------------
// Validaciones de transición de prioridad
// ---------------------------------------------------------------------------

/**
 * Indica si el ticket ya tiene una prioridad asignada distinta de UNASSIGNED.
 *
 * @param ticket - Ticket a evaluar
 */
export function hasAssignedPriority(ticket: Ticket): boolean {
  return ticket.priority !== undefined && ticket.priority !== 'Unassigned';
}

/**
 * Valida que la transición de prioridad sea permitida por las reglas de negocio.
 *
 * Reglas:
 *  - El valor destino no puede ser vacío ni UNASSIGNED.
 *  - No se permite volver a UNASSIGNED si ya hay una prioridad asignada.
 *
 * @param ticket - Ticket con la prioridad actual
 * @param next   - Valor de prioridad candidato
 */
export function isValidPriorityTransition(ticket: Ticket, next: string): boolean {
  if (!next || next === 'Unassigned') return false;
  if (hasAssignedPriority(ticket) && next === 'Unassigned') return false;
  return true;
}

// ---------------------------------------------------------------------------
// Construcción de payload
// ---------------------------------------------------------------------------

/**
 * Construye el payload para la API de actualización de prioridad.
 * Incluye `justification` solo si el texto no está vacío.
 *
 * @param priority      - Prioridad validada a enviar
 * @param justification - Justificación opcional ingresada por el usuario
 */
export function buildPriorityPayload(
  priority: TicketPriority,
  justification: string,
): { priority: TicketPriority; justification?: string } {
  const payload: { priority: TicketPriority; justification?: string } = { priority };
  const trimmed = justification.trim();
  if (trimmed) payload.justification = trimmed;
  return payload;
}

// ---------------------------------------------------------------------------
// Mapeo de errores de API
// ---------------------------------------------------------------------------

/**
 * Convierte un error de API en un mensaje legible para el usuario.
 *
 * @param err - Error capturado en el bloque catch
 */
export function resolvePriorityErrorMessage(err: unknown): string {
  const status = (err as { response?: { status: number } })?.response?.status;
  return status === 403
    ? 'No tienes permiso para cambiar la prioridad.'
    : 'No se pudo actualizar la prioridad. Intenta de nuevo.';
}
