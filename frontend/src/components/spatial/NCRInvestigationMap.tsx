import React, { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { SpatialCaseFeature } from '../../api/spatial';
import { Shield, Scale, AlertCircle, Briefcase } from 'lucide-react';

interface NCRInvestigationMapProps {
  cases: SpatialCaseFeature[];
  selectedCaseId: string | null;
  onSelectCase: (caseId: string) => void;
}

const getMarkerColor = (status: string, priority: string): { bg: string; border: string; ring: string } => {
  if (priority === 'CRITICAL' || status === 'SUSPENDED') {
    return { bg: '#dc2626', border: '#ffffff', ring: 'rgba(220, 38, 38, 0.3)' };
  }
  if (priority === 'HIGH') {
    return { bg: '#ea580c', border: '#ffffff', ring: 'rgba(234, 88, 12, 0.3)' };
  }
  if (priority === 'MEDIUM') {
    return { bg: '#d97706', border: '#ffffff', ring: 'rgba(217, 119, 6, 0.3)' };
  }
  if (priority === 'LOW') {
    return { bg: '#16a34a', border: '#ffffff', ring: 'rgba(22, 163, 74, 0.3)' };
  }
  return { bg: '#475569', border: '#ffffff', ring: 'rgba(71, 85, 105, 0.3)' };
};

const createCaseMarkerIcon = (feat: SpatialCaseFeature, isSelected: boolean) => {
  const { status, priority, event_count } = feat.properties;
  const { bg, border } = getMarkerColor(status, priority);
  const size = isSelected ? 24 : 18;

  const html = `
    <div style="
      width: ${size}px;
      height: ${size}px;
      background-color: ${bg};
      border: 2px solid ${border};
      border-radius: 50%;
      box-shadow: ${isSelected ? `0 0 0 4px ${bg}44, 0 2px 6px rgba(0,0,0,0.3)` : '0 1px 4px rgba(0,0,0,0.25)'};
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: ${isSelected ? '11px' : '9px'};
      font-weight: bold;
      font-family: monospace;
    ">
      ${event_count > 0 ? event_count : ''}
    </div>
  `;

  return L.divIcon({
    className: 'civix-case-marker',
    html,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  });
};

const MapController: React.FC<{ cases: SpatialCaseFeature[]; selectedId: string | null }> = ({ cases, selectedId }) => {
  const map = useMap();

  useEffect(() => {
    if (selectedId) {
      const selected = cases.find(c => c.properties.case_id === selectedId);
      if (selected && selected.geometry?.coordinates) {
        const [lon, lat] = selected.geometry.coordinates;
        map.flyTo([lat, lon], 14, { duration: 1.2 });
      }
    }
  }, [selectedId, cases, map]);

  return null;
};

export const NCRInvestigationMap: React.FC<NCRInvestigationMapProps> = ({
  cases,
  selectedCaseId,
  onSelectCase
}) => {
  const center: [number, number] = [28.6139, 77.2090]; // Delhi NCR Operational Center

  // Compute dynamic case counts from actual API response array
  const statusCounts = useMemo(() => {
    let critical = 0;
    let high = 0;
    let medium = 0;
    let low = 0;
    let closed = 0;

    cases.forEach(c => {
      const prio = c.properties.priority;
      const stat = c.properties.status;
      if (prio === 'CRITICAL') critical++;
      else if (prio === 'HIGH') high++;
      else if (prio === 'MEDIUM') medium++;
      else if (prio === 'LOW') low++;
      else if (stat.startsWith('CLOSED')) closed++;
      else medium++;
    });

    return { critical, high, medium, low, closed };
  }, [cases]);

  return (
    <div className="w-full h-full min-h-[460px] relative rounded overflow-hidden border border-slate-200 bg-slate-100 z-0">
      {/* On-Map Dynamic Legend Overlay Card (Top Right) */}
      <div className="absolute top-3 right-3 z-[1000] bg-white/95 backdrop-blur-xs border border-slate-200 rounded p-3 shadow-md w-48 text-xs font-sans">
        <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 border-b border-slate-100 pb-1">
          CASE STATUS
        </h4>
        <div className="space-y-1.5 mb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-600 inline-block"></span>
              <span className="text-slate-700 text-[11px]">Critical</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-slate-900">({statusCounts.critical})</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-600 inline-block"></span>
              <span className="text-slate-700 text-[11px]">High</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-slate-900">({statusCounts.high})</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-600 inline-block"></span>
              <span className="text-slate-700 text-[11px]">Medium</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-slate-900">({statusCounts.medium})</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block"></span>
              <span className="text-slate-700 text-[11px]">Low</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-slate-900">({statusCounts.low})</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-slate-600 inline-block"></span>
              <span className="text-slate-700 text-[11px]">Closed</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-slate-900">({statusCounts.closed})</span>
          </div>
        </div>

        <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 border-b border-slate-100 pb-1">
          CASE TYPE
        </h4>
        <div className="space-y-1 text-[11px] text-slate-600">
          <div className="flex items-center space-x-1.5">
            <Scale className="w-3 h-3 text-slate-500" />
            <span>Financial</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Shield className="w-3 h-3 text-slate-500" />
            <span>Criminal</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <AlertCircle className="w-3 h-3 text-slate-500" />
            <span>Intelligence</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Briefcase className="w-3 h-3 text-slate-500" />
            <span>Multi-Case</span>
          </div>
        </div>
      </div>

      <MapContainer
        center={center}
        zoom={10}
        style={{ width: '100%', height: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapController cases={cases} selectedId={selectedCaseId} />

        {cases.map((feat) => {
          const { case_id, title, case_number, priority, status } = feat.properties;
          const [lon, lat] = feat.geometry.coordinates;
          const isSelected = case_id === selectedCaseId;

          return (
            <Marker
              key={case_id}
              position={[lat, lon]}
              icon={createCaseMarkerIcon(feat, isSelected)}
              eventHandlers={{
                click: () => onSelectCase(case_id)
              }}
            >
              <Popup className="civix-map-popup">
                <div className="p-1 max-w-xs font-sans">
                  <span className="text-[9px] font-mono font-bold text-slate-400 uppercase">{case_number}</span>
                  <h3 className="font-bold text-slate-900 text-xs mt-0.5 leading-tight">{title}</h3>
                  <div className="flex items-center space-x-1.5 mt-2">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                      priority === 'CRITICAL' ? 'bg-red-50 text-red-700 border border-red-200' :
                      priority === 'HIGH' ? 'bg-orange-50 text-orange-700 border border-orange-200' :
                      'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}>
                      {priority}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">{status}</span>
                  </div>
                  <button
                    onClick={() => onSelectCase(case_id)}
                    className="mt-2.5 w-full bg-[#1a3a6c] hover:bg-[#132c54] text-white text-[11px] font-semibold py-1 px-2 rounded transition-colors"
                  >
                    Inspect Case
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
