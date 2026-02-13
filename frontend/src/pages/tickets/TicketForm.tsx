import { useState, type FormEvent } from 'react';
import type { CreateTicketDTO } from '../../types/ticket';
import './TicketForm.css';

interface Props {
  onSubmit: (data: Omit<CreateTicketDTO, 'user_id'>) => void;
}

const TicketForm = ({ onSubmit }: Props) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    onSubmit({ title, description });

    setTitle('');
    setDescription('');
  };

  return (
    <form onSubmit={handleSubmit} className="ticket-form">
      <div className="form-group">
      <label className="form-label">Título</label>
      <input
        type="text"
        className="form-input"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
      />
      </div>

      <div className="form-group">
      <label className="form-label">Descripción</label>
      <textarea
        className="form-textarea"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        required
      />
      </div>

      <button type="submit" className="form-button">Crear Ticket</button>
    </form>
  );
};

export default TicketForm;
