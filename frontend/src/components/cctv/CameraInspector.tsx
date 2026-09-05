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
        No camera selected. Click a map pin or directory item to inspect metadata.
      </div>
    );
  }

  const { camera, feeds } = cameraData;
  const hasActiveFeed = feeds && feeds.length > 0 && feeds[0].is_active;
  const cameraStatusLabel = camera.status === 'REGISTERED_ONLY' ? 'REGISTERED' : camera.status;

  return (
    <div className="space-y-3 font-sans select-none">
      <div className="flex items-start justify-between">
        <div className="pr-2">
          <h3 className="font-extrabold text-white text-sm leading-tight">{camera.display_name}</h3>
          <div className="flex items-center text-[11px] text-slate-400 mt-1 font-medium">
            <MapPin size={12} className="mr-1 text-blue-400 flex-shrink-0" />
            <span>{camera.city}, {camera.region}</span>
          </div>
        </div>

        <div className="flex flex-col items-end space-y-1 flex-shrink-0">
          <div className="flex items-center space-x-1">
            <span className="text-[9px] font-extrabold text-slate-400 uppercase tracking-wider">CAMERA:</span>
            <span className="bg-[#161922] text-slate-200 border border-[#1E2430] px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider">
              {cameraStatusLabel}
            </span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="text-[9px] font-extrabold text-slate-400 uppercase tracking-wider">FEED:</span>
            <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${
              hasActiveFeed
                ? 'bg-emerald-950 text-emerald-400 border-emerald-600/40'
                : 'bg-amber-950 text-amber-400 border-amber-600/40'
            }`}>
              {hasActiveFeed ? 'VERIFIED · REACHABLE' : 'UNAVAILABLE'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-y-2.5 gap-x-3 pt-2.5 border-t border-[#1E2430] text-xs">
        <div>
          <p className="text-[9px] uppercase font-black text-slate-400 tracking-wider">Camera Code</p>
          <p className="font-mono text-white text-[11px] font-bold mt-0.5">{camera.camera_code}</p>
        </div>
        <div>
          <p className="text-[9px] uppercase font-black text-slate-400 tracking-wider">Coordinates</p>
          <p className="font-mono text-slate-300 text-[11px] mt-0.5">
            {camera.latitude.toFixed(4)}, {camera.longitude.toFixed(4)}
          </p>
        </div>
        <div>
          <p className="text-[9px] uppercase font-black text-slate-400 tracking-wider">Operator</p>
          <div className="flex items-center text-[11px] text-white font-bold mt-0.5">
            <ShieldCheck size={12} className="mr-1 text-blue-400" />
            TfL Open Data
          </div>
        </div>
        <div>
          <p className="text-[9px] uppercase font-black text-slate-400 tracking-wider">Sync Date</p>
          <div className="flex items-center text-[11px] text-slate-300 mt-0.5">
            <Clock size={12} className="mr-1 text-slate-400" />
            {new Date(camera.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>

      <div className="pt-2 border-t border-[#1E2430] flex items-center justify-between">
        <a 
          href="https://tfl.gov.uk/info-for/open-data-users/our-open-data" 
          target="_blank" 
          rel="noopener noreferrer"
          className="inline-flex items-center text-[10px] text-blue-400 hover:text-blue-300 transition-colors font-bold"
        >
          <ExternalLink size={11} className="mr-1" />
          Licensing Terms & Open Data Protocol
        </a>
      </div>
    </div>
  );
};
