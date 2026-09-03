import React from 'react';
import { Panel } from '../components/ui/Panel';
import { Badge } from '../components/ui/Badge';
import { HierarchyBadge } from '../components/domain/HierarchyBadge';

export const FoundationTestPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <Panel
        title="CIVIX 2.0 — Foundation Clean Reset Verified"
        subtitle="Frontend architecture reset to light-first institutional standards"
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-700 leading-relaxed">
            The frontend has been successfully initialized from absolute zero. All legacy prototype code has been removed.
            The foundation adheres strictly to the Master Design System: Light-first surfaces, restrained 4px borders, navy accents, and zero glassmorphism.
          </p>

          <div className="border-t border-slate-200 pt-4">
            <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-2">
              Visual Hierarchy Standard Verification
            </h4>
            <div className="flex flex-wrap gap-2 items-center">
              <HierarchyBadge tier="SOURCE_EVIDENCE" />
              <span className="text-xs text-slate-400">➔</span>
              <HierarchyBadge tier="DETERMINISTIC_FINDING" />
              <span className="text-xs text-slate-400">➔</span>
              <HierarchyBadge tier="MODEL_SIGNAL" />
              <span className="text-xs text-slate-400">➔</span>
              <HierarchyBadge tier="AI_EXPLANATION" />
            </div>
          </div>

          <div className="border-t border-slate-200 pt-4">
            <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-2">
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
