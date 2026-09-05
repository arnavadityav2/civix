import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { Camera } from '../../api/cctv';

// Clean standard divIcon for Verified/Reachable camera
const verifiedIcon = L.divIcon({
  className: 'custom-camera-marker',
  html: `<div style="width: 14px; height: 14px; background-color: #3b82f6; border: 2px solid #111318; border-radius: 50%; box-shadow: 0 1px 3px rgba(0,0,0,0.5);"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7]
});

// Deprecated or unverified camera
const unavailableIcon = L.divIcon({
  className: 'custom-camera-marker-dim',
  html: `<div style="width: 12px; height: 12px; background-color: #4b5563; border: 2px solid #111318; border-radius: 50%; box-shadow: 0 1px 2px rgba(0,0,0,0.4);"></div>`,
  iconSize: [12, 12],
  iconAnchor: [6, 6]
});

// Selected camera pulse
const selectedIcon = L.divIcon({
  className: 'custom-camera-marker-selected',
  html: `<div style="width: 18px; height: 18px; background-color: #f59e0b; border: 2px solid #111318; border-radius: 50%; box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.4);"></div>`,
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
    <div className="flex-1 bg-civix-bg rounded-sm border border-civix-border overflow-hidden relative z-0 w-full h-full min-h-[400px]">
      <MapContainer center={center} zoom={11} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
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
                <div className="p-1 min-w-[200px] text-civix-text-main">
                  <h3 className="font-semibold text-civix-text-main text-sm">{cam.display_name}</h3>
                  <p className="text-[10px] text-civix-text-muted font-mono mt-1">{cam.camera_code}</p>
                  
                  <div className="mt-3">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        onCameraSelect(cam.camera_id);
                      }}
                      className="civix-btn-secondary w-full justify-center text-xs py-1 px-3"
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
