import React, { useState } from 'react';
import { Info, ChevronDown, ChevronUp } from 'lucide-react';

export const EpistemicLegend: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  return (
    <div className="absolute bottom-4 left-4 z-40 bg-[#0d1322]/95 border border-[#1e2d4a] rounded p-2 shadow-xl backdrop-blur-xs text-slate-300 font-mono text-[10px] select-none antialiased max-w-xs">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between gap-2 font-bold text-cyan-400 uppercase tracking-wider hover:text-cyan-300"
      >
        <div className="flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5" />
          <span>GRAPH EPISTEMIC LEGEND</span>
        </div>
        {isExpanded ? <ChevronDown className="w-3 h-3 text-slate-400" /> : <ChevronUp className="w-3 h-3 text-slate-400" />}
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-1.5 pt-2 border-t border-[#162035] text-[10px]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 border border-cyan-300"></span>
              <span className="text-slate-200">Authoritative Graph Record</span>
            </div>
            <span className="text-slate-500 text-[9px]">CONFIRMED</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-emerald-300"></span>
              <span className="text-slate-200">Supervisor Accepted</span>
            </div>
            <span className="text-emerald-400 text-[9px]">ACCEPTED</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-0.5 border-b-2 border-dashed border-amber-400"></span>
              <span className="text-slate-200">Investigator Proposal</span>
            </div>
            <span className="text-amber-400 text-[9px]">PROPOSED</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-950 border border-rose-500"></span>
              <span className="text-slate-200">Suspect / Accused Role</span>
            </div>
            <span className="text-rose-400 text-[9px]">ROLE</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded border border-cyan-400 bg-[#0f172a]"></span>
              <span className="text-slate-200">Network Hub ($\ge 4$ Deg)</span>
            </div>
            <span className="text-cyan-400 text-[9px]">CONNECTIVITY</span>
          </div>
        </div>
      )}
    </div>
  );
};
