/**
 * TicketPriorityManager
 *
 * Formulario que permite a un ADMIN cambiar manualmente la prioridad de un
 * ticket. Toda la lógica de validación y construcción del payload se delega
 * en `priorityRules.ts`, manteniendo el componente con responsabilidad única:
 * orquestar estado UI y llamar al servicio.
 */
import { useState } from 'react';
import { ticketApi } from '../../services/ticketApi';
import { useAuth } from '../../context/AuthContext';
import type { Ticket, TicketPriority } from '../../types/ticket';
import {
  ASSIGNABLE_PRIORITY_OPTIONS,
  canManagePriority,
  hasAssignedPriority,
  isValidPriorityTransition,
  buildPriorityPayload,
  resolvePriorityErrorMessage,
} from './priorityRules';
import './TicketPriorityManager.css';

interface TicketPriorityManagerProps {
  /** Ticket cuya prioridad se va a gestionar. */
  ticket: Ticket;
  /** Callback invocado con el ticket actualizado tras una operación exitosa. */
  onUpdate: (updated: Ticket) => void;
}

/**
 * Gestión manual de prioridad por Administrador.
 * Renderiza null para usuarios sin rol ADMIN o tickets en estado CLOSED.
 */
const TicketPriorityManager = ({ ticket, onUpdate }: TicketPriorityManagerProps) => {
  const { user: currentUser } = useAuth();
  const ticketHasPriority = hasAssignedPriority(ticket);

  // Hooks siempre antes del return condicional (regla de hooks de React).
  const [selectedPriority, setSelectedPriority] = useState<string>(
    ticketHasPriority ? (ticket.priority as string) : 'Low',
  );
  const [justification, setJustification] = useState('');
  const [apiError, setApiError]           = useState<string | null>(null);
  const [saving, setSaving]               = useState(false);

  if (!canManagePriority(currentUser, ticket)) return null;

  /** Envía el cambio al backend si la transición es válida. */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isValidPriorityTransition(ticket, selectedPriority)) return;

    const payload = buildPriorityPayload(
      selectedPriority as TicketPriority,
      justification,
    );

    setSaving(true);
    setApiError(null);

    try {
      const updated = await ticketApi.updatePriority(ticket.id, payload);
      onUpdate(updated);
      setJustification('');
    } catch (err) {
      setApiError(resolvePriorityErrorMessage(err));
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

          {ASSIGNABLE_PRIORITY_OPTIONS.map((opt) => (
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
