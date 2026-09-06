import React from 'react';
import { ChevronRight, History, Compass } from 'lucide-react';
import type { InvestigationTrailItem } from '../../types/graph';

interface InvestigationTrailProps {
  trail: InvestigationTrailItem[];
  onSelectTrailItem: (item: InvestigationTrailItem) => void;
  onClearTrail: () => void;
}

export const InvestigationTrail: React.FC<InvestigationTrailProps> = ({
  trail,
  onSelectTrailItem,
  onClearTrail,
}) => {
  return (
    <div className="flex items-center justify-between px-3 py-1.5 bg-[#0b0f19] border-t border-[#1e2d4a] text-slate-300 font-mono text-[11px] select-none antialiased">
      <div className="flex items-center gap-2 min-w-0 overflow-x-auto">
        <div className="flex items-center gap-1.5 text-cyan-400 font-bold shrink-0">
          <Compass className="w-3.5 h-3.5" />
          <span>INVESTIGATION TRAIL:</span>
        </div>

        {trail.length === 0 ? (
          <span className="text-slate-500 italic text-[10px]">
            Click entities or cases to build an investigation breadcrumb trail.
          </span>
        ) : (
          <div className="flex items-center gap-1.5">
            {trail.map((item, index) => (
              <React.Fragment key={`${item.id}-${index}`}>
                {index > 0 && <ChevronRight className="w-3 h-3 text-slate-600 shrink-0" />}
                <button
                  onClick={() => onSelectTrailItem(item)}
                  className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-[#131b2e] border border-[#1e2d4a] hover:border-cyan-500/60 hover:text-white transition-colors shrink-0 text-[10px]"
                >
                  <span className="text-cyan-400 font-bold uppercase">{item.type}</span>
                  <span className="font-semibold text-slate-200 truncate max-w-[120px]">{item.label}</span>
                </button>
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {trail.length > 0 && (
        <button
          onClick={onClearTrail}
          className="flex items-center gap-1 text-[10px] text-slate-400 hover:text-slate-200 shrink-0 ml-3"
        >
          <History className="w-3 h-3 text-slate-500" />
          <span>CLEAR TRAIL</span>
        </button>
      )}
    </div>
  );
};
