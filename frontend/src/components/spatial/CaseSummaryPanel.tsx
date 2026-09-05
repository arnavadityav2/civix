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
      <div className="civix-panel p-6 flex flex-col items-center justify-center text-center h-[280px]">
        <div className="w-12 h-12 rounded-sm bg-civix-blue-950 text-civix-blue-400 flex items-center justify-center mb-3 border border-civix-blue-600/40">
          <Target className="w-6 h-6 stroke-[1.75]" />
        </div>
        <h3 className="text-sm font-bold text-civix-text-main tracking-tight">No Case Selected</h3>
        <p className="text-xs text-civix-text-muted max-w-xs mt-1 leading-relaxed">
          Select a case from the map or list to view case summary, events, and intelligence.
        </p>
      </div>
    );
  }

  const { case_id, case_number, title, status, priority, case_type, event_count, spatial_semantic } = selectedCase.properties;
  const [lon, lat] = selectedCase.geometry.coordinates;

  return (
    <div className="civix-panel p-4 flex flex-col justify-between space-y-4">
      <div>
        <div className="flex items-center justify-between border-b border-civix-border pb-2 mb-3">
          <h3 className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider">
            CASE SUMMARY
          </h3>
          <span className="civix-id">{case_number}</span>
        </div>

        <h2 className="text-sm font-bold text-civix-text-main leading-tight mb-2">
          {title}
        </h2>

        {/* Badges */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          <span className={`px-2 py-0.5 rounded-sm text-[9px] font-bold uppercase border ${
            priority === 'CRITICAL' ? 'bg-civix-red-950 text-civix-red-400 border-civix-red-600/50' :
            priority === 'HIGH' ? 'bg-civix-gold-950 text-civix-gold-400 border-civix-gold-600/50' :
            'bg-civix-gold-950/60 text-civix-gold-400 border-civix-gold-600/40'
          }`}>
            {priority}
          </span>
          <span className="px-2 py-0.5 rounded-sm text-[9px] font-bold uppercase bg-civix-blue-950 text-civix-blue-400 border border-civix-blue-600/50">
            {status}
          </span>
          <span className="px-2 py-0.5 rounded-sm text-[9px] font-bold uppercase bg-civix-surface-2 text-civix-text-secondary border border-civix-border">
            {case_type}
          </span>
        </div>

        {/* Dynamic Coordinates & Spatial Semantics */}
        <div className="bg-civix-surface rounded-sm border border-civix-border p-2.5 space-y-2 text-xs text-civix-text-secondary mb-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-civix-text-muted uppercase flex items-center">
              <MapPin className="w-3 h-3 mr-1 text-civix-blue-400" />
              Footprint Centroid
            </span>
            <span className="font-mono text-[11px] font-semibold text-civix-text-main">
              {lat.toFixed(4)}° N, {lon.toFixed(4)}° E
            </span>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-civix-border/40 text-[10px]">
            <span className="text-civix-text-muted">Semantic Tag:</span>
            <span className="font-mono font-semibold text-civix-blue-400 bg-civix-blue-950 px-1.5 py-0.5 rounded-sm border border-civix-blue-600/40">
              {spatial_semantic}
            </span>
          </div>

          <div className="flex items-center justify-between text-[10px]">
            <span className="text-civix-text-muted">Spatially Grounded Events:</span>
            <span className="font-mono font-bold text-civix-text-main bg-civix-surface-2 px-1.5 py-0.5 rounded-sm border border-civix-border">
              {event_count} {event_count === 1 ? 'event' : 'events'}
            </span>
          </div>
        </div>
      </div>

      {/* Primary Action Button */}
      <button
        onClick={() => onOpenEventMap(case_id)}
        className="civix-btn-primary w-full justify-center"
      >
        <span>SEE CASE EVENT MAP</span>
        <ArrowRight className="w-4 h-4 text-civix-gold" />
      </button>
    </div>
  );
};
