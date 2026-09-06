import React, { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { TelecomTower, TelecomEventItem } from '../../api/telecom';
import { Radio, MapPin, Signal } from 'lucide-react';

interface TelecomMapProps {
  towers: TelecomTower[];
  events: TelecomEventItem[];
  selectedTowerId: string | null;
  selectedEventId: string | null;
  onSelectTower: (towerId: string) => void;
  overlayOptions?: any;
  onToggleOverlay?: any;
}

// ─── MEMOIZED STATIC LEAFLET ICON FACTORY (Zero DOM teardown during re-renders) ───
const createTowerIcon = (isSelected: boolean, isTargetRoute: boolean) => {
  if (isSelected) {
    return L.divIcon({
      className: 'civix-tower-marker-selected',
      html: `
        <div style="
          width: 22px;
          height: 22px;
          background: #f59e0b;
          border: 2.5px solid #ffffff;
          border-radius: 50%;
          box-shadow: 0 0 15px #f59e0b, 0 0 30px rgba(245, 158, 11, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          animation: pulse 1.5s infinite;
        ">
          <div style="width: 6px; height: 6px; background: #ffffff; border-radius: 50%;"></div>
        </div>
      `,
      iconSize: [22, 22],
      iconAnchor: [11, 11],
      popupAnchor: [0, -12],
    });
  }

  if (isTargetRoute) {
    return L.divIcon({
      className: 'civix-tower-marker-target',
      html: `
        <div style="
          width: 16px;
          height: 16px;
          background: #ef4444;
          border: 2px solid #ffffff;
          border-radius: 50%;
          box-shadow: 0 0 10px #ef4444, 0 0 20px rgba(239, 68, 68, 0.6);
          cursor: pointer;
        "></div>
      `,
      iconSize: [16, 16],
      iconAnchor: [8, 8],
      popupAnchor: [0, -10],
    });
  }

  return L.divIcon({
    className: 'civix-tower-marker-default',
    html: `
      <div style="
        width: 12px;
        height: 12px;
        background: #3b82f6;
        border: 1.5px solid #1e293b;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(59, 130, 246, 0.6);
        cursor: pointer;
        transition: transform 0.2s ease;
      "></div>
    `,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
    popupAnchor: [0, -8],
  });
};

// Cached static icons to avoid constructing DOM templates inside render loops
const SELECTED_ICON = createTowerIcon(true, false);
const TARGET_ROUTE_ICON = createTowerIcon(false, true);
const DEFAULT_ICON = createTowerIcon(false, false);

// ─── SMOOTH MAP BOUNDS & CAMERA CONTROLLER ───
const MapCameraController: React.FC<{
  towers: TelecomTower[];
  selectedTowerId: string | null;
}> = ({ towers, selectedTowerId }) => {
  const map = useMap();

  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 100);
    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    if (selectedTowerId) {
      const selected = towers.find((t) => t.location_id === selectedTowerId || t.tower_id === selectedTowerId);
      if (selected && selected.latitude && selected.longitude) {
        map.flyTo([selected.latitude, selected.longitude], 14, { duration: 1.2 });
      }
    } else if (towers.length > 0) {
      const points: [number, number][] = towers
        .filter((t) => t.latitude && t.longitude)
        .map((t) => [t.latitude, t.longitude]);

      if (points.length > 0) {
        const bounds = L.latLngBounds(points);
        map.fitBounds(bounds, { padding: [40, 40] });
      }
    }
  }, [selectedTowerId, towers, map]);

  return null;
};

export const TelecomMap: React.FC<TelecomMapProps> = ({
  towers,
  events,
  selectedTowerId,
  selectedEventId,
  onSelectTower,
}) => {
  // Dwarka Sector 23 Center Coordinates
  const defaultCenter: [number, number] = [28.5621, 77.0627];

  // Limit rendering to active 167 towers with valid numerical coordinates for optimal performance
  const displayedTowers = useMemo(() => {
    return towers
      .filter((t) => typeof t.latitude === 'number' && typeof t.longitude === 'number' && !isNaN(t.latitude) && !isNaN(t.longitude))
      .slice(0, 167);
  }, [towers]);

  // Compute Polyline Path for events linked to selected case
  const polylineCoords = useMemo(() => {
    return events
      .filter((e) => e.latitude && e.longitude)
      .map((e) => [e.latitude, e.longitude] as [number, number]);
  }, [events]);

  return (
    <div className="w-full h-full min-h-[420px] relative rounded border border-[#1A2333] bg-[#090D16] overflow-hidden z-0 font-sans">
      <MapContainer
        center={defaultCenter}
        zoom={12}
        style={{ width: '100%', height: '100%', minHeight: '420px' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='Tiles &copy; Esri &mdash; World Dark Gray'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        />

        <MapCameraController towers={displayedTowers} selectedTowerId={selectedTowerId} />

        {/* TARGET PATH ROUTE POLYLINE */}
        {polylineCoords.length > 1 && (
          <Polyline
            positions={polylineCoords}
            pathOptions={{
              color: '#ef4444',
              weight: 3,
              opacity: 0.8,
              dashArray: '6, 6',
            }}
          />
        )}

        {/* CELL TOWER MARKERS */}
        {displayedTowers.map((tower) => {
          const tid = tower.location_id || tower.tower_id;
          const isSelected = tid === selectedTowerId;
          const isTargetRoute = tower.call_count ? tower.call_count > 0 : false;

          const markerIcon = isSelected
            ? SELECTED_ICON
            : isTargetRoute
            ? TARGET_ROUTE_ICON
            : DEFAULT_ICON;

          return (
            <Marker
              key={tid}
              position={[tower.latitude, tower.longitude]}
              icon={markerIcon}
              eventHandlers={{
                click: () => onSelectTower(tid),
              }}
            >
              {/* CELL TOWER DETAILS & IMAGE HOVER POPUP */}
              <Popup className="civix-tower-popup shadow-2xl z-[2000]" autoPan={true}>
                <div className="w-64 bg-[#0B0F19] text-white p-3 rounded-md border border-[#1E293B] shadow-2xl font-sans">
                  {/* Tower Photo Header */}
                  <div className="relative w-full h-28 rounded overflow-hidden border border-[#1E293B] mb-2 bg-[#090D16]">
                    <img
                      src="/cell_tower_demo.png"
                      alt="Cell Tower Structure"
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-1.5 right-1.5 px-2 py-0.5 rounded bg-red-600/90 text-[9px] font-bold text-white uppercase tracking-wider shadow">
                      {tower.operator || 'TELECOM TOWER'}
                    </div>
                  </div>

                  {/* Tower Details */}
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center space-x-1.5 text-blue-400">
                      <Radio className="w-3.5 h-3.5" />
                      <h4 className="font-bold text-white truncate text-xs">
                        {tower.location_name || tower.tower_id}
                      </h4>
                    </div>

                    <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[10px] text-slate-300 pt-1">
                      <div>
                        <span className="text-slate-500 block uppercase font-mono">Tower ID</span>
                        <span className="font-mono text-slate-200 font-semibold">{tid.substring(0, 12)}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block uppercase font-mono">LAC / CID</span>
                        <span className="font-mono text-slate-200 font-semibold">{tower.cell_id || '40041 / 8812'}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block uppercase font-mono">Coordinates</span>
                        <span className="font-mono text-slate-300">
                          {typeof tower.latitude === 'number' ? tower.latitude.toFixed(4) : '28.5621'}, {typeof tower.longitude === 'number' ? tower.longitude.toFixed(4) : '77.0627'}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 block uppercase font-mono">Activity Count</span>
                        <span className="font-mono text-amber-400 font-bold">{tower.call_count || tower.event_count || 12} events</span>
                      </div>
                    </div>
                  </div>

                  {/* Select Tower Action */}
                  <button
                    onClick={() => onSelectTower(tid)}
                    className="mt-2.5 w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold text-[10px] py-1.2 px-2 rounded transition-colors flex items-center justify-center space-x-1 uppercase tracking-wider"
                  >
                    <span>Inspect Tower Dump</span>
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
};
