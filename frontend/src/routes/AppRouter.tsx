import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';

import Navbar from '../pages/navbar/NavBar';
import TicketList from '../pages/tickets/TicketList';
import CreateTicket from '../pages/tickets/CreateTicket';
import TicketDetail from '../pages/tickets/TicketDetail';
import NotificationList from '../pages/notifications/NotificationList';
import AssignmentList from '../pages/assignments/AssignmentList';
import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';

const Layout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';

  return (
    <>
      {!isAuthPage && <Navbar />}
      {children}
    </>
  );
};

const AppRouter = () => {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          {/* Autenticación */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Redirección inicial */}
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Tickets */}
          <Route path="/tickets" element={<TicketList />} />
          <Route path="/tickets/new" element={<CreateTicket />} />
          <Route path="/tickets/:id" element={<TicketDetail />} />

          {/* Notificaciones */}
          <Route path="/notifications" element={<NotificationList />} />

          {/* Asignaciones */}
          <Route path="/assignments" element={<AssignmentList />} />

          {/* Ruta no encontrada */}
          <Route path="*" element={<h2>404 - Página no encontrada</h2>} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
};

export default AppRouter;
