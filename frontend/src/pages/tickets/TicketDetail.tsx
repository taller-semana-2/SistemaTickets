import { useParams } from 'react-router-dom';

const TicketDetail = () => {
  const { id } = useParams<{ id: string }>();

  return <h1>Detalle del ticket {id}</h1>;
};

export default TicketDetail;