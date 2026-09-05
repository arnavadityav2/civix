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
    return { bg: '#ef4444', border: '#111318', ring: 'rgba(239, 68, 68, 0.4)' };
  }
  if (priority === 'HIGH') {
    return { bg: '#f59e0b', border: '#111318', ring: 'rgba(245, 158, 11, 0.4)' };
  }
  if (priority === 'MEDIUM') {
    return { bg: '#d97706', border: '#111318', ring: 'rgba(217, 119, 6, 0.4)' };
  }
  if (priority === 'LOW') {
    return { bg: '#10b981', border: '#111318', ring: 'rgba(16, 185, 129, 0.4)' };
  }
  return { bg: '#3b82f6', border: '#111318', ring: 'rgba(59, 130, 246, 0.4)' };
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
      border-radius: 2px;
      box-shadow: ${isSelected ? `0 0 0 4px ${bg}66, 0 2px 6px rgba(0,0,0,0.5)` : '0 1px 4px rgba(0,0,0,0.4)'};
      display: flex;
      align-items: center;
      justify-content: center;
      color: #0b0c10;
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
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 150);
    return () => clearTimeout(timer);
  }, [map]);

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
    <div className="w-full h-full min-h-[460px] relative rounded-sm overflow-hidden border border-civix-border bg-civix-bg z-0">
      {/* On-Map Dynamic Legend Overlay Card (Top Right) */}
      <div className="absolute top-3 right-3 z-[1000] bg-civix-surface-2/95 backdrop-blur-xs border border-civix-border rounded-sm p-3 shadow-md w-48 text-xs font-sans">
        <h4 className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-2 border-b border-civix-border/40 pb-1">
          CASE STATUS
        </h4>
        <div className="space-y-1.5 mb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-xs bg-civix-red-500 inline-block"></span>
              <span className="text-civix-text-secondary text-[11px]">Critical</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-civix-text-main">({statusCounts.critical})</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-xs bg-civix-gold-500 inline-block"></span>
              <span className="text-civix-text-secondary text-[11px]">High</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-civix-text-main">({statusCounts.high})</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-xs bg-civix-gold-600 inline-block"></span>
              <span className="text-civix-text-secondary text-[11px]">Medium</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-civix-text-main">({statusCounts.medium})</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-xs bg-civix-green-500 inline-block"></span>
              <span className="text-civix-text-secondary text-[11px]">Low</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-civix-text-main">({statusCounts.low})</span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <span className="w-2.5 h-2.5 rounded-xs bg-civix-text-muted inline-block"></span>
              <span className="text-civix-text-secondary text-[11px]">Closed</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-civix-text-main">({statusCounts.closed})</span>
          </div>
        </div>

        <h4 className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-2 border-b border-civix-border/40 pb-1">
          CASE TYPE
        </h4>
        <div className="space-y-1 text-[11px] text-civix-text-secondary">
          <div className="flex items-center space-x-1.5">
            <Scale className="w-3 h-3 text-civix-text-muted" />
            <span>Financial</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Shield className="w-3 h-3 text-civix-text-muted" />
            <span>Criminal</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <AlertCircle className="w-3 h-3 text-civix-text-muted" />
            <span>Intelligence</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Briefcase className="w-3 h-3 text-civix-text-muted" />
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
          attribution='Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
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
                <div className="p-1 max-w-xs font-sans text-civix-text-main">
                  <span className="civix-id">{case_number}</span>
                  <h3 className="font-bold text-civix-text-main text-xs mt-0.5 leading-tight">{title}</h3>
                  <div className="flex items-center space-x-1.5 mt-2">
                    <span className={`px-1.5 py-0.5 rounded-sm text-[9px] font-bold uppercase border ${
                      priority === 'CRITICAL' ? 'bg-civix-red-950 text-civix-red-400 border-civix-red-600/50' :
                      priority === 'HIGH' ? 'bg-civix-gold-950 text-civix-gold-400 border-civix-gold-600/50' :
                      'bg-civix-gold-950/60 text-civix-gold-400 border-civix-gold-600/40'
                    }`}>
                      {priority}
                    </span>
                    <span className="text-[10px] text-civix-text-muted font-mono">{status}</span>
                  </div>
                  <button
                    onClick={() => onSelectCase(case_id)}
                    className="mt-2.5 w-full civix-btn-primary py-1 px-2 text-[11px] justify-center"
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
