import React from 'react';

interface PanelProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  headerAction?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  /** accent: 'blue' (default) | 'red' (critical) | 'gold' (priority) | 'green' (confirmed) */
  accent?: 'blue' | 'red' | 'gold' | 'green' | 'none';
}

const accentBorder: Record<string, string> = {
  blue:  'border-l-civix-blue',
  red:   'border-l-civix-red',
  gold:  'border-l-civix-gold',
  green: 'border-l-civix-green',
  none:  '',
};

export const Panel: React.FC<PanelProps> = ({
  title,
  subtitle,
  headerAction,
  children,
  className = '',
  accent = 'none',
  ...props
}) => {
  const leftAccent = accent !== 'none' ? `border-l-2 ${accentBorder[accent]}` : '';

  return (
    <div
      className={`civix-panel ${leftAccent} ${className}`}
      {...props}
    >
      {(title || headerAction) && (
        <div className="civix-panel-header">
          <div>
            {title && (
              <h3 className="civix-panel-title">{title}</h3>
            )}
            {subtitle && (
              <p className="civix-panel-subtitle">{subtitle}</p>
            )}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
};
