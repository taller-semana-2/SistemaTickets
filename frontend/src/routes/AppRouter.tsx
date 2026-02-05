import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import Navbar from '../components/NavBar';
import TicketList from '../pages/TicketList';
import CreateTicket from '../pages/CreateTicket';
import TicketDetail from '../pages/TicketDetail';

const AppRouter = () => {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        {/* Redirección inicial */}
        <Route path="/" element={<Navigate to="/tickets" replace />} />

        {/* Tickets */}
        <Route path="/tickets" element={<TicketList />} />
        <Route path="/tickets/new" element={<CreateTicket />} />
        <Route path="/tickets/:id" element={<TicketDetail />} />

        {/* Ruta no encontrada */}
        <Route path="*" element={<h2>404 - Página no encontrada</h2>} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRouter;
