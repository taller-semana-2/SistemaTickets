/**
 * TicketPriorityManager — STUB (fase RED / TDD)
 *
 * Componente vacío que permite que los tests compilen y fallen
 * por aserciones de negocio, no por error de importación.
 *
 * TODO (fase GREEN): implementar las siguientes capacidades
 *   - Mostrar selector de prioridad solo para ADMIN y ticket OPEN/IN_PROGRESS
 *   - Bloquear la opción UNASSIGNED si la prioridad actual no es UNASSIGNED
 *   - Campo de justificación opcional (textarea)
 *   - Botón "Guardar" que llama a ticketApi.updatePriority
 *   - Propagar el ticket actualizado vía onUpdate
 *   - Mostrar div de error rojo (role=alert) ante respuestas 400/403
 */
import type { Ticket } from '../../types/ticket';

interface TicketPriorityManagerProps {
  ticket: Ticket;
  onUpdate: (updated: Ticket) => void;
}

/**
 * Gestión manual de prioridad por Administrador.
 * Solo visible para ADMIN en tickets con estado OPEN o IN_PROGRESS.
 */
const TicketPriorityManager = (_props: TicketPriorityManagerProps) => {
  // Stub — no implementado aún. Los tests deben fallar en fase RED.
  return null;
};

export default TicketPriorityManager;
