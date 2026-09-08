import React, { useState } from 'react';
import { Info, ChevronDown, ChevronUp } from 'lucide-react';

export const EpistemicLegend: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  return (
    <div className="absolute bottom-4 left-4 z-40 bg-[#0d1322]/95 border border-[#1e2d4a] rounded-lg p-2.5 shadow-2xl backdrop-blur-md text-slate-300 font-mono text-[10px] select-none antialiased w-72">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between gap-2 font-bold text-cyan-400 uppercase tracking-wider hover:text-cyan-300 transition-colors"
      >
        <div className="flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span>VISUAL LANGUAGE LEGEND</span>
        </div>
        {isExpanded ? <ChevronDown className="w-3 h-3 text-slate-400" /> : <ChevronUp className="w-3 h-3 text-slate-400" />}
      </button>

      {isExpanded && (
        <div className="mt-2 space-y-2.5 pt-2 border-t border-[#162035] text-[10px]">
          {/* Section 1: Entity Types & Solid Node Palettes */}
          <div>
            <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
              ENTITY NODE TYPES
            </div>
            <div className="grid grid-cols-2 gap-1.5 text-[9.5px]">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-[#2563eb] border border-[#93c5fd] shrink-0"></span>
                <span className="text-slate-200 truncate">👤 Person (Circle)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-xs bg-[#d97706] border border-[#fef08a] shrink-0"></span>
                <span className="text-slate-200 truncate">📁 Case (Square)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3.5 h-2 rounded-xs bg-[#dc2626] border border-[#fca5a5] shrink-0"></span>
                <span className="text-slate-200 truncate">🚗 Vehicle (Capsule)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-3.5 rounded-xs bg-[#0284c7] border border-[#bae6fd] shrink-0"></span>
                <span className="text-slate-200 truncate">📄 Evidence (Doc)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rotate-45 bg-[#059669] border border-[#a7f3d0] shrink-0"></span>
                <span className="text-slate-200 truncate">📍 Location (Pin)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rotate-45 bg-[#ea580c] border border-[#ffedd5] shrink-0"></span>
                <span className="text-slate-200 truncate">🏢 Org (Diamond)</span>
              </div>
              <div className="flex items-center gap-1.5 col-span-2">
                <span className="w-3.5 h-2.5 bg-[#0d9488] border border-[#99f6e4] shrink-0"></span>
                <span className="text-slate-200 truncate">📱 Phone / Device (Rhomboid)</span>
              </div>
            </div>
          </div>

          {/* Section 2: Relationship Line & Pattern Encoding */}
          <div className="pt-2 border-t border-[#162035]">
            <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
              RELATIONSHIP ENCODING
            </div>
            <div className="space-y-1 text-[9.5px]">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-4 h-0.5 bg-rose-500 shrink-0"></span>
                  <span className="text-slate-200">Vehicle / Operation</span>
                </div>
                <span className="text-rose-400 font-mono text-[9px]">SOLID RED</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-4 h-0.5 bg-emerald-500 shrink-0"></span>
                  <span className="text-slate-200">Spatial / Sighting</span>
                </div>
                <span className="text-emerald-400 font-mono text-[9px]">GREEN VEE</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-4 h-0.5 bg-amber-500 shrink-0"></span>
                  <span className="text-slate-200">Case Association</span>
                </div>
                <span className="text-amber-400 font-mono text-[9px]">GOLD TRIANGLE</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-4 h-0.5 border-b-2 border-dotted border-sky-400 shrink-0"></span>
                  <span className="text-slate-200">Evidence Provenance</span>
                </div>
                <span className="text-sky-400 font-mono text-[9px]">DOTTED DIAMOND</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-4 h-0.5 border-b-2 border-dashed border-amber-400 shrink-0"></span>
                  <span className="text-slate-200">Investigator Proposal</span>
                </div>
                <span className="text-amber-400 font-mono text-[9px]">DASHED AMBER</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

