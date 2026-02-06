import { NavLink } from "react-router-dom";
import "./NavBar.css";

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar__brand">
        <NavLink to="/tickets" className="navbar__logo">
          TicketSystem
        </NavLink>
      </div>

      <ul className="navbar__links">
        {/* Rutas internas */}
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

        {/* Cambio de app */}
        <li className="navbar__separator" />

        <li>
          <a
            href="http://localhost:5174"
            className="navbar__link navbar__external"
          >
            🔔 Notificaciones
          </a>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
