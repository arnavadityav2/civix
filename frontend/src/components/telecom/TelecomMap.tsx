import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Polygon, Circle, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { TelecomTower, TelecomEventItem } from '../../api/telecom';

interface TelecomMapProps {
  towers: TelecomTower[];
  events: TelecomEventItem[];
  selectedTowerId: string | null;
  selectedEventId: string | null;
  onSelectTower: (towerId: string | null) => void;
  overlayOptions: {
    cellTowers: boolean;
    coverageArea: boolean;
    devicePings: boolean;
    movementPath: boolean;
    selectedTower: boolean;
    mapLabels: boolean;
  };
  onToggleOverlay: (key: keyof TelecomMapProps['overlayOptions']) => void;
}

// Custom DivIcons matching reference image styling exactly
const createTowerIcon = (isSelected: boolean, name: string) => {
  const color = isSelected ? '#f59e0b' : '#3b82f6';
  const size = isSelected ? 32 : 26;

  const html = `
    <div style="
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    ">
      <div style="
        width: ${size}px;
        height: ${size}px;
        background: rgba(17, 24, 39, 0.9);
        border: 2px solid ${color};
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: ${isSelected ? `0 0 12px ${color}88` : '0 2px 4px rgba(0,0,0,0.5)'};
      ">
        <svg width="${size - 10}" height="${size - 10}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2L4 22h16L12 2z"/>
          <path d="M12 6v16"/>
          <path d="M8 14h8"/>
          <path d="M7 18h10"/>
        </svg>
      </div>
      <div style="
        margin-top: 3px;
        background: rgba(11, 15, 25, 0.85);
        border: 1px solid ${isSelected ? '#f59e0b88' : '#1e293b'};
        padding: 1px 5px;
        border-radius: 3px;
        font-family: monospace;
        font-size: 9px;
        font-weight: bold;
        color: ${isSelected ? '#fbbf24' : '#94a3b8'};
        white-space: nowrap;
        pointer-events: none;
      ">
        ${name.replace('Investigative Location — ', '').substring(0, 16)}
      </div>
    </div>
  `;

  return L.divIcon({
    className: 'civix-tower-marker',
    html,
    iconSize: [size + 40, size + 24],
    iconAnchor: [(size + 40) / 2, size / 2],
  });
};

const createPingMarkerIcon = (isSelected: boolean) => {
  const color = isSelected ? '#ef4444' : '#f59e0b';
  const size = isSelected ? 12 : 8;

  const html = `
    <div style="
      width: ${size}px;
      height: ${size}px;
      background-color: ${color};
      border: 1.5px solid #0f172a;
      border-radius: 50%;
      box-shadow: ${isSelected ? `0 0 8px ${color}` : '0 1px 3px rgba(0,0,0,0.6)'};
    "></div>
  `;

  return L.divIcon({
    className: 'civix-ping-marker',
    html,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

const MapBoundsController: React.FC<{
  towers: TelecomTower[];
  events: TelecomEventItem[];
  selectedTowerId: string | null;
}> = ({ towers, events, selectedTowerId }) => {
  const map = useMap();

  useEffect(() => {
    if (selectedTowerId) {
      const selected = towers.find((t) => t.tower_id === selectedTowerId);
      if (selected && selected.centroid_lat && selected.centroid_lon) {
        map.flyTo([selected.centroid_lat, selected.centroid_lon], 13, { duration: 0.8 });
        return;
      }
    }

    const points: [number, number][] = [];
    towers.forEach((t) => {
      if (t.centroid_lat && t.centroid_lon) {
        points.push([t.centroid_lat, t.centroid_lon]);
      }
    });

    events.forEach((e) => {
      if (e.location_lat && e.location_lon) {
        points.push([e.location_lat, e.location_lon]);
      }
    });

    if (points.length > 0) {
      const bounds = L.latLngBounds(points);
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [selectedTowerId, towers, events, map]);

  return null;
};

export const TelecomMap: React.FC<TelecomMapProps> = ({
  towers,
  events,
  selectedTowerId,
  selectedEventId,
  onSelectTower,
  overlayOptions,
  onToggleOverlay,
}) => {
  // Default to Delhi NCR center [28.6139, 77.2090]
  const defaultCenter: [number, number] = [28.6139, 77.2090];

  // Construct movement path connecting observations chronologically
  const movementPath = React.useMemo(() => {
    const validLocs = events
      .filter((e) => e.location_lat !== null && e.location_lon !== null && e.start !== null)
      .sort((a, b) => new Date(a.start!).getTime() - new Date(b.start!).getTime());

    return validLocs.map((e) => [e.location_lat!, e.location_lon!] as [number, number]);
  }, [events]);

  return (
    <div className="w-full h-full min-h-[440px] relative rounded-md overflow-hidden border border-[#1E293B] bg-[#090D16] select-none">
      {/* Map Overlays Control Box (Top Right inside map) matching reference image */}
      <div className="absolute top-3 right-3 z-[1000] bg-[#0C121E]/90 border border-[#1E293B] rounded-md p-2.5 shadow-lg text-xs space-y-1.5 min-w-[140px]">
        <label className="flex items-center space-x-2 text-slate-300 hover:text-white cursor-pointer select-none">
          <input
            type="checkbox"
            checked={overlayOptions.cellTowers}
            onChange={() => onToggleOverlay('cellTowers')}
            className="w-3.5 h-3.5 rounded bg-[#111827] border-[#374151] text-blue-500 focus:ring-0"
          />
          <span className="flex items-center gap-1.5 text-[11px] font-medium">
            <span className="w-2 h-2 rounded-sm bg-blue-500"></span> Cell Towers
          </span>
        </label>

        <label className="flex items-center space-x-2 text-slate-300 hover:text-white cursor-pointer select-none">
          <input
            type="checkbox"
            checked={overlayOptions.coverageArea}
            onChange={() => onToggleOverlay('coverageArea')}
            className="w-3.5 h-3.5 rounded bg-[#111827] border-[#374151] text-blue-500 focus:ring-0"
          />
          <span className="flex items-center gap-1.5 text-[11px] font-medium">
            <span className="w-2 h-2 rounded-full border border-blue-400 bg-blue-500/20"></span> Coverage Area
          </span>
        </label>

        <label className="flex items-center space-x-2 text-slate-300 hover:text-white cursor-pointer select-none">
          <input
            type="checkbox"
            checked={overlayOptions.devicePings}
            onChange={() => onToggleOverlay('devicePings')}
            className="w-3.5 h-3.5 rounded bg-[#111827] border-[#374151] text-blue-500 focus:ring-0"
          />
          <span className="flex items-center gap-1.5 text-[11px] font-medium">
            <span className="w-2 h-2 rounded-full bg-amber-500"></span> Device Pings
          </span>
        </label>

        <label className="flex items-center space-x-2 text-slate-300 hover:text-white cursor-pointer select-none">
          <input
            type="checkbox"
            checked={overlayOptions.movementPath}
            onChange={() => onToggleOverlay('movementPath')}
            className="w-3.5 h-3.5 rounded bg-[#111827] border-[#374151] text-blue-500 focus:ring-0"
          />
          <span className="flex items-center gap-1.5 text-[11px] font-medium">
            <span className="w-3 h-0.5 bg-blue-400"></span> Movement Path
          </span>
        </label>

        <label className="flex items-center space-x-2 text-slate-300 hover:text-white cursor-pointer select-none">
          <input
            type="checkbox"
            checked={overlayOptions.selectedTower}
            onChange={() => onToggleOverlay('selectedTower')}
            className="w-3.5 h-3.5 rounded bg-[#111827] border-[#374151] text-amber-500 focus:ring-0"
          />
          <span className="flex items-center gap-1.5 text-[11px] font-medium">
            <span className="w-2.5 h-2.5 text-amber-400 font-bold">★</span> Selected Tower
          </span>
        </label>

        <label className="flex items-center space-x-2 text-slate-300 hover:text-white cursor-pointer select-none">
          <input
            type="checkbox"
            checked={overlayOptions.mapLabels}
            onChange={() => onToggleOverlay('mapLabels')}
            className="w-3.5 h-3.5 rounded bg-[#111827] border-[#374151] text-blue-500 focus:ring-0"
          />
          <span className="flex items-center gap-1.5 text-[11px] font-medium">
            🏷️ Map Labels
          </span>
        </label>
      </div>

      <MapContainer
        center={defaultCenter}
        zoom={11}
        style={{ width: '100%', height: '100%' }}
        scrollWheelZoom={true}
        zoomControl={false}
      >
        <TileLayer
          attribution='Tiles &copy; Esri &mdash; Dark Gray Canvas'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        />

        <MapBoundsController towers={towers} events={events} selectedTowerId={selectedTowerId} />

        {/* Movement Path (Dashed blue polyline) */}
        {overlayOptions.movementPath && movementPath.length >= 2 && (
          <Polyline
            positions={movementPath}
            pathOptions={{
              color: '#3b82f6',
              weight: 2.5,
              dashArray: '6, 8',
              opacity: 0.85,
            }}
          />
        )}

        {/* Render Tower Coverage Areas */}
        {overlayOptions.coverageArea &&
          towers.map((t) => {
            const isSelected = t.tower_id === selectedTowerId;
            if (!t.centroid_lat || !t.centroid_lon) return null;

            // Render PostGIS polygon geometry if available
            if (t.geometry && t.geometry.type === 'Polygon') {
              const ring = (t.geometry.coordinates as [number, number][][])[0];
              const positions = ring.map(([lon, lat]) => [lat, lon] as [number, number]);

              return (
                <Polygon
                  key={`coverage-poly-${t.tower_id}`}
                  positions={positions}
                  pathOptions={{
                    color: isSelected ? '#f59e0b' : '#3b82f6',
                    fillColor: isSelected ? '#f59e0b' : '#3b82f6',
                    fillOpacity: isSelected ? 0.25 : 0.1,
                    weight: isSelected ? 2 : 1,
                  }}
                />
              );
            }

            // Fallback to circular coverage area using uncertainty radius or default 1500m
            const radius = t.uncertainty_radius_meters || 1500;
            return (
              <Circle
                key={`coverage-circle-${t.tower_id}`}
                center={[t.centroid_lat, t.centroid_lon]}
                radius={radius}
                pathOptions={{
                  color: isSelected ? '#f59e0b' : '#1d4ed8',
                  fillColor: isSelected ? '#f59e0b' : '#3b82f6',
                  fillOpacity: isSelected ? 0.2 : 0.08,
                  weight: isSelected ? 2 : 1,
                  dashArray: isSelected ? undefined : '4, 4',
                }}
              />
            );
          })}

        {/* Render Towers */}
        {overlayOptions.cellTowers &&
          towers.map((t) => {
            const isSelected = t.tower_id === selectedTowerId;
            if (!t.centroid_lat || !t.centroid_lon) return null;

            return (
              <Marker
                key={t.tower_id}
                position={[t.centroid_lat, t.centroid_lon]}
                icon={createTowerIcon(isSelected, t.name || t.tower_id)}
                eventHandlers={{
                  click: () => onSelectTower(isSelected ? null : t.tower_id),
                }}
              >
                <Popup className="civix-map-popup">
                  <div className="p-1 max-w-xs font-sans text-slate-200">
                    <div className="flex items-center justify-between gap-2 border-b border-slate-700/60 pb-1 mb-1.5">
                      <span className="text-[10px] font-mono font-bold text-amber-400">
                        {t.tower_id}
                      </span>
                      <span className="text-[9px] font-mono text-slate-400">
                        Hits: {t.hit_count}
                      </span>
                    </div>
                    <h3 className="font-bold text-white text-xs leading-tight">
                      {t.name || 'Cell Tower'}
                    </h3>
                    <div className="text-[10px] text-slate-400 mt-1 space-y-0.5 font-mono">
                      <div>Lat/Lon: {t.centroid_lat.toFixed(4)}, {t.centroid_lon.toFixed(4)}</div>
                      <div>Calls: {t.call_count} | Pings: {t.ping_count}</div>
                    </div>
                    <button
                      onClick={() => onSelectTower(isSelected ? null : t.tower_id)}
                      className="mt-2.5 w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-1 px-2 text-[11px] rounded transition-all"
                    >
                      {isSelected ? 'Deselect Tower' : 'Filter by this Tower'}
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          })}

        {/* Render Device Pings on map */}
        {overlayOptions.devicePings &&
          events.map((e) => {
            if (!e.location_lat || !e.location_lon) return null;
            const isSelected = e.event_id === selectedEventId;

            return (
              <Marker
                key={`ping-${e.event_id}`}
                position={[e.location_lat, e.location_lon]}
                icon={createPingMarkerIcon(isSelected)}
              >
                <Popup>
                  <div className="p-1 text-xs font-sans text-slate-200">
                    <div className="font-mono text-[9px] text-amber-400 font-bold uppercase">
                      {e.event_type}
                    </div>
                    <div className="font-mono text-white text-xs mt-0.5">
                      {e.caller_msisdn || e.subject_msisdn || 'Target Device'}
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono mt-1">
                      Time: {e.start ? new Date(e.start).toLocaleTimeString() : '—'}
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono">
                      Sector: {e.location_name || 'Cell Sector'}
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
