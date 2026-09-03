import React from 'react';
import type { CameraDetail } from '../../api/cctv';
import { MapPin, ShieldCheck, Clock, ExternalLink } from 'lucide-react';

interface CameraInspectorProps {
  cameraData: CameraDetail | null;
}

export const CameraInspector: React.FC<CameraInspectorProps> = ({ cameraData }) => {
  if (!cameraData) {
    return (
      <div className="text-slate-400 text-xs italic py-2">
        No camera selected. Click a map pin or directory item to inspect.
      </div>
    );
  }

  const { camera, feeds } = cameraData;
  const hasActiveFeed = feeds && feeds.length > 0 && feeds[0].is_active;
  const cameraStatusLabel = camera.status === 'REGISTERED_ONLY' ? 'REGISTERED' : camera.status;

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between">
        <div className="pr-2">
          <h3 className="font-semibold text-slate-900 text-sm leading-tight">{camera.display_name}</h3>
          <div className="flex items-center text-[11px] text-slate-500 mt-0.5">
            <MapPin size={11} className="mr-1 text-slate-400 flex-shrink-0" />
            <span>{camera.city}, {camera.region}</span>
          </div>
        </div>

        <div className="flex flex-col items-end space-y-1 flex-shrink-0">
          <div className="flex items-center space-x-1">
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">CAMERA:</span>
            <span className="bg-slate-100 text-slate-700 border border-slate-300 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider">
              {cameraStatusLabel}
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">FEED:</span>
            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${
              hasActiveFeed
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}>
              {hasActiveFeed ? 'VERIFIED · REACHABLE' : 'UNAVAILABLE'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-y-2 gap-x-3 pt-2 border-t border-slate-100 text-xs">
        <div>
          <p className="text-[9px] uppercase font-bold text-slate-400">Camera Code</p>
          <p className="font-mono text-slate-700 text-[11px] mt-0.5">{camera.camera_code}</p>
        </div>
        <div>
          <p className="text-[9px] uppercase font-bold text-slate-400">Coordinates</p>
          <p className="font-mono text-slate-600 text-[11px] mt-0.5">
            {camera.latitude.toFixed(4)}, {camera.longitude.toFixed(4)}
          </p>
        </div>
        <div>
          <p className="text-[9px] uppercase font-bold text-slate-400">Operator</p>
          <div className="flex items-center text-[11px] text-slate-700 font-medium mt-0.5">
            <ShieldCheck size={11} className="mr-1 text-slate-400" />
            TfL Open Data
          </div>
        </div>
        <div>
          <p className="text-[9px] uppercase font-bold text-slate-400">Sync Date</p>
          <div className="flex items-center text-[11px] text-slate-600 mt-0.5">
            <Clock size={11} className="mr-1 text-slate-400" />
            {new Date(camera.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>

      <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
        <a 
          href="https://tfl.gov.uk/info-for/open-data-users/our-open-data" 
          target="_blank" 
          rel="noopener noreferrer"
          className="inline-flex items-center text-[10px] text-blue-600 hover:text-blue-800 transition-colors font-medium"
        >
          <ExternalLink size={10} className="mr-1" />
          Licensing Terms
        </a>
      </div>
    </div>
  );
};
