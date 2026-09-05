import React from 'react';

export type HierarchyTier = 'SOURCE_EVIDENCE' | 'DETERMINISTIC_FINDING' | 'MODEL_SIGNAL' | 'AI_EXPLANATION';

interface HierarchyBadgeProps {
  tier: HierarchyTier;
  className?: string;
}

// Semantic tier hierarchy — NO PURPLE anywhere
const tierConfig: Record<HierarchyTier, { label: string; styles: string }> = {
  // Darkest / most authoritative — source material
  SOURCE_EVIDENCE: {
    label: 'SOURCE EVIDENCE',
    styles: 'bg-civix-surface-3 text-civix-text-primary border-civix-border-strong font-mono text-[9px]'
  },
  // Green = verified, confirmed, reliable finding
  DETERMINISTIC_FINDING: {
    label: 'DETERMINISTIC FINDING',
    styles: 'bg-civix-green-subtle text-civix-green-light border-civix-green-muted font-mono text-[9px]'
  },
  // Gold = ML signal, priority attention — not yet confirmed
  MODEL_SIGNAL: {
    label: 'MODEL SIGNAL',
    styles: 'bg-civix-gold-subtle text-civix-gold border-civix-gold-muted font-mono text-[9px]'
  },
  // Blue = analytical context — was purple, now institutional blue
  AI_EXPLANATION: {
    label: 'AI EXPLANATION',
    styles: 'bg-civix-blue-subtle text-civix-blue-light border-civix-blue-muted font-mono text-[9px]'
  }
};

export const HierarchyBadge: React.FC<HierarchyBadgeProps> = ({ tier, className = '' }) => {
  const config = tierConfig[tier];
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded-sm border uppercase font-bold tracking-widest ${config.styles} ${className}`}>
      {config.label}
    </span>
  );
};
