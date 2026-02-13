import { useState, useEffect } from 'react';
import { userService } from '../services/user';
import type { AdminUser } from '../services/user';
import './TicketAssign.css';

interface TicketAssignProps {
  ticketId?: number;
  currentAssignedId?: string;
  onAssign?: (userId: string) => void;
}

const TicketAssign = ({ ticketId, currentAssignedId, onAssign }: TicketAssignProps) => {
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>(currentAssignedId || '');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAdminUsers = async () => {
      try {
        setLoading(true);
        setError(null);
        const users = await userService.getAdminUsers();
        setAdminUsers(users);
      } catch (err) {
        console.error('Error cargando usuarios ADMIN:', err);
        setError('No se pudieron cargar los administradores');
      } finally {
        setLoading(false);
      }
    };

    fetchAdminUsers();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const userId = e.target.value;
    setSelectedUserId(userId);
    
    if (onAssign) {
      onAssign(userId);
    }
  };

  if (loading) {
    return (
      <div className="ticket-assign">
        <label className="ticket-assign__label">Asignar a:</label>
        <div className="ticket-assign__loading">Cargando usuarios...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ticket-assign">
        <label className="ticket-assign__label">Asignar a:</label>
        <p className="ticket-assign__info" style={{ color: '#ef4444' }}>
          {error}
        </p>
      </div>
    );
  }

  return (
    <div className="ticket-assign">
      <label htmlFor="admin-select" className="ticket-assign__label">
        Asignar a:
      </label>
      <select
        id="admin-select"
        className="ticket-assign__select"
        value={selectedUserId}
        onChange={handleChange}
      >
        <option value="">-- Seleccionar administrador --</option>
        {adminUsers.map((user) => (
          <option key={user.id} value={user.id}>
            {user.username} ({user.email})
          </option>
        ))}
      </select>
      
      {ticketId && (
        <p className="ticket-assign__info">
          {selectedUserId 
            ? `Ticket #${ticketId} será asignado al administrador seleccionado`
            : 'Selecciona un administrador para asignar este ticket'
          }
        </p>
      )}
    </div>
  );
};

export default TicketAssign;
