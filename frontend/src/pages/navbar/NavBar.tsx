import { NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from 'react';
import { notificationsApi } from '../../services/notification';
import { authService } from '../../services/auth';
import type { User } from '../../types/auth';
import "./NavBar.css";

const Navbar = () => {
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  const loadUnreadCount = async () => {
    try {
      const notifications = await notificationsApi.getNotifications();
      const unread = notifications.filter((n) => !n.read).length;
      setUnreadCount(unread);
    } catch (error) {
      console.error('Error cargando notificaciones', error);
    }
  };

  useEffect(() => {
    // Cargar usuario actual
    const user = authService.getCurrentUser();
    setCurrentUser(user);
    
    loadUnreadCount();
  }, []);

  const handleLogout = () => {
    authService.logout();
    navigate('/login', { replace: true });
  };

  // Determinar si el usuario es admin
  const isAdmin = currentUser?.role === 'ADMIN';

  return (
    <nav className="navbar">
      <div className="navbar__brand">
        <NavLink to="/tickets" className="navbar__logo">
          TicketSystem
        </NavLink>
      </div>

      <ul className="navbar__links">
        {/* Tickets - Visible para todos */}
        <li>
          <NavLink
            to="/tickets"
            end
            className={({ isActive }) =>
              isActive ? "navbar__link active" : "navbar__link"
            }
          >
             Tickets
          </NavLink>
        </li>

        {/* Crear Ticket - Visible para todos */}
        <li>
          <NavLink
            to="/tickets/new"
            className={({ isActive }) =>
              isActive ? "navbar__link active" : "navbar__link"
            }
          >
             Crear Ticket
          </NavLink>
        </li>

        {/* Notificaciones - Solo ADMIN */}
        {isAdmin && (
          <li>
            <NavLink
              to="/notifications"
              className={({ isActive }) =>
                isActive ? "navbar__link active" : "navbar__link"
              }
            >
              🔔 Notificaciones
              {unreadCount > 0 && (
                <span className="navbar__badge">{unreadCount}</span>
              )}
            </NavLink>
          </li>
        )}

        {/* Asignaciones - Solo ADMIN */}
        {isAdmin && (
          <li>
            <NavLink
              to="/assignments"
              className={({ isActive }) =>
                isActive ? "navbar__link active" : "navbar__link"
              }
            >
               Asignaciones
            </NavLink>
          </li>
        )}

        {currentUser && (
          <li className="navbar__user">
            <span className="navbar__username">
              👤 {currentUser.username}
              {currentUser.role === 'ADMIN' && (
                <span className="navbar__admin-badge">Admin</span>
              )}
            </span>
          </li>
        )}

        <li className="navbar__logout">
          <button
            onClick={handleLogout}
            className="navbar__link navbar__link--logout"
          >
             Cerrar Sesión
          </button>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
