interface EmptyStateProps {
  message: string;
  icon?: string;
}

const EmptyState = ({ message, icon }: EmptyStateProps) => {
  const renderIcon = () => {
    switch (icon) {
      case 'check_circle':
        return '✅';
      case 'info':
        return 'ℹ️';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      case 'inbox':
        return '📥';
      default:
        return icon;
    }
  };

  return (
    <div className="status-container">
      {icon ? (
        <div className="empty-state">
          <span className="empty-icon" role="img" aria-label={icon}>
            {renderIcon()}
          </span>
          <p>{message}</p>
        </div>
      ) : (
        <p>{message}</p>
      )}
    </div>
  );
};

export default EmptyState;
