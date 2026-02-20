import { createContext, useContext, useState, useEffect } from "react";
import { authService } from "../services/auth";

type NotificationContextType = {
  trigger: number;
  refreshUnread: () => void;
};

const NotificationContext = createContext<NotificationContextType | null>(null);

export const NotificationProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const [trigger, setTrigger] = useState(0);
  const user = authService.getCurrentUser();

  const refreshUnread = () => setTrigger((t) => t + 1);

  // SSE connection for instant real-time updates
  useEffect(() => {
    if (!user || user.role !== "ADMIN") return;

    // Conectar al endpoint SSE pasando el user_id en la URL
    const sseUrl = `http://localhost:8001/api/notifications/sse/${user.id}/`;
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      // Si el mensaje es un hearbeat no hace nada, sino recarga
      if (event.data !== "heartbeat") {
        refreshUnread();
      }
    };

    eventSource.addEventListener("notification", () => {
        refreshUnread();
    });

    eventSource.onerror = (error) => {
      console.error("SSE connection error", error);
      eventSource.close();
      // Reconnection is handled natively by EventSource, but we close it and rely on effect retrigger
      // Optionally we could use setTimeout to reconnect.
    };

    return () => {
      eventSource.close();
    };
  }, [user]);

  return (
    <NotificationContext.Provider value={{ trigger, refreshUnread }}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotifications = () => {
  const ctx = useContext(NotificationContext);
  if (!ctx) {
    throw new Error(
      "useNotifications must be used within NotificationProvider"
    );
  }
  return ctx;
};
