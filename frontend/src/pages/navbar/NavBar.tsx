import { NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState, useCallback } from "react";
import { notificationsApi } from "../../services/notification";
import { useNotifications } from "../../context/NotificacionContext";
import { useAuth } from "../../context/AuthContext";
import "./NavBar.css";

const Navbar = () => {
  const navigate = useNavigate();
  const { trigger } = useNotifications();

  const [unreadCount, setUnreadCount] = useState(0);
  const [menuOpen, setMenuOpen] = useState(false);
  const { user: currentUser, isAdmin, logout, isAuthenticated } = useAuth();

  const loadUnreadCount = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const notifications = await notificationsApi.getNotifications();
      const unread = notifications.filter((n) => !n.read).length;
      setUnreadCount(unread);
    } catch (error) {
      console.error("Error cargando notificaciones", error);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    loadUnreadCount();
  }, [loadUnreadCount, trigger]);

  const handleLogout = async () => {
    closeMenu();
    await logout();
    navigate("/login", { replace: true });
  };

  const toggleMenu = () => setMenuOpen((prev) => !prev);
  const closeMenu = () => setMenuOpen(false);

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
