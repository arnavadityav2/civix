import React from 'react';
import { Panel } from '../components/ui/Panel';
import { Badge } from '../components/ui/Badge';
import { HierarchyBadge } from '../components/domain/HierarchyBadge';

export const FoundationTestPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      <Panel
        title="CIVIX 2.0 — Dark Institutional Foundation Verified"
        subtitle="Frontend architecture aligned with Dark + Institutional + Indian Police visual authority"
      >
        <div className="space-y-4">
          <p className="text-sm text-civix-text-main leading-relaxed">
            The frontend visual design has been successfully transformed.
            The foundation adheres strictly to the Dark Institutional Master Design System: dark slate surfaces (`bg-civix-bg`, `bg-civix-surface`), flat 1px borders (`civix-border`), Ashoka gold identity highlights, deep technical blue accents, and zero light-mode UI drift.
          </p>

          <div className="border-t border-civix-border pt-4">
            <h4 className="text-xs font-bold text-civix-text-muted uppercase tracking-wider mb-2">
              Visual Hierarchy Standard Verification
            </h4>
            <div className="flex flex-wrap gap-2 items-center">
              <HierarchyBadge tier="SOURCE_EVIDENCE" />
              <span className="text-xs text-civix-text-muted">➔</span>
              <HierarchyBadge tier="DETERMINISTIC_FINDING" />
              <span className="text-xs text-civix-text-muted">➔</span>
              <HierarchyBadge tier="MODEL_SIGNAL" />
              <span className="text-xs text-civix-text-muted">➔</span>
              <HierarchyBadge tier="AI_EXPLANATION" />
            </div>
          </div>

          <div className="border-t border-civix-border pt-4">
            <h4 className="text-xs font-bold text-civix-text-muted uppercase tracking-wider mb-2">
              Institutional Status & Entity Type Badges
            </h4>
            <div className="flex flex-wrap gap-2">
              <Badge variant="confirmed">Confirmed</Badge>
              <Badge variant="active">Active</Badge>
              <Badge variant="warning">Warning</Badge>
              <Badge variant="critical">Critical</Badge>
              <Badge variant="deferred">Deferred</Badge>
              <Badge variant="closed">Closed</Badge>
              <Badge variant="person">Person</Badge>
              <Badge variant="org">Organization</Badge>
              <Badge variant="device">Device</Badge>
              <Badge variant="phone">Phone</Badge>
            </div>
          </div>
        </div>
      </Panel>
    </div>
  );
};
