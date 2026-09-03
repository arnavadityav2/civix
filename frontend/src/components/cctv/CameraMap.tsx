import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { Camera } from '../../api/cctv';

// Clean standard divIcon for Verified/Reachable camera
const verifiedIcon = L.divIcon({
  className: 'custom-camera-marker',
  html: `<div style="width: 14px; height: 14px; background-color: #1a3a6c; border: 2px solid white; border-radius: 50%; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7]
});

// Deprecated or unverified camera
const unavailableIcon = L.divIcon({
  className: 'custom-camera-marker-dim',
  html: `<div style="width: 12px; height: 12px; background-color: #94a3b8; border: 2px solid white; border-radius: 50%; box-shadow: 0 1px 2px rgba(0,0,0,0.2);"></div>`,
  iconSize: [12, 12],
  iconAnchor: [6, 6]
});

// Selected camera pulse
const selectedIcon = L.divIcon({
  className: 'custom-camera-marker-selected',
  html: `<div style="width: 18px; height: 18px; background-color: #ff9933; border: 2px solid white; border-radius: 50%; box-shadow: 0 0 0 4px rgba(255, 153, 51, 0.3);"></div>`,
  iconSize: [18, 18],
  iconAnchor: [9, 9]
});

interface CameraMapProps {
  cameras: Camera[];
  selectedCameraId: string | null;
  onCameraSelect: (cameraId: string) => void;
}

const MapUpdater: React.FC<{ cameras: Camera[], selectedId: string | null }> = ({ cameras, selectedId }) => {
  const map = useMap();
  useEffect(() => {
    if (selectedId) {
      const cam = cameras.find(c => c.camera_id === selectedId);
      if (cam && cam.latitude && cam.longitude) {
        map.flyTo([cam.latitude, cam.longitude], 15, { duration: 1.5 });
      }
    } else if (cameras.length > 0) {
      const valid = cameras.filter(c => c.latitude && c.longitude);
      if (valid.length > 0) {
        const bounds = L.latLngBounds(valid.map(c => [c.latitude, c.longitude]));
        map.fitBounds(bounds, { padding: [50, 50] });
      }
    }
  }, [selectedId, cameras, map]);
  return null;
};

export const CameraMap: React.FC<CameraMapProps> = ({ cameras, selectedCameraId, onCameraSelect }) => {
  const [center] = useState<[number, number]>([51.5074, -0.1278]); // Default London

  return (
    <div className="flex-1 bg-slate-50 rounded border border-slate-200 overflow-hidden relative z-0 w-full h-full min-h-[400px]">
      <MapContainer center={center} zoom={11} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, TfL Open Data'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapUpdater cameras={cameras} selectedId={selectedCameraId} />
        
        {cameras.map(cam => {
          const isSelected = cam.camera_id === selectedCameraId;
          const isVerified = cam.status === 'LIVE' || cam.status === 'REGISTERED_ONLY';
          
          return (
            <Marker 
              key={cam.camera_id} 
              position={[cam.latitude, cam.longitude]}
              icon={isSelected ? selectedIcon : (isVerified ? verifiedIcon : unavailableIcon)}
              eventHandlers={{
                click: () => onCameraSelect(cam.camera_id)
              }}
            >
              <Popup className="civix-map-popup">
                <div className="p-1 min-w-[200px]">
                  <h3 className="font-semibold text-slate-900 text-sm">{cam.display_name}</h3>
                  <p className="text-[10px] text-slate-500 font-mono mt-1">{cam.camera_code}</p>
                  
                  <div className="mt-3">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        onCameraSelect(cam.camera_id);
                      }}
                      className="w-full bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-medium py-1.5 px-3 rounded border border-slate-300 transition-colors"
                    >
                      {isSelected ? 'Currently Selected' : 'Select Camera'}
                    </button>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};
