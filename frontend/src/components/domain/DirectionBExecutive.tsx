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
      <div className="bg-white border-l-4 border-l-slate-900 border border-slate-200 rounded p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded bg-slate-900 text-amber-500 flex items-center justify-center font-mono font-bold text-lg shadow-2xs">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight">
                DELHI NCR INVESTIGATION WORKSPACE
              </h2>
              <span className="bg-emerald-50 text-emerald-800 border border-emerald-300 text-[10px] font-mono font-bold px-2 py-0.5 rounded">
                EXECUTIVE BRIEFING ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1 font-sans">
              Ministry of Home Affairs • Official High-Priority Case Overview & AI Intelligence Summary
            </p>
          </div>
        </div>

        {/* High Level Metrics Bar */}
        <div className="flex items-center space-x-6 text-xs font-mono border-t md:border-t-0 md:border-l border-slate-200 pt-3 md:pt-0 md:pl-6">
          <div>
            <div className="text-[10px] text-slate-500 uppercase">Active Cases</div>
            <div className="text-sm font-bold text-slate-900 flex items-center space-x-1">
              <Briefcase className="w-3.5 h-3.5 text-blue-600 inline mr-1" />
              <span>2 Open</span>
            </div>
          </div>
          <div>
            <div className="text-[10px] text-slate-500 uppercase">Verified Leads</div>
            <div className="text-sm font-bold text-slate-900 flex items-center space-x-1">
              <FileCheck className="w-3.5 h-3.5 text-emerald-600 inline mr-1" />
              <span>1 Pending</span>
            </div>
          </div>
          <div>
            <div className="text-[10px] text-slate-500 uppercase">System Integrity</div>
            <div className="text-sm font-bold text-emerald-700 flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 inline mr-1" />
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
          <div className="bg-white border border-slate-200 rounded p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-tight">
                  Executive Relationship Intelligence
                </h3>
                <p className="text-xs text-slate-500">
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
