import React from 'react';

export type HierarchyTier = 'SOURCE_EVIDENCE' | 'DETERMINISTIC_FINDING' | 'MODEL_SIGNAL' | 'AI_EXPLANATION';

interface HierarchyBadgeProps {
  tier: HierarchyTier;
  className?: string;
}

const tierConfig: Record<HierarchyTier, { label: string; styles: string }> = {
  SOURCE_EVIDENCE: {
    label: 'SOURCE EVIDENCE',
    styles: 'bg-slate-900 text-slate-100 border-slate-900 font-mono text-[10px]'
  },
  DETERMINISTIC_FINDING: {
    label: 'DETERMINISTIC FINDING',
    styles: 'bg-emerald-700 text-white border-emerald-800 font-mono text-[10px]'
  },
  MODEL_SIGNAL: {
    label: 'MODEL SIGNAL',
    styles: 'bg-amber-600 text-white border-amber-700 font-mono text-[10px]'
  },
  AI_EXPLANATION: {
    label: 'AI EXPLANATION',
    styles: 'bg-purple-700 text-white border-purple-800 font-mono text-[10px]'
  }
};

export const HierarchyBadge: React.FC<HierarchyBadgeProps> = ({ tier, className = '' }) => {
  const config = tierConfig[tier];
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded border uppercase font-bold tracking-widest ${config.styles} ${className}`}>
      {config.label}
    </span>
  );
};
