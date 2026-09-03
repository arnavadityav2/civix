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
    <div className="space-y-6">


      {/* Hero Attention Card: Priority Investigative Lead (Maximizing Hierarchy & Action) */}
      <div className="w-full">
        <PriorityLeadsWidget />
      </div>

      {/* Core Split 1: Active Cases + Relationship Network Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <ActiveInvestigationsWidget />
        </div>
        <div className="lg:col-span-5">
          <div className="bg-white border border-slate-200 rounded p-4 shadow-sm h-full flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3 border-b border-slate-100 pb-2">
              <div>
                <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                  CURRENT INVESTIGATION RELATIONSHIPS
                </h3>
                <p className="text-[11px] text-slate-500 font-mono">
                  Verified Node & Relationship Intelligence
                </p>
              </div>
              <Network className="w-4 h-4 text-slate-400" />
            </div>
            <StructuredGraphView />
          </div>
        </div>
      </div>

      {/* Core Split 2: Knowledge Graph (Neo4j) + Recent Evidence Log */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <InvestigationGraphWidget />
        </div>
        <div className="lg:col-span-5">
          <RecentEvidenceWidget />
        </div>
      </div>

      {/* Bottom Split: System Audit Trail + Operational Health */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
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
