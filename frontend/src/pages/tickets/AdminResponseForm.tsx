import { useRef, useState } from 'react';
import type React from 'react';
import { ticketApi } from '../../services/ticketApi';
import type { TicketResponse } from '../../types/ticket';
import { useAuth } from '../../context/AuthContext';
import './AdminResponseForm.css';

export const MAX_RESPONSE_LENGTH = 2000;

export interface AdminResponseFormProps {
  ticketId: number;
  onResponseCreated: (response: TicketResponse) => void;
}

/**
 * Formulario exclusivo para admins. Gestiona estado local del textarea,
 * el contador de caracteres y la llamada a la API.
 * Solo se monta cuando el ticket NO está CLOSED (decisión del padre).
 */
const AdminResponseForm = ({ ticketId, onResponseCreated }: AdminResponseFormProps) => {
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { user } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || submitting) return;

    setSubmitting(true);
    try {
      const created = await ticketApi.createResponse(ticketId, text, user!.id);
      onResponseCreated(created);
      setText('');
      textareaRef.current?.focus();
      window.alert('Respuesta enviada correctamente');
    } catch (err) {
      console.error('Error al enviar respuesta:', err);
      window.alert('No se pudo enviar la respuesta');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="admin-response-form">
      <h3 className="admin-response-form-title">Añadir respuesta</h3>
      <form onSubmit={handleSubmit}>
        <textarea
          ref={textareaRef}
          data-testid="response-textarea"
          className="admin-response-textarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={MAX_RESPONSE_LENGTH}
          placeholder="Escribe tu respuesta..."
          rows={4}
        />
        <div className="admin-response-footer">
          <span className="admin-response-counter">
            {text.length} / {MAX_RESPONSE_LENGTH}
          </span>
          <button
            type="submit"
            className="admin-response-submit"
            disabled={text.trim().length === 0 || submitting}
          >
            Responder
          </button>
        </div>
      </form>
    </section>
  );
};

export default AdminResponseForm;
