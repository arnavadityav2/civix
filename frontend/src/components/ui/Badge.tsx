import React from 'react';

export type BadgeVariant = 
  | 'confirmed' 
  | 'active' 
  | 'warning' 
  | 'critical' 
  | 'deferred' 
  | 'closed' 
  | 'person' 
  | 'org' 
  | 'device' 
  | 'phone' 
  | 'financial' 
  | 'vehicle' 
  | 'source' 
  | 'default';

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

// Dark institutional badge styles — NO PURPLE
const variantStyles: Record<BadgeVariant, string> = {
  // GREEN = verified / confirmed
  confirmed: 'bg-civix-green-subtle text-civix-green-light border-civix-green-muted',
  // BLUE = active / operational
  active:    'bg-civix-blue-subtle text-civix-blue-light border-civix-blue-muted',
  // GOLD = priority / warning / review
  warning:   'bg-civix-gold-subtle text-civix-gold border-civix-gold-muted',
  // RED = critical / urgent
  critical:  'bg-civix-red-subtle text-civix-red-light border-civix-red-muted',
  // GOLD = deferred / review (was purple — now gold as priority state)
  deferred:  'bg-civix-gold-subtle text-civix-gold border-civix-gold-muted',
  // SLATE = closed / inactive
  closed:    'bg-civix-surface-3 text-civix-text-muted border-civix-border',
  // Entity types
  person:    'bg-civix-blue-subtle text-civix-blue-light border-civix-blue-muted',
  org:       'bg-civix-gold-subtle text-civix-gold border-civix-gold-muted',
  // device was purple — now blue (analytical/technical context)
  device:    'bg-civix-blue-subtle text-civix-blue-light border-civix-blue-muted',
  phone:     'bg-civix-green-subtle text-civix-green-light border-civix-green-muted',
  financial: 'bg-civix-gold-subtle text-civix-gold-light border-civix-gold-muted',
  vehicle:   'bg-civix-red-subtle text-civix-red-light border-civix-red-muted',
  source:    'bg-civix-surface-2 text-civix-text-secondary border-civix-border',
  default:   'bg-civix-surface-2 text-civix-text-secondary border-civix-border',
};

export const Badge: React.FC<BadgeProps> = ({ variant = 'default', children, className = '' }) => {
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded-sm text-[10px] font-bold border uppercase tracking-widest font-mono ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
