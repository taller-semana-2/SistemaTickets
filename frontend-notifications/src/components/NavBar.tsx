import { NavLink } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { notificationApi } from '../api/notificationApi';
import './NavBar.css';

const Navbar = () => {
  const [unreadCount, setUnreadCount] = useState(0);

  const loadUnreadCount = async () => {
    try {
      const notifications = await notificationApi.getNotifications();
      const unread = notifications.filter((n) => !n.read).length;
      setUnreadCount(unread);
    } catch (error) {
      console.error("Error cargando notificaciones", error);
    }
  };

  useEffect(() => {
    loadUnreadCount();
  }, []);

  return (
    <nav className="navbar">
      {/* Sección de Marca/Título */}
      <div className="navbar__brand">
        <NavLink to="/notifications" className="navbar__logo">
          Sistema de Notificaciones
        </NavLink>
      </div>

      {/* Lista de Enlaces */}
      <ul className="navbar__links">
        <li>
          <NavLink
            to="/notifications"
            className={({ isActive }) =>
              isActive ? 'navbar__link active' : 'navbar__link'
            }
          >
            Notificaciones
            {unreadCount > 0 && (
              <span className="navbar__badge">{unreadCount}</span>
            )}
          </NavLink>
        </li>

        <li>
          <NavLink
            to="/assignments"
            className={({ isActive }) =>
              isActive ? 'navbar__link active' : 'navbar__link'
            }
          >
            Asignaciones
          </NavLink>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;