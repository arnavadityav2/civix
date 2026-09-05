import React from 'react';
import type { Camera } from '../../api/cctv';
import { MapPin, Search, Camera as CameraIcon } from 'lucide-react';

interface CameraGridProps {
  cameras: Camera[];
  selectedCameraId: string | null;
  onCameraSelect: (cameraId: string) => void;
}

export const CameraGrid: React.FC<CameraGridProps> = ({ cameras, selectedCameraId, onCameraSelect }) => {
  const [searchTerm, setSearchTerm] = React.useState('');

  const filteredCameras = cameras.filter(c => 
    c.display_name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    c.camera_code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="bg-[#11141C] border border-[#1E2430] rounded-xl flex flex-col h-full overflow-hidden shadow-lg select-none font-sans">
      <div className="px-4 py-3 border-b border-[#1E2430] flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 bg-[#11141C]">
        <div className="flex items-center space-x-2">
          <CameraIcon className="w-4 h-4 text-[#E6B325]" />
          <h3 className="text-xs font-black text-white uppercase tracking-wider">Camera Directory</h3>
          <span className="bg-[#161922] text-slate-300 text-[10px] font-mono font-bold px-2 py-0.5 rounded border border-[#1E2430]">
            {filteredCameras.length}
          </span>
        </div>
        
        <div className="relative w-full sm:w-64">
          <input 
            type="text" 
            placeholder="Search camera name or code..."
            className="w-full bg-[#161922] border border-[#1E2430] focus:border-slate-500 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none transition-colors"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
          <Search className="absolute left-2.5 top-2 text-slate-400" size={13} />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3.5 bg-[#090C12]">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
          {filteredCameras.map(cam => {
            const isSelected = cam.camera_id === selectedCameraId;
            const isVerified = cam.status === 'LIVE' || cam.status === 'REGISTERED_ONLY';
            
            return (
              <div 
                key={cam.camera_id} 
                className={`bg-[#11141C] border rounded-xl cursor-pointer transition-all overflow-hidden flex flex-col justify-between shadow ${
                  isSelected ? 'border-[#E6B325] ring-1 ring-[#E6B325]/40 bg-[#161922]' : 'border-[#1E2430] hover:border-slate-600'
                }`}
                onClick={() => onCameraSelect(cam.camera_id)}
              >
                <div className="p-3">
                  <div className="flex items-start justify-between">
                    <h4 className="font-extrabold text-white text-xs truncate pr-1" title={cam.display_name}>
                      {cam.display_name}
                    </h4>
                    {isVerified && (
                      <span className="bg-emerald-950 text-emerald-400 text-[8px] font-bold px-1.5 py-0.5 rounded uppercase border border-emerald-600/40 flex-shrink-0">
                        REACHABLE
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-400 font-mono mt-1">{cam.camera_code}</p>
                </div>
                
                <div className="px-3 py-2 bg-[#161922] border-t border-[#1E2430] flex items-center justify-between">
                  <div className="flex items-center text-[10px] text-slate-400 font-medium">
                    <MapPin size={11} className="mr-1 text-blue-400" />
                    <span>{cam.city}</span>
                  </div>
                  <button 
                    className={`text-[9px] font-extrabold px-2.5 py-0.5 rounded transition-colors ${
                      isSelected 
                        ? 'bg-[#E6B325] text-black shadow' 
                        : 'bg-[#11141C] text-slate-300 hover:bg-slate-800 border border-[#1E2430]'
                    }`}
                  >
                    {isSelected ? 'SELECTED' : 'INSPECT'}
                  </button>
                </div>
              </div>
            );
          })}
          
          {filteredCameras.length === 0 && (
            <div className="col-span-full py-8 text-center text-slate-400 text-xs">
              No cameras match your search filter.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
