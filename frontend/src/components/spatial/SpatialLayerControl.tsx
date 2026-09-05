import React from 'react';
import { Layers, MapPin, Navigation, Flame, Eye } from 'lucide-react';

interface SpatialLayerControlProps {
  layers: {
    footprints: boolean;
    eventLocations: boolean;
    routes: boolean;
    heatmap: boolean;
  };
  onToggleLayer: (layerKey: 'footprints' | 'eventLocations' | 'routes' | 'heatmap') => void;
  hasSelectedCase: boolean;
}

export const SpatialLayerControl: React.FC<SpatialLayerControlProps> = ({
  layers,
  onToggleLayer,
  hasSelectedCase
}) => {
  return (
    <div className="civix-panel p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-civix-border pb-2">
        <h3 className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider flex items-center">
          <Layers className="w-3.5 h-3.5 mr-1.5 text-civix-blue-400" />
          SPATIAL LAYERS
        </h3>
      </div>

      <div className="space-y-2.5 text-xs">
        {/* Layer 1: Case Footprints */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex flex-col min-w-0">
            <span className="font-semibold text-civix-text-main flex items-center truncate">
              <MapPin className="w-3.5 h-3.5 mr-1.5 text-civix-blue-400 flex-shrink-0" />
              Case Footprints
            </span>
            <span className="text-[10px] text-civix-text-muted pl-5 truncate">Case centroid locations</span>
          </div>
          <button
            onClick={() => onToggleLayer('footprints')}
            className={`w-9 h-5 rounded-full transition-colors relative flex-shrink-0 focus:outline-none ${
              layers.footprints ? 'bg-civix-blue-600' : 'bg-civix-surface-2 border border-civix-border'
            }`}
          >
            <span className={`w-3.5 h-3.5 rounded-full bg-civix-text-main absolute top-0.5 transition-all ${
              layers.footprints ? 'right-0.5' : 'left-0.5'
            }`} />
          </button>
        </div>

        {/* Layer 2: Event Locations */}
        <div className={`flex items-center justify-between gap-2 ${!hasSelectedCase ? 'opacity-50' : ''}`}>
          <div className="flex flex-col min-w-0">
            <span className="font-semibold text-civix-text-main flex items-center truncate">
              <Eye className="w-3.5 h-3.5 mr-1.5 text-civix-gold-400 flex-shrink-0" />
              Event Locations
            </span>
            <span className="text-[10px] text-civix-text-muted pl-5 truncate">
              {hasSelectedCase ? 'Spatial event points' : 'Requires case selection'}
            </span>
          </div>
          <button
            disabled={!hasSelectedCase}
            onClick={() => onToggleLayer('eventLocations')}
            className={`w-9 h-5 rounded-full transition-colors relative flex-shrink-0 focus:outline-none ${
              layers.eventLocations && hasSelectedCase ? 'bg-civix-blue-600' : 'bg-civix-surface-2 border border-civix-border'
            }`}
          >
            <span className={`w-3.5 h-3.5 rounded-full bg-civix-text-main absolute top-0.5 transition-all ${
              layers.eventLocations && hasSelectedCase ? 'right-0.5' : 'left-0.5'
            }`} />
          </button>
        </div>

        {/* Layer 3: Movement Routes */}
        <div className={`flex items-center justify-between gap-2 ${!hasSelectedCase ? 'opacity-50' : ''}`}>
          <div className="flex flex-col min-w-0">
            <span className="font-semibold text-civix-text-main flex items-center truncate">
              <Navigation className="w-3.5 h-3.5 mr-1.5 text-civix-blue-400 flex-shrink-0" />
              Movement Routes
            </span>
            <span className="text-[10px] text-civix-text-muted pl-5 truncate">
              {hasSelectedCase ? 'Route lines & trajectories' : 'Requires case selection'}
            </span>
          </div>
          <button
            disabled={!hasSelectedCase}
            onClick={() => onToggleLayer('routes')}
            className={`w-9 h-5 rounded-full transition-colors relative flex-shrink-0 focus:outline-none ${
              layers.routes && hasSelectedCase ? 'bg-civix-blue-600' : 'bg-civix-surface-2 border border-civix-border'
            }`}
          >
            <span className={`w-3.5 h-3.5 rounded-full bg-civix-text-main absolute top-0.5 transition-all ${
              layers.routes && hasSelectedCase ? 'right-0.5' : 'left-0.5'
            }`} />
          </button>
        </div>

        {/* Layer 4: Heatmap (Disabled) */}
        <div className="flex items-center justify-between gap-2 opacity-40 cursor-not-allowed">
          <div className="flex flex-col min-w-0">
            <span className="font-semibold text-civix-text-main flex items-center truncate">
              <Flame className="w-3.5 h-3.5 mr-1.5 text-civix-red-400 flex-shrink-0" />
              Heatmap (Events)
            </span>
            <span className="text-[10px] text-civix-text-muted pl-5 truncate">Event density visualization</span>
          </div>
          <button
            disabled
            className="w-9 h-5 rounded-full bg-civix-surface-2 border border-civix-border relative flex-shrink-0 cursor-not-allowed"
          >
            <span className="w-3.5 h-3.5 rounded-full bg-civix-text-muted absolute top-0.5 left-0.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
