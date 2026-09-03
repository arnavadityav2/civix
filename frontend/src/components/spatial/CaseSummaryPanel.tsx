import React from 'react';
import type { SpatialCaseFeature } from '../../api/spatial';
import { Target, ArrowRight, MapPin } from 'lucide-react';

interface CaseSummaryPanelProps {
  selectedCase: SpatialCaseFeature | null;
  onOpenEventMap: (caseId: string) => void;
}

export const CaseSummaryPanel: React.FC<CaseSummaryPanelProps> = ({
  selectedCase,
  onOpenEventMap
}) => {
  if (!selectedCase) {
    return (
      <div className="bg-white border border-slate-200 rounded p-6 shadow-sm flex flex-col items-center justify-center text-center h-[280px]">
        <div className="w-12 h-12 rounded-full bg-blue-50 text-[#1a3a6c] flex items-center justify-center mb-3 border border-blue-100">
          <Target className="w-6 h-6 stroke-[1.75]" />
        </div>
        <h3 className="text-sm font-bold text-slate-800 tracking-tight">No Case Selected</h3>
        <p className="text-xs text-slate-500 max-w-xs mt-1 leading-relaxed">
          Select a case from the map or list to view case summary, events, and intelligence.
        </p>
      </div>
    );
  }

  const { case_id, case_number, title, status, priority, case_type, event_count, spatial_semantic } = selectedCase.properties;
  const [lon, lat] = selectedCase.geometry.coordinates;

  return (
    <div className="bg-white border border-slate-200 rounded p-4 shadow-sm flex flex-col justify-between space-y-4">
      <div>
        <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
          <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
            CASE SUMMARY
          </h3>
          <span className="font-mono text-[10px] text-slate-400 font-semibold">{case_number}</span>
        </div>

        <h2 className="text-sm font-bold text-slate-900 leading-tight mb-2">
          {title}
        </h2>

        {/* Badges */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
            priority === 'CRITICAL' ? 'bg-red-50 text-red-700 border border-red-200' :
            priority === 'HIGH' ? 'bg-orange-50 text-orange-700 border border-orange-200' :
            'bg-amber-50 text-amber-700 border border-amber-200'
          }`}>
            {priority}
          </span>
          <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-blue-50 text-blue-800 border border-blue-200">
            {status}
          </span>
          <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase bg-slate-100 text-slate-700 border border-slate-200">
            {case_type}
          </span>
        </div>

        {/* Dynamic Coordinates & Spatial Semantics */}
        <div className="bg-slate-50 rounded border border-slate-200 p-2.5 space-y-2 text-xs text-slate-600 mb-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase flex items-center">
              <MapPin className="w-3 h-3 mr-1 text-slate-400" />
              Footprint Centroid
            </span>
            <span className="font-mono text-[11px] font-semibold text-slate-800">
              {lat.toFixed(4)}° N, {lon.toFixed(4)}° E
            </span>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 text-[10px]">
            <span className="text-slate-400">Semantic Tag:</span>
            <span className="font-mono font-semibold text-[#1a3a6c] bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
              {spatial_semantic}
            </span>
          </div>

          <div className="flex items-center justify-between text-[10px]">
            <span className="text-slate-400">Spatially Grounded Events:</span>
            <span className="font-mono font-bold text-slate-900 bg-white px-1.5 py-0.5 rounded border border-slate-200">
              {event_count} {event_count === 1 ? 'event' : 'events'}
            </span>
          </div>
        </div>
      </div>

      {/* Primary Action Button */}
      <button
        onClick={() => onOpenEventMap(case_id)}
        className="w-full bg-[#1a3a6c] hover:bg-[#132c54] text-white font-semibold text-xs py-2.5 px-4 rounded flex items-center justify-center space-x-2 shadow-sm transition-colors cursor-pointer"
      >
        <span>SEE CASE EVENT MAP</span>
        <ArrowRight className="w-4 h-4 text-amber-400" />
      </button>
    </div>
  );
};
