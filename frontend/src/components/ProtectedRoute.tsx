import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

/**
 * Route guard based on authentication and role.
 *
 * @param children - Component to render if access is granted.
 * @param requireAdmin - If true, only ADMIN role users can access.
 */
const ProtectedRoute = ({ children, requireAdmin = false }: ProtectedRouteProps) => {
  const { user, loading, isAuthenticated, isAdmin } = useAuth();

  // Wait for AuthContext to verify session via /api/auth/me/
  if (loading) {
    return <div className="loading-screen">Cargando...</div>;
  }

  // Not authenticated — redirect to login
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  // Route requires admin but user is not admin
  if (requireAdmin && !isAdmin) {
    return <Navigate to="/tickets" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
