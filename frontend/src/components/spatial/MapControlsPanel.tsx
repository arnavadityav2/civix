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
    <div className="bg-white border border-slate-200 rounded p-4 shadow-sm space-y-3">
      <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-100 pb-2">
        MAP CONTROLS
      </h3>

      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={onFitViewport}
          className="flex items-center justify-center space-x-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold py-2 px-3 rounded border border-slate-200 transition-colors"
        >
          <Maximize2 className="w-3.5 h-3.5 text-slate-500" />
          <span>Fit to Viewport</span>
        </button>

        <button
          onClick={onResetLayers}
          className="flex items-center justify-center space-x-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold py-2 px-3 rounded border border-slate-200 transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
          <span>Reset Layers</span>
        </button>
      </div>

      <button
        onClick={onExportView}
        className="w-full flex items-center justify-center space-x-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold py-2 px-3 rounded border border-slate-200 transition-colors"
      >
        <Download className="w-3.5 h-3.5 text-slate-500" />
        <span>Export Map View</span>
      </button>
    </div>
  );
};
