import { useNavigate } from 'react-router-dom';
import TicketForm from '../components/TicketForm';
import { ticketApi } from '../api/ticketApi';
import type { CreateTicketDTO } from '../types/ticket';


const CreateTicket = () => {
  const navigate = useNavigate();

  const handleCreate = async (data: CreateTicketDTO) => {
    await ticketApi.createTicket(data);
    navigate('/tickets');
  };

  return (
    <div>
      <h1>Crear Ticket</h1>
      <TicketForm onSubmit={handleCreate} />
    </div>
  );
};

export default CreateTicket;
