import type { TicketPriority } from '../../types/ticket';

const PRIORITY_LABELS: Record<TicketPriority, string> = {
  Unassigned: 'Sin prioridad',
  Low: 'Baja',
  Medium: 'Media',
  High: 'Alta',
};

/**
 * Devuelve la etiqueta legible para una prioridad.
 * Si priority es undefined o UNASSIGNED, retorna 'Unassigned'.
 *
 * @param priority - Valor de prioridad del ticket
 * @returns Etiqueta formateada para mostrar al usuario
 */
export function formatPriority(priority: TicketPriority | undefined): string {
  if (!priority) return 'Unassigned';
  return PRIORITY_LABELS[priority] ?? 'Unassigned';
}
