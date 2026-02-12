import { NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from 'react';
import { notificationsApi } from '../api/notification';
import "./NavBar.css";

const Navbar = () => {
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);

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
    loadUnreadCount();
  }, []);

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
            className={({ isActive }) =>
              isActive ? "navbar__link active" : "navbar__link"
            }
          >
             Tickets
          </NavLink>
        </li>

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

        <li className="navbar__logout">
          <button
            onClick={() => {
              // TODO: Limpiar token/sesión del localStorage
              navigate('/login');
            }}
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
