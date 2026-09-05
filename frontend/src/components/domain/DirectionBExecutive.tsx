import React from 'react';
import { ActiveInvestigationsWidget } from './ActiveInvestigationsWidget';
import { PriorityLeadsWidget } from './PriorityLeadsWidget';
import { StructuredGraphView } from './StructuredGraphView';
import { SystemHealthWidget } from './SystemHealthWidget';
import { AuditTrailWidget } from './AuditTrailWidget';
import { ShieldCheck, Award, Briefcase, FileCheck } from 'lucide-react';

export const DirectionBExecutive: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Executive Briefing Banner */}
      <div className="civix-panel border-l-4 border-l-civix-gold-500 p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-sm bg-civix-gold-950 text-civix-gold-400 flex items-center justify-center font-mono font-bold text-lg border border-civix-gold-600/40">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-extrabold text-civix-text-main tracking-tight">
                DELHI NCR INVESTIGATION WORKSPACE
              </h2>
              <span className="bg-civix-green-950 text-civix-green-400 border border-civix-green-600/40 text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm">
                EXECUTIVE BRIEFING ACTIVE
              </span>
            </div>
            <p className="text-xs text-civix-text-muted mt-1 font-sans">
              Ministry of Home Affairs • Official High-Priority Case Overview & AI Intelligence Summary
            </p>
          </div>
        </div>

        {/* High Level Metrics Bar */}
        <div className="flex items-center space-x-6 text-xs font-mono border-t md:border-t-0 md:border-l border-civix-border pt-3 md:pt-0 md:pl-6">
          <div>
            <div className="text-[10px] text-civix-text-muted uppercase">Active Cases</div>
            <div className="text-sm font-bold text-civix-text-main flex items-center space-x-1">
              <Briefcase className="w-3.5 h-3.5 text-civix-blue-400 inline mr-1" />
              <span>2 Open</span>
            </div>
          </div>
          <div>
            <div className="text-[10px] text-civix-text-muted uppercase">Verified Leads</div>
            <div className="text-sm font-bold text-civix-text-main flex items-center space-x-1">
              <FileCheck className="w-3.5 h-3.5 text-civix-green-400 inline mr-1" />
              <span>1 Pending</span>
            </div>
          </div>
          <div>
            <div className="text-[10px] text-civix-text-muted uppercase">System Integrity</div>
            <div className="text-sm font-bold text-civix-green-400 flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5 text-civix-green-400 inline mr-1" />
              <span>100% RLS</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Focus Row: Hero Priority Lead (Executive Level) */}
      <div className="w-full">
        <PriorityLeadsWidget />
      </div>

      {/* Middle Grid: Structured Relationship Network & Active Cases */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <div className="civix-panel p-5 space-y-3">
            <div className="civix-panel-header">
              <div>
                <h3 className="civix-panel-title">
                  Executive Relationship Intelligence
                </h3>
                <p className="civix-panel-subtitle">
                  Key Subjects & Verified Institutional Links (Operation Trident)
                </p>
              </div>
            </div>
            <StructuredGraphView />
          </div>
        </div>

        <div className="lg:col-span-5">
          <ActiveInvestigationsWidget />
        </div>
      </div>

      {/* Bottom Row: Audit & System Health */}
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
