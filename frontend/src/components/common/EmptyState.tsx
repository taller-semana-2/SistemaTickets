interface EmptyStateProps {
  message: string;
  icon?: string;
}

const EmptyState = ({ message, icon }: EmptyStateProps) => {
  return (
    <div className="status-container">
      {icon ? (
        <div className="empty-state">
          <span className="empty-icon">{icon}</span>
          <p>{message}</p>
        </div>
      ) : (
        <p>{message}</p>
      )}
    </div>
  );
};

export default EmptyState;
