import React from 'react';
import { DirectionCHybrid } from '../components/domain/DirectionCHybrid';
import { Clock, Briefcase } from 'lucide-react';

export const CommandCenterPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Title Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-slate-200 gap-3">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight uppercase">
              Command Center
            </h1>
            <span className="text-[11px] font-mono font-bold bg-slate-900 text-white px-2.5 py-0.5 rounded flex items-center space-x-1.5 shadow-2xs">
              <Briefcase className="w-3 h-3 text-amber-500 inline mr-1" />
              <span>ACTIVE CASE CONTEXT · CASE-2026-0142</span>
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 font-medium">
            Case activity and investigative intelligence overview
          </p>
        </div>

        {/* Date & Workspace Timestamp Badge */}
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-600 bg-white border border-slate-200 px-3 py-1.5 rounded shadow-2xs">
          <Clock className="w-3.5 h-3.5 text-amber-600" />
          <span>02 September 2026, 13:42 IST</span>
          <span className="text-slate-300">|</span>
          <span className="font-bold text-slate-800">DELHI NCR WORKSPACE</span>
        </div>
      </div>

      {/* Production Hybrid Command Center View */}
      <DirectionCHybrid />
    </div>
  );
};
