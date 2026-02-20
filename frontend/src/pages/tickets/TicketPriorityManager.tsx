/**
 * TicketPriorityManager — fase GREEN
 *
 * Permite a un ADMIN cambiar la prioridad de un ticket con estado
 * OPEN o IN_PROGRESS. Bloquea la reversión a UNASSIGNED si ya hay
 * una prioridad asignada. La justificación es opcional.
 */
import { useState } from 'react';
import { ticketApi } from '../../services/ticketApi';
import { authService } from '../../services/auth';
import type { Ticket, TicketPriority } from '../../types/ticket';

interface TicketPriorityManagerProps {
  ticket: Ticket;
  onUpdate: (updated: Ticket) => void;
}

/** Opciones de prioridad asignables (excluye UNASSIGNED). */
const PRIORITY_OPTIONS: { value: TicketPriority; label: string }[] = [
  { value: 'LOW',    label: 'Low'    },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'HIGH',   label: 'High'   },
];

const EDITABLE_STATUSES: Ticket['status'][] = ['OPEN', 'IN_PROGRESS'];

/**
 * Gestión manual de prioridad por Administrador.
 * Solo visible para ADMIN en tickets con estado OPEN o IN_PROGRESS.
 *
 * @param ticket   - Ticket actual
 * @param onUpdate - Callback invocado con el ticket actualizado tras éxito
 */
const TicketPriorityManager = ({ ticket, onUpdate }: TicketPriorityManagerProps) => {
  const currentUser = authService.getCurrentUser();

  const canManage =
    currentUser?.role === 'ADMIN' &&
    EDITABLE_STATUSES.includes(ticket.status);

  // ¿Ya existe una prioridad distinta de UNASSIGNED? Bloquea reversión.
  const hasAssignedPriority =
    ticket.priority !== undefined && ticket.priority !== 'UNASSIGNED';

  // Estado del formulario — hooks siempre antes del return condicional.
  const [selectedPriority, setSelectedPriority] = useState<string>(
    hasAssignedPriority ? (ticket.priority as string) : ''
  );
  const [justification, setJustification] = useState('');
  const [apiError, setApiError]             = useState<string | null>(null);
  const [saving, setSaving]                 = useState(false);

  if (!canManage) return null;

  /**
   * Envía el cambio de prioridad al backend.
   * Bloquea si el valor seleccionado es UNASSIGNED cuando ya hay prioridad.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Regla de negocio: no permitir revertir a UNASSIGNED si ya hay prioridad.
    if (hasAssignedPriority && selectedPriority === 'UNASSIGNED') return;

    // Sin selección válida, no hay nada que guardar.
    if (!selectedPriority || selectedPriority === 'UNASSIGNED') return;

    const payload: { priority: TicketPriority; justification?: string } = {
      priority: selectedPriority as TicketPriority,
    };
    if (justification.trim()) {
      payload.justification = justification.trim();
    }

    setSaving(true);
    setApiError(null);

    try {
      const updated = await ticketApi.updatePriority(ticket.id, payload);
      onUpdate(updated);
      setJustification('');
    } catch (err) {
      const status = (err as { response?: { status: number } })?.response?.status;
      const message =
        status === 403
          ? 'No tienes permiso para cambiar la prioridad.'
          : 'No se pudo actualizar la prioridad. Intenta de nuevo.';
      setApiError(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="priority-manager">
      <div className="priority-manager__field">
        <label htmlFor="priority-select">Prioridad</label>
        <select
          id="priority-select"
          value={selectedPriority}
          onChange={(e) => setSelectedPriority(e.target.value)}
        >
          {!hasAssignedPriority && (
            <option value="" disabled>
              Seleccionar prioridad
            </option>
          )}
          {PRIORITY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="priority-manager__field">
        <label htmlFor="priority-justification">Justificación</label>
        <textarea
          id="priority-justification"
          value={justification}
          onChange={(e) => setJustification(e.target.value)}
          placeholder="Opcional: describe el motivo del cambio de prioridad"
          rows={3}
        />
      </div>

      {apiError && (
        <div
          role="alert"
          style={{
            color: '#dc2626',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '0.75rem 1rem',
            margin: '0.5rem 0',
          }}
        >
          {apiError}
        </div>
      )}

      <button type="submit" disabled={saving}>
        {saving ? 'Guardando…' : 'Guardar'}
      </button>
    </form>
  );
};

export default TicketPriorityManager;
