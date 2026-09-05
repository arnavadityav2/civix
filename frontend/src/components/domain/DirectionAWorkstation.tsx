import React from 'react';
import { ActiveInvestigationsWidget } from './ActiveInvestigationsWidget';
import { RecentEvidenceWidget } from './RecentEvidenceWidget';
import { InvestigationGraphWidget } from './InvestigationGraphWidget';
import { AuditTrailWidget } from './AuditTrailWidget';
import { PriorityLeadsWidget } from './PriorityLeadsWidget';
import { SystemHealthWidget } from './SystemHealthWidget';
import { StructuredGraphView } from './StructuredGraphView';

export const DirectionAWorkstation: React.FC = () => {
  return (
    <div className="space-y-4">
      {/* Top Notification Banner / Workstation Control Header */}
      <div className="civix-panel bg-civix-surface-2 px-4 py-2 flex flex-wrap items-center justify-between text-xs font-mono">
        <div className="flex items-center space-x-3">
          <span className="bg-civix-gold-500 text-civix-bg px-2 py-0.5 rounded-sm font-bold">MODE: HIGH DENSITY WORKSTATION</span>
          <span className="text-civix-text-secondary">Target: Rapid Case Scanning & Lead Disposition</span>
        </div>
        <div className="flex items-center space-x-4 text-civix-text-muted">
          <span>Active Case Filter: ALL</span>
          <span>RLS Context: ACTIVE</span>
        </div>
      </div>

      {/* Top Split Layout: Priority Leads (Hero) + Recent Evidence */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-8">
          <PriorityLeadsWidget />
        </div>
        <div className="lg:col-span-4">
          <RecentEvidenceWidget />
        </div>
      </div>

      {/* Middle Split Layout: Active Investigations + Structured Relationship Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-6">
          <ActiveInvestigationsWidget />
        </div>
        <div className="lg:col-span-6">
          <div className="civix-panel p-4 h-full flex flex-col justify-between">
            <div className="civix-panel-header">
              <h3 className="civix-panel-title">
                RELATIONSHIP INTELLIGENCE CANVAS
              </h3>
              <span className="text-[10px] font-mono text-civix-text-muted uppercase">Interactive Network</span>
            </div>
            <StructuredGraphView />
          </div>
        </div>
      </div>

      {/* Bottom Layout: Graph & System Health / Audit */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-6">
          <InvestigationGraphWidget />
        </div>
        <div className="lg:col-span-3">
          <AuditTrailWidget />
        </div>
        <div className="lg:col-span-3">
          <SystemHealthWidget />
        </div>
      </div>
    </div>
  );
};
