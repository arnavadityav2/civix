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
      const selected = towers.find((t) => (t as any).location_id === selectedTowerId || t.tower_id === selectedTowerId);
      const lat = selected ? ((selected as any).latitude ?? selected.centroid_lat) : null;
      const lon = selected ? ((selected as any).longitude ?? selected.centroid_lon) : null;
      if (selected && typeof lat === 'number' && typeof lon === 'number') {
        map.flyTo([lat, lon], 14, { duration: 1.2 });
      }
    } else if (towers.length > 0) {
      const points: [number, number][] = towers
        .map((t) => [((t as any).latitude ?? t.centroid_lat), ((t as any).longitude ?? t.centroid_lon)] as [number, number])
        .filter(([lat, lon]) => typeof lat === 'number' && typeof lon === 'number');

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
  selectedEventId: _selectedEventId,
  onSelectTower,
}) => {
  // Dwarka Sector 23 Center Coordinates
  const defaultCenter: [number, number] = [28.5621, 77.0627];

  // Limit rendering to active towers with valid numerical coordinates
  const displayedTowers = useMemo(() => {
    return towers
      .filter((t) => {
        const lat = (t as any).latitude ?? t.centroid_lat;
        const lon = (t as any).longitude ?? t.centroid_lon;
        return typeof lat === 'number' && typeof lon === 'number' && !isNaN(lat) && !isNaN(lon);
      })
      .slice(0, 167);
  }, [towers]);

  // Compute Polyline Path for events linked to selected case
  const polylineCoords = useMemo(() => {
    return events
      .map((e) => [e.location_lat, e.location_lon] as [number, number])
      .filter(([lat, lon]) => typeof lat === 'number' && typeof lon === 'number');
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
          const tid = (tower as any).location_id || tower.tower_id;
          const lat = (tower as any).latitude ?? tower.centroid_lat;
          const lon = (tower as any).longitude ?? tower.centroid_lon;
          const name = (tower as any).location_name ?? tower.name ?? tower.tower_id;
          const operator = (tower as any).operator ?? 'Airtel Delhi';
          const cellId = (tower as any).cell_id ?? '40041 / 8812';
          const count = tower.call_count ?? (tower as any).event_count ?? tower.hit_count ?? 12;

          const isSelected = tid === selectedTowerId;
          const isTargetRoute = count > 0;

          const markerIcon = isSelected
            ? SELECTED_ICON
            : isTargetRoute
            ? TARGET_ROUTE_ICON
            : DEFAULT_ICON;

          return (
            <Marker
              key={tid}
              position={[lat, lon]}
              icon={markerIcon}
              eventHandlers={{
                click: () => onSelectTower(tid),
              }}
            >
              {/* CELL TOWER DETAILS & IMAGE HOVER POPUP */}
              <Popup className="civix-tower-popup shadow-2xl z-[2000]" autoPan={true} maxWidth={240}>
                <div className="w-56 bg-[#090D16] text-white p-2 rounded border border-[#1E293B] shadow-2xl font-sans text-xs">
                  {/* Tower Photo Header */}
                  <div className="relative w-full h-20 rounded overflow-hidden border border-[#1E293B] mb-1.5 bg-[#070A11]">
                    <img
                      src="/assets/indian_telecom_tower.png"
                      alt="Cell Tower Structure"
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-1 right-1 px-1.5 py-0.5 rounded bg-red-600/90 text-[8px] font-bold text-white uppercase tracking-wider shadow font-mono">
                      {operator}
                    </div>
                  </div>

                  {/* Tower Details */}
                  <div className="space-y-1">
                    <div className="flex items-center space-x-1 text-cyan-400">
                      <Radio className="w-3 h-3 flex-shrink-0" />
                      <h4 className="font-bold text-white truncate text-[11px]">
                        {name}
                      </h4>
                    </div>

                    <div className="grid grid-cols-2 gap-x-1.5 gap-y-0.5 text-[9px] text-slate-300 pt-0.5 border-t border-[#1A2333]">
                      <div>
                        <span className="text-slate-500 uppercase font-mono text-[8px]">Tower ID</span>
                        <span className="font-mono text-slate-200 font-bold block truncate">{tid}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 uppercase font-mono text-[8px]">LAC / CID</span>
                        <span className="font-mono text-slate-200 font-bold block">{cellId}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 uppercase font-mono text-[8px]">Coordinates</span>
                        <span className="font-mono text-slate-300 block">
                          {lat.toFixed(3)}, {lon.toFixed(3)}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-500 uppercase font-mono text-[8px]">Activity</span>
                        <span className="font-mono text-amber-400 font-bold block">{count} events</span>
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
