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

const variantStyles: Record<BadgeVariant, string> = {
  confirmed: 'bg-emerald-50 text-emerald-800 border-emerald-300',
  active:    'bg-blue-50 text-blue-800 border-blue-300',
  warning:   'bg-amber-50 text-amber-800 border-amber-300',
  critical:  'bg-red-50 text-red-800 border-red-300',
  deferred:  'bg-purple-50 text-purple-800 border-purple-300',
  closed:    'bg-slate-100 text-slate-700 border-slate-300',
  person:    'bg-blue-50 text-blue-700 border-blue-200',
  org:       'bg-amber-50 text-amber-800 border-amber-200',
  device:    'bg-purple-50 text-purple-700 border-purple-200',
  phone:     'bg-emerald-50 text-emerald-700 border-emerald-200',
  financial: 'bg-yellow-50 text-yellow-800 border-yellow-300',
  vehicle:   'bg-red-50 text-red-700 border-red-200',
  source:    'bg-slate-50 text-slate-700 border-slate-200',
  default:   'bg-slate-100 text-slate-800 border-slate-200',
};

export const Badge: React.FC<BadgeProps> = ({ variant = 'default', children, className = '' }) => {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border uppercase tracking-wider ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
};
