import { BrowserRouter, Routes, Route, Navigate, useLocation, useMatch } from 'react-router-dom';
import { useSSE } from '../hooks/useSSE';

import Navbar from '../pages/navbar/NavBar';
import TicketList from '../pages/tickets/TicketList';
import CreateTicket from '../pages/tickets/CreateTicket';
import TicketDetail from '../pages/tickets/TicketDetail';
import NotificationList from '../pages/notifications/NotificationList';
import AssignmentList from '../pages/assignments/AssignmentList';
import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';
import ProtectedRoute from '../components/ProtectedRoute';

/**
 * Monta la conexión SSE global para actualizar el badge de notificaciones.
 * Solo se activa en rutas autenticadas y cuando el usuario NO está en
 * TicketDetail (esa ruta ya abre su propia conexión SSE con callback de
 * refresco de respuestas), garantizando una única conexión EventSource.
 */
const SSEGlobalListener = () => {
  useSSE();
  return null;
};

const Layout = ({ children }: { children: React.ReactNode }) => {
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
  // useMatch devuelve un objeto si la ruta actual coincide con el patrón.
  const isTicketDetail = Boolean(useMatch('/tickets/:id'));

  return (
    <>
      {!isAuthPage && <Navbar />}
      {/* SSE global: solo en rutas autenticadas que no sean TicketDetail */}
      {!isAuthPage && !isTicketDetail && <SSEGlobalListener />}
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

          {/* Tickets - Protegido para usuarios autenticados */}
          <Route 
            path="/tickets" 
            element={
              <ProtectedRoute>
                <TicketList />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/tickets/new" 
            element={
              <ProtectedRoute>
                <CreateTicket />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/tickets/:id" 
            element={
              <ProtectedRoute>
                <TicketDetail />
              </ProtectedRoute>
            } 
          />

          {/* Notificaciones - Solo ADMIN */}
          <Route 
            path="/notifications" 
            element={
              <ProtectedRoute requireAdmin={true}>
                <NotificationList />
              </ProtectedRoute>
            } 
          />

          {/* Asignaciones - Solo ADMIN */}
          <Route 
            path="/assignments" 
            element={
              <ProtectedRoute requireAdmin={true}>
                <AssignmentList />
              </ProtectedRoute>
            } 
          />

          {/* Ruta no encontrada */}
          <Route path="*" element={<h2>404 - Página no encontrada</h2>} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
};

export default AppRouter;
