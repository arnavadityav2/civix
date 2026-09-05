import React from 'react';
import { Maximize2, RotateCcw, Download } from 'lucide-react';

interface MapControlsPanelProps {
  onFitViewport: () => void;
  onResetLayers: () => void;
  onExportView: () => void;
}

export const MapControlsPanel: React.FC<MapControlsPanelProps> = ({
  onFitViewport,
  onResetLayers,
  onExportView
}) => {
  return (
    <div className="civix-panel p-4 space-y-3">
      <h3 className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider border-b border-civix-border pb-2">
        MAP CONTROLS
      </h3>

      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={onFitViewport}
          className="civix-btn-secondary justify-center text-xs py-2"
        >
          <Maximize2 className="w-3.5 h-3.5 text-civix-text-muted" />
          <span>Fit to Viewport</span>
        </button>

        <button
          onClick={onResetLayers}
          className="civix-btn-secondary justify-center text-xs py-2"
        >
          <RotateCcw className="w-3.5 h-3.5 text-civix-text-muted" />
          <span>Reset Layers</span>
        </button>
      </div>

      <button
        onClick={onExportView}
        className="civix-btn-secondary w-full justify-center text-xs py-2"
      >
        <Download className="w-3.5 h-3.5 text-civix-text-muted" />
        <span>Export Map View</span>
      </button>
    </div>
  );
};
