import { NavLink, useNavigate } from 'react-router-dom';
import { useEffect, useState, useCallback } from 'react';
import { notificationsApi } from '../../services/notification';
import { useAuth } from '../../context/AuthContext';
import { useNotifications } from '../../context/NotificacionContext';
import './NavBar.css';

const Navbar = () => {
  const navigate = useNavigate();
  const { trigger } = useNotifications();
  const { user, logout, isAdmin } = useAuth();

  const [unreadCount, setUnreadCount] = useState(0);

  const loadUnreadCount = useCallback(async () => {
    try {
      const notifications = await notificationsApi.getNotifications();
      const unread = notifications.filter((n) => !n.read).length;
      setUnreadCount(unread);
    } catch (error) {
      console.error('Error cargando notificaciones', error);
    }
  }, []);

  useEffect(() => {
    loadUnreadCount();
  }, [loadUnreadCount, trigger]);

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <nav className="navbar">
      <div className="navbar__brand">
        <NavLink to="/tickets" className="navbar__logo">
          TicketSystem
        </NavLink>
      </div>
      <ul className="navbar__links">
        <li>
          <NavLink
            to="/tickets"
            end
            className={({ isActive }) => (isActive ? 'navbar__link active' : 'navbar__link')}
          >
            Tickets
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/tickets/new"
            className={({ isActive }) => (isActive ? 'navbar__link active' : 'navbar__link')}
          >
            Crear Ticket
          </NavLink>
        </li>
        {isAdmin && (
          <li>
            <NavLink
              to="/notifications"
              className={({ isActive }) => (isActive ? 'navbar__link active' : 'navbar__link')}
            >
              🔔 Notificaciones
              {unreadCount > 0 && <span className="navbar__badge">{unreadCount}</span>}
            </NavLink>
          </li>
        )}
        {isAdmin && (
          <li>
            <NavLink
              to="/assignments"
              className={({ isActive }) => (isActive ? 'navbar__link active' : 'navbar__link')}
            >
              Asignaciones
            </NavLink>
          </li>
        )}
        {user && (
          <li className="navbar__user">
            <span className="navbar__username">
              👤 {user.username}
              {user.role === 'ADMIN' && <span className="navbar__admin-badge">Admin</span>}
            </span>
          </li>
        )}
        <li className="navbar__logout">
          <button onClick={handleLogout} className="navbar__link navbar__link--logout">
            Cerrar Sesión
          </button>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
