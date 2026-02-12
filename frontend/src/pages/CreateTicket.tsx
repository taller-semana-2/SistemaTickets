import { useNavigate } from 'react-router-dom';
import TicketForm from '../components/TicketForm';
import { ticketApi } from '../api/ticketApi';
import type { CreateTicketDTO } from '../types/ticket';
import './CreateTicket.css';

const CreateTicket = () => {
  const navigate = useNavigate();

  const handleCreate = async (data: CreateTicketDTO) => {
    await ticketApi.createTicket(data);
    navigate('/tickets');
  };

  return (
    <div className="page-container">
      <div className="create-ticket-header">
        <h1 className="create-ticket-title">Crear Nuevo Ticket</h1>
        <p className="create-ticket-subtitle">
          Completa el formulario para crear un nuevo ticket de soporte
        </p>
      </div>
      <TicketForm onSubmit={handleCreate} />
    </div>
  );
};

export default CreateTicket;
