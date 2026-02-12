import { Navigate } from 'react-router-dom';
import { authService } from '../services/auth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

/**
 * Componente para proteger rutas según autenticación y rol
 * 
 * @param children - Componente a renderizar si tiene acceso
 * @param requireAdmin - Si true, solo permite acceso a usuarios ADMIN
 */
const ProtectedRoute = ({ children, requireAdmin = false }: ProtectedRouteProps) => {
  const isAuthenticated = authService.isAuthenticated();
  const isAdmin = authService.isAdmin();

  // Si no está autenticado, redirigir al login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Si la ruta requiere admin y el usuario no es admin, redirigir a tickets
  if (requireAdmin && !isAdmin) {
    return <Navigate to="/tickets" replace />;
  }

  // Usuario tiene acceso, renderizar el componente
  return <>{children}</>;
};

export default ProtectedRoute;
