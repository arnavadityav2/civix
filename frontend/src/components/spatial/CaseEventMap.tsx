import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { SpatialEventFeature, EpistemicStatus } from '../../api/spatial';

interface CaseEventMapProps {
  events: SpatialEventFeature[];
  selectedEventId: string | null;
  onSelectEvent: (event: SpatialEventFeature) => void;
}

const getEpistemicColor = (status: EpistemicStatus): { bg: string; border: string; opacity: number } => {
  switch (status) {
    case 'CONFIRMED':
      return { bg: '#10b981', border: '#ffffff', opacity: 1.0 };
    case 'PROBABLE':
      return { bg: '#d97706', border: '#ffffff', opacity: 0.9 };
    case 'POSSIBLE':
      return { bg: '#64748b', border: '#ffffff', opacity: 0.75 };
    case 'REFUTED':
      return { bg: '#ef4444', border: '#ffffff', opacity: 0.6 };
    case 'INCONCLUSIVE':
    default:
      return { bg: '#94a3b8', border: '#ffffff', opacity: 0.6 };
  }
};

const createEventMarkerIcon = (feat: SpatialEventFeature, isSelected: boolean) => {
  const { epistemic_status, location_predicate } = feat.properties;
  const { bg, border } = getEpistemicColor(epistemic_status);
  const size = isSelected ? 22 : 16;
  const isTower = location_predicate === 'PINGED_TOWER';

  const html = `
    <div style="
      width: ${size}px;
      height: ${size}px;
      background-color: ${bg};
      border: 2px solid ${border};
      border-radius: ${isTower ? '3px' : '50%'};
      box-shadow: ${isSelected ? `0 0 0 4px ${bg}55, 0 2px 6px rgba(0,0,0,0.3)` : '0 1px 3px rgba(0,0,0,0.25)'};
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: ${isSelected ? '10px' : '8px'};
      font-weight: bold;
    ">
    </div>
  `;

  return L.divIcon({
    className: 'civix-event-marker',
    html,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  });
};

const MapBoundsUpdater: React.FC<{ events: SpatialEventFeature[]; selectedId: string | null }> = ({ events, selectedId }) => {
  const map = useMap();

  useEffect(() => {
    if (selectedId) {
      const selected = events.find(e => e.properties.event_location_id === selectedId);
      if (selected && selected.geometry) {
        if (selected.geometry.type === 'Point') {
          const [lon, lat] = selected.geometry.coordinates as [number, number];
          map.flyTo([lat, lon], 14, { duration: 1.0 });
        }
      }
    } else if (events.length > 0) {
      const points: [number, number][] = [];
      events.forEach(e => {
        if (e.geometry.type === 'Point') {
          const [lon, lat] = e.geometry.coordinates as [number, number];
          points.push([lat, lon]);
        } else if (e.geometry.type === 'LineString') {
          const coords = e.geometry.coordinates as [number, number][];
          coords.forEach(([lon, lat]) => points.push([lat, lon]));
        }
      });

      if (points.length > 0) {
        const bounds = L.latLngBounds(points);
        map.fitBounds(bounds, { padding: [40, 40] });
      }
    }
  }, [selectedId, events, map]);

  return null;
};

export const CaseEventMap: React.FC<CaseEventMapProps> = ({
  events,
  selectedEventId,
  onSelectEvent
}) => {
  const defaultCenter: [number, number] = [28.6139, 77.2090];

  return (
    <div className="w-full h-full min-h-[460px] relative rounded overflow-hidden border border-slate-200 bg-slate-100 z-0">
      {/* On-Map Epistemic Status Legend Overlay */}
      <div className="absolute top-3 right-3 z-[1000] bg-white/95 backdrop-blur-xs border border-slate-200 rounded p-3 shadow-md w-48 text-xs font-sans">
        <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 border-b border-slate-100 pb-1">
          EPISTEMIC STATUS
        </h4>
        <div className="space-y-1.5 text-[11px]">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
            <span className="text-slate-800 font-semibold">CONFIRMED</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-600 inline-block"></span>
            <span className="text-slate-800 font-semibold">PROBABLE</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-500 inline-block"></span>
            <span className="text-slate-700">POSSIBLE</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"></span>
            <span className="text-slate-700 line-through">REFUTED</span>
          </div>
        </div>
      </div>

      <MapContainer
        center={defaultCenter}
        zoom={11}
        style={{ width: '100%', height: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapBoundsUpdater events={events} selectedId={selectedEventId} />

        {events.map((feat) => {
          const { event_location_id, location_name, event_type, location_predicate, epistemic_status } = feat.properties;
          const isSelected = event_location_id === selectedEventId;

          if (feat.geometry.type === 'Point') {
            const [lon, lat] = feat.geometry.coordinates as [number, number];

            return (
              <Marker
                key={event_location_id}
                position={[lat, lon]}
                icon={createEventMarkerIcon(feat, isSelected)}
                eventHandlers={{
                  click: () => onSelectEvent(feat)
                }}
              >
                <Popup className="civix-map-popup">
                  <div className="p-1 max-w-xs font-sans">
                    <span className="text-[9px] font-mono font-bold text-slate-400 uppercase">{event_type}</span>
                    <h3 className="font-bold text-slate-900 text-xs mt-0.5 leading-tight">{location_name}</h3>
                    <div className="flex items-center space-x-1.5 mt-2">
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-blue-50 text-blue-800 border border-blue-200">
                        {location_predicate}
                      </span>
                      <span className="text-[9px] font-bold text-slate-600">
                        {epistemic_status}
                      </span>
                    </div>
                    <button
                      onClick={() => onSelectEvent(feat)}
                      className="mt-2.5 w-full bg-[#1a3a6c] hover:bg-[#132c54] text-white text-[11px] font-semibold py-1 px-2 rounded transition-colors"
                    >
                      Inspect Event Details
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          } else if (feat.geometry.type === 'LineString') {
            // Render native PostGIS ST_LineString geometry as a Polyline
            const lineCoords = (feat.geometry.coordinates as [number, number][]).map(
              ([lon, lat]) => [lat, lon] as [number, number]
            );

            return (
              <Polyline
                key={event_location_id}
                positions={lineCoords}
                pathOptions={{
                  color: isSelected ? '#ff9933' : '#1a3a6c',
                  weight: isSelected ? 5 : 3.5,
                  opacity: 0.85
                }}
                eventHandlers={{
                  click: () => onSelectEvent(feat)
                }}
              />
            );
          }

          return null;
        })}
      </MapContainer>
    </div>
  );
};
