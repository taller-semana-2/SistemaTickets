import { NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useFetch } from "../../hooks/useFetchOnce";
import { notificationsApi } from "../../services/notification";
import { authService } from "../../services/auth";
import { useNotifications } from "../../context/NotificacionContext";
import type { User } from "../../types/auth";
import "./NavBar.css";

const Navbar = () => {
  const navigate = useNavigate();
  const { trigger } = useNotifications();

  const [unreadCount, setUnreadCount] = useState(0);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  /**
   * Carga el conteo de notificaciones no leídas con AbortController
   */
  const loadUnreadCount = async (signal?: AbortSignal) => {
    if (!authService.isAuthenticated()) return;
    try {
      const notifications = await notificationsApi.getNotifications(signal);
      const unread = notifications.filter((n) => !n.read).length;
      setUnreadCount(unread);
    } catch (error) {
      // Ignorar errores de cancelación
      if ((error as Error).name !== 'AbortError') {
        console.error("Error cargando notificaciones", error);
      }
    }
  };

  useEffect(() => {
    const user = authService.getCurrentUser();
    setCurrentUser(user);
  }, []);

  // Cargar conteo de notificaciones una sola vez en el montaje (con AbortController)
  useFetch(
    async (signal) => {
      if (!authService.isAuthenticated()) return;
      const notifications = await notificationsApi.getNotifications(signal);
      return notifications;
    },
    (notifications) => {
      if (notifications) {
        const unread = notifications.filter((n) => !n.read).length;
        setUnreadCount(unread);
      }
    },
    (error) => {
      console.error("Error cargando notificaciones", error);
    }
  );

  // Recargar conteo cuando trigger cambie (actualizaciones en tiempo real)
  useEffect(() => {
    if (trigger > 0) {
      loadUnreadCount();
    }
  }, [trigger]);

  const handleLogout = () => {
    authService.logout();
    navigate("/login", { replace: true });
  };

  const toggleMenu = () => setMenuOpen((prev) => !prev);
  const closeMenu = () => setMenuOpen(false);

  const isAdmin = currentUser?.role === "ADMIN";

  return (
    <nav className="navbar">
      <div className="navbar__brand">
        <NavLink to="/tickets" className="navbar__logo" onClick={closeMenu}>
          TicketSystem
        </NavLink>
      </div>

      <button
        className={`navbar__hamburger ${menuOpen ? "open" : ""}`}
        onClick={toggleMenu}
        aria-label="Toggle menu"
        aria-expanded={menuOpen}
      >
        <span className="navbar__hamburger-line" />
        <span className="navbar__hamburger-line" />
        <span className="navbar__hamburger-line" />
      </button>

      {menuOpen && (
        <div className="navbar__overlay" onClick={closeMenu} />
      )}

      <ul className={`navbar__links ${menuOpen ? "navbar__links--open" : ""}`}>
        <li>
          <NavLink
            to="/tickets"
            end
            className={({ isActive }) =>
              isActive ? "navbar__link active" : "navbar__link"
            }
            onClick={closeMenu}
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
            onClick={closeMenu}
          >
            Crear Ticket
          </NavLink>
        </li>

        {isAdmin && (
          <li>
            <NavLink
              to="/notifications"
              className={({ isActive }) =>
                isActive ? "navbar__link active" : "navbar__link"
              }
              onClick={closeMenu}
            >
              🔔 Notificaciones
              {unreadCount > 0 && (
                <span className="navbar__badge">{unreadCount}</span>
              )}
            </NavLink>
          </li>
        )}

        {isAdmin && (
          <li>
            <NavLink
              to="/assignments"
              className={({ isActive }) =>
                isActive ? "navbar__link active" : "navbar__link"
              }
              onClick={closeMenu}
            >
              Asignaciones
            </NavLink>
          </li>
        )}

        {currentUser && (
          <li className="navbar__user">
            <span className="navbar__username">
              👤 {currentUser.username}
              {currentUser.role === "ADMIN" && (
                <span className="navbar__admin-badge">Admin</span>
              )}
            </span>
          </li>
        )}

        <li className="navbar__logout">
          <button
            onClick={() => { handleLogout(); closeMenu(); }}
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
