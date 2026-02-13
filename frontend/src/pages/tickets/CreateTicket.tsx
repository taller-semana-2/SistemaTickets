import { useNavigate } from "react-router-dom";
import { useState } from "react";
import TicketForm from "./TicketForm";
import { ticketApi } from "../../services/ticketApi";
import { authService } from "../../services/auth";
import type { CreateTicketDTO } from "../../types/ticket";
import { useNotifications } from "../../context/NotificacionContext";
import "./CreateTicket.css";

const CreateTicket = () => {
  const navigate = useNavigate();
  const { refreshUnread } = useNotifications();
  const [error, setError] = useState("");

  const handleCreate = async (data: Omit<CreateTicketDTO, "user_id">) => {
    try {
      const currentUser = authService.getCurrentUser();

      if (!currentUser) {
        setError("Debes iniciar sesión para crear un ticket");
        navigate("/login");
        return;
      }

      const ticketData: CreateTicketDTO = {
        ...data,
        user_id: currentUser.id,
      };

      await ticketApi.createTicket(ticketData);

      refreshUnread();

      navigate("/tickets");
    } catch (err: any) {
      console.error("Error creating ticket:", err);
      setError(err.response?.data?.error || "Error al crear el ticket");
    }
  };

  return (
    <div className="page-container">
      <div className="create-ticket-header">
        <h1 className="create-ticket-title">Crear Nuevo Ticket</h1>
        <p className="create-ticket-subtitle">
          Completa el formulario para crear un nuevo ticket de soporte
        </p>
      </div>

      {error && (
        <div
          className="error-message"
          style={{
            backgroundColor: "#fee2e2",
            border: "1px solid #ef4444",
            color: "#dc2626",
            padding: "12px",
            borderRadius: "8px",
            marginBottom: "16px",
          }}
        >
          {error}
        </div>
      )}

      <TicketForm onSubmit={handleCreate} />
    </div>
  );
};

export default CreateTicket;
