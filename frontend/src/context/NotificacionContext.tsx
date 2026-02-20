import { createContext, useContext, useState } from "react";

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

  // Expose a way to manually increment the trigger from anywhere (SSE, UI actions)
  const refreshUnread = () => setTrigger((t) => t + 1);

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
