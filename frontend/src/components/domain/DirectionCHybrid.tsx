import React from 'react';
import { ActiveInvestigationsWidget } from './ActiveInvestigationsWidget';
import { RecentEvidenceWidget } from './RecentEvidenceWidget';
import { InvestigationGraphWidget } from './InvestigationGraphWidget';
import { AuditTrailWidget } from './AuditTrailWidget';
import { PriorityLeadsWidget } from './PriorityLeadsWidget';
import { SystemHealthWidget } from './SystemHealthWidget';
import { StructuredGraphView } from './StructuredGraphView';
import { Network } from 'lucide-react';

export const DirectionCHybrid: React.FC = () => {
  return (
    <div className="space-y-5">

      {/* ── PRIORITY INVESTIGATIVE SIGNAL (top — full width hero) */}
      <PriorityLeadsWidget />

      {/* ── CORE SPLIT 1: Active Investigations + Relationship Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-7">
          <ActiveInvestigationsWidget />
        </div>
        <div className="lg:col-span-5">
          <div className="civix-panel h-full flex flex-col">
            <div className="civix-panel-header">
              <div>
                <h3 className="civix-panel-title">CURRENT INVESTIGATION RELATIONSHIPS</h3>
                <p className="civix-panel-subtitle">Verified Node & Relationship Intelligence</p>
              </div>
              <Network className="w-4 h-4 text-civix-text-muted" />
            </div>
            <div className="p-4 flex-1">
              <StructuredGraphView />
            </div>
          </div>
        </div>
      </div>

      {/* ── CORE SPLIT 2: Entity Network Graph + Evidence Log */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-7">
          <InvestigationGraphWidget />
        </div>
        <div className="lg:col-span-5">
          <RecentEvidenceWidget />
        </div>
      </div>

      {/* ── BOTTOM SPLIT: Audit Trail + System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-7">
          <AuditTrailWidget />
        </div>
        <div className="lg:col-span-5">
          <SystemHealthWidget />
        </div>
      </div>
    </div>
  );
};
