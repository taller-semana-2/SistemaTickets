import { type ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string | ReactNode;
  action?: ReactNode;
}

const PageHeader = ({ title, subtitle, action }: PageHeaderProps) => {
  return (
    <header className="list-header">
      <div>
        <h1>{title}</h1>
        {subtitle && (
          typeof subtitle === 'string' ? (
            <span className="ticket-count">{subtitle}</span>
          ) : (
            <div className="ticket-count">{subtitle}</div>
          )
        )}
      </div>
      {action && <div>{action}</div>}
    </header>
  );
};

export default PageHeader;
