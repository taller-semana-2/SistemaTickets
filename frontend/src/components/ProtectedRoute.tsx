import { useEffect } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { authService, getAccessToken } from '../services/auth';

const isTokenExpired = (token: string): boolean => {
  try {
    const payloadBase64 = token.split('.')[1];
    if (!payloadBase64) {
      return true;
    }

    const payload = JSON.parse(atob(payloadBase64.replace(/-/g, '+').replace(/_/g, '/'))) as {
      exp?: number;
    };

    if (!payload.exp) {
      return true;
    }

    return payload.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
};

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
  const navigate = useNavigate();
  const currentUser = authService.getCurrentUser();
  const accessToken = getAccessToken();
  const hasValidToken = accessToken !== null && !isTokenExpired(accessToken);
  const isAuthenticated = authService.isAuthenticated();
  const isAdmin = currentUser?.role === 'ADMIN';

  const shouldDenyAdmin = requireAdmin && !isAdmin && isAuthenticated && hasValidToken && !!currentUser;

  useEffect(() => {
    if (shouldDenyAdmin) {
      alert('Acceso denegado: no tienes permisos de administrador para acceder a esta página.');
      navigate('/tickets', { replace: true });
    }
  }, [shouldDenyAdmin, navigate]);

  // Si no está autenticado o no tiene token válido, redirigir al login
  if (!isAuthenticated || !hasValidToken || !currentUser) {
    authService.logout();
    return <Navigate to="/login" replace />;
  }

  // Si la ruta requiere admin y el usuario no es admin, mostrar mensaje y redirigir
  if (shouldDenyAdmin) {
    return null;
  }

  // Usuario tiene acceso, renderizar el componente
  return <>{children}</>;
};

export default ProtectedRoute;
