import React, { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { SpatialCaseFeature } from '../../api/spatial';
import { Shield, Plus, Minus, Target, Maximize2 } from 'lucide-react';

interface CaseRegistryMapProps {
  cases: SpatialCaseFeature[];
  selectedCaseId: string | null;
  onSelectCase: (caseId: string) => void;
  onOpenCaseWorkspace: (caseId: string) => void;
  totalCaseCount?: number;
}

// ── Landmark City Labels matching Visual Reference ───────────────────────────

const NCR_LANDMARKS = [
  { id: 'dwarka_sec23', name: 'Dwarka Sector 23', coords: [28.5921, 77.0511] as [number, number] },
  { id: 'dwarka', name: 'Dwarka', coords: [28.5880, 77.0400] as [number, number] },
  { id: 'gurugram', name: 'Gurugram', coords: [28.4595, 77.0266] as [number, number] },
  { id: 'igi', name: 'IGI Airport', coords: [28.5562, 77.1000] as [number, number] },
  { id: 'new_delhi', name: 'New Delhi', coords: [28.6139, 77.2090] as [number, number] },
  { id: 'faridabad', name: 'Faridabad', coords: [28.4089, 77.3178] as [number, number] },
  { id: 'noida', name: 'Noida', coords: [28.5355, 77.3910] as [number, number] },
  { id: 'ghaziabad', name: 'Ghaziabad', coords: [28.6692, 77.4538] as [number, number] },
];

const createCityLabelIcon = (cityName: string) => {
  return L.divIcon({
    className: 'civix-city-label-icon',
    html: `
      <div style="
        display: flex;
        align-items: center;
        gap: 5px;
        font-family: monospace, system-ui, sans-serif;
        font-size: 11px;
        font-weight: 800;
        color: #e2e8f0;
        text-shadow: 0 1px 4px #000000, 0 0 10px #000000;
        white-space: nowrap;
        pointer-events: none;
        letter-spacing: 0.05em;
      ">
        <span style="width: 5px; height: 5px; border-radius: 50%; background: #38bdf8; box-shadow: 0 0 8px #38bdf8; display: inline-block;"></span>
        <span>${cityName}</span>
      </div>
    `,
    iconSize: [110, 20],
    iconAnchor: [55, 10]
  });
};

// ── Custom Marker Icons with Sonar Pulse Ring Animations ─────────────────────

const createCustomCaseMarkerIcon = (feat: SpatialCaseFeature, isSelected: boolean) => {
  const { priority, status, event_count } = feat.properties;
  const isCritical = priority === 'CRITICAL';

  if (isSelected) {
    // Red teardrop location pin marker with sonar pulse ring animation
    const html = `
      <div style="position: relative; width: 40px; height: 48px; display: flex; align-items: center; justify-content: center;">
        <div class="civix-sonar-ring-red"></div>
        <svg width="34" height="42" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0 4px 14px rgba(239, 68, 68, 0.95)); z-index: 10;">
          <path d="M12 0C5.37 0 0 5.37 0 12C0 21 12 30 12 30C12 30 24 21 24 12C24 5.37 18.63 0 12 0Z" fill="url(#pinGrad)" stroke="#ffffff" stroke-width="1.8"/>
          <circle cx="12" cy="11" r="4.5" fill="#ffffff"/>
          <defs>
            <linearGradient id="pinGrad" x1="0" y1="0" x2="24" y2="30" gradientUnits="userSpaceOnUse">
              <stop stop-color="#ef4444"/>
              <stop offset="1" stop-color="#991b1b"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
    `;
    return L.divIcon({
      className: 'civix-selected-pin-marker',
      html,
      iconSize: [40, 48],
      iconAnchor: [20, 44],
      popupAnchor: [0, -40]
    });
  }

  // Vivid Glowing Animated Node Badges
  let grad = 'radial-gradient(circle at 35% 35%, #38bdf8 0%, #0284c7 60%, #0369a1 100%)'; // Blue/Cyan default
  let glow = '0 0 16px rgba(56, 189, 248, 0.95), 0 0 28px rgba(56, 189, 248, 0.4)';
  let border = '#38bdf8';
  let textColor = '#ffffff';
  let sonarRingHtml = '';

  if (isCritical) {
    grad = 'radial-gradient(circle at 35% 35%, #f87171 0%, #dc2626 60%, #7f1d1d 100%)'; // Red
    glow = '0 0 18px rgba(239, 68, 68, 0.95), 0 0 30px rgba(239, 68, 68, 0.5)';
    border = '#ef4444';
    sonarRingHtml = '<div class="civix-sonar-ring-red"></div>';
  } else if (status === 'ACTIVE' || status === 'OPEN') {
    grad = 'radial-gradient(circle at 35% 35%, #34d399 0%, #059669 60%, #064e3b 100%)'; // Green
    glow = '0 0 18px rgba(16, 185, 129, 0.95), 0 0 30px rgba(16, 185, 129, 0.5)';
    border = '#10b981';
    sonarRingHtml = '<div class="civix-sonar-ring-green"></div>';
  } else if (priority === 'HIGH') {
    grad = 'radial-gradient(circle at 35% 35%, #fbbf24 0%, #d97706 60%, #78350f 100%)'; // Amber/Priority
    glow = '0 0 16px rgba(245, 158, 11, 0.95), 0 0 28px rgba(245, 158, 11, 0.4)';
    border = '#f59e0b';
    sonarRingHtml = '<div class="civix-sonar-ring-gold"></div>';
  }

  const size = isCritical ? 26 : (status === 'ACTIVE' || status === 'OPEN' ? 24 : 20);

  const html = `
    <div style="position: relative; width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center;">
      ${sonarRingHtml}
      <div style="
        position: relative;
        width: ${size}px;
        height: ${size}px;
        background: ${grad};
        border: 2px solid ${border};
        border-radius: 50%;
        box-shadow: ${glow};
        display: flex;
        align-items: center;
        justify-content: center;
        color: ${textColor};
        font-size: ${size > 22 ? '10px' : '8px'};
        font-weight: 900;
        font-family: monospace;
        z-index: 5;
      " class="animate-node-pulse">
        ${event_count > 0 ? event_count : ''}
      </div>
    </div>
  `;

  return L.divIcon({
    className: 'civix-node-cluster-marker',
    html,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2]
  });
};

// ── Map Controller & Controls ────────────────────────────────────────────────

const MapController: React.FC<{
  cases: SpatialCaseFeature[];
  selectedId: string | null;
}> = ({ cases, selectedId }) => {
  const map = useMap();

  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 200);
    return () => clearTimeout(timer);
  }, [map]);

  useEffect(() => {
    if (selectedId) {
      const selected = cases.find((c) => c.properties.case_id === selectedId);
      if (selected && selected.geometry?.coordinates) {
        const [lon, lat] = selected.geometry.coordinates;
        map.flyTo([lat, lon], 13, { duration: 1.2 });
      }
    }
  }, [selectedId, cases, map]);

  return null;
};

const MapControls: React.FC<{ onFitNCR: () => void }> = ({ onFitNCR }) => {
  const map = useMap();

  return (
    <div className="absolute top-3 right-3 z-[1000] flex flex-col items-end space-y-2">
      <div className="bg-[#0c1017]/95 backdrop-blur-md border border-[#1e293b] rounded-sm shadow-2xl flex flex-col overflow-hidden text-slate-300 divide-y divide-[#1e293b]">
        <button
          onClick={() => map.zoomIn()}
          className="p-2 hover:bg-[#1e293b] hover:text-white transition-colors"
          title="Zoom In"
        >
          <Plus className="w-4 h-4" />
        </button>
        <button
          onClick={() => map.zoomOut()}
          className="p-2 hover:bg-[#1e293b] hover:text-white transition-colors"
          title="Zoom Out"
        >
          <Minus className="w-4 h-4" />
        </button>
        <button
          onClick={onFitNCR}
          className="p-2 hover:bg-[#1e293b] hover:text-cyan-400 transition-colors"
          title="Center Delhi NCR"
        >
          <Target className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

// ── Main CaseRegistryMap Component ──────────────────────────────────────────

export const CaseRegistryMap: React.FC<CaseRegistryMapProps> = ({
  cases,
  selectedCaseId,
  onSelectCase,
  onOpenCaseWorkspace,
  totalCaseCount = 268
}) => {
  const centerNCR: [number, number] = [28.595, 77.160];
  const [activeLayer, setActiveLayer] = useState<'density' | 'jurisdictions' | 'police' | 'roads' | 'satellite'>('density');
  const [showAllMapCases, setShowAllMapCases] = useState(false);
  const [mapInstance, setMapInstance] = useState<L.Map | null>(null);

  // Map Cases Filter: By default show ONLY Critical cases + whichever case is selected from right menu
  const visibleCases = useMemo(() => {
    return cases.filter((feat) => {
      const isCritical = feat.properties.priority === 'CRITICAL';
      const isSelected = feat.properties.case_id === selectedCaseId;
      if (showAllMapCases) return true;
      return isCritical || isSelected;
    });
  }, [cases, selectedCaseId, showAllMapCases]);

  // Constellation streaming network polylines connecting key multi-event spatial nodes
  const networkLines = useMemo(() => {
    const lines: Array<{ id: string; coords: [ [number, number], [number, number] ]; color: string }> = [];

    const spatialPts = visibleCases.filter(c => c.geometry?.coordinates && (c.properties.priority === 'CRITICAL' || c.properties.event_count >= 3));

    for (let i = 0; i < spatialPts.length; i++) {
      const p1 = spatialPts[i];
      const [lon1, lat1] = p1.geometry.coordinates;

      for (let j = i + 1; j < spatialPts.length; j++) {
        const p2 = spatialPts[j];
        const [lon2, lat2] = p2.geometry.coordinates;
        const dist = Math.sqrt(Math.pow(lat1 - lat2, 2) + Math.pow(lon1 - lon2, 2));

        if (dist < 0.22) {
          lines.push({
            id: `line-${p1.properties.case_id}-${p2.properties.case_id}`,
            coords: [[lat1, lon1], [lat2, lon2]],
            color: p1.properties.priority === 'CRITICAL' ? 'rgba(239, 68, 68, 0.65)' : 'rgba(56, 189, 248, 0.55)'
          });
        }
      }
    }
    return lines.slice(0, 30);
  }, [visibleCases]);

  const handleFitNCR = () => {
    if (mapInstance) {
      mapInstance.flyTo([28.595, 77.160], 11, { duration: 1 });
    }
  };

  return (
    <div className="relative w-full h-[440px] bg-[#070a0f] border border-civix-border/80 rounded-md overflow-hidden font-mono select-none shadow-2xl">
      {/* ── Top Left Title & View Mode Toggle Overlay ───────────────────────── */}
      <div className="absolute top-3 left-3 z-[1000] bg-[#0c1017]/90 backdrop-blur-md border border-[#1e293b] px-3 py-1.5 rounded-md shadow-xl flex items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse shadow-[0_0_8px_#ef4444]" />
          <div>
            <h3 className="text-xs font-bold text-slate-100 tracking-wider uppercase font-mono leading-none">
              Case Geographic Intelligence
            </h3>
            <p className="text-[9px] text-slate-400 mt-0.5 font-mono">
              Delhi NCR • <span className="text-cyan-400 font-bold">{visibleCases.length} cases showing</span>
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowAllMapCases(!showAllMapCases)}
          className={`px-2.5 py-1 rounded-sm text-[10px] font-mono font-bold transition-all border ${
            showAllMapCases
              ? 'bg-blue-600/40 text-cyan-300 border-blue-500/60 shadow-[0_0_8px_rgba(56,189,248,0.25)]'
              : 'bg-red-500/20 text-red-300 border-red-500/40 hover:bg-red-500/30'
          }`}
        >
          {showAllMapCases ? 'Show All (268)' : 'Critical Only (27)'}
        </button>
      </div>

      {/* ── Bottom Operational Layer Toolbar matching Visual Lock ────────────── */}
      <div className="absolute bottom-3 left-3 z-[1000] flex items-center space-x-1.5 bg-[#0c1017]/95 backdrop-blur-md border border-[#1e293b] p-1 rounded-md shadow-2xl text-[10px]">
        {[
          { id: 'density', label: 'Case Density' },
          { id: 'jurisdictions', label: 'Jurisdictions' },
          { id: 'police', label: 'Police Stations' },
          { id: 'roads', label: 'Major Roads' },
          { id: 'satellite', label: 'Satellite' }
        ].map((layer) => (
          <button
            key={layer.id}
            onClick={() => setActiveLayer(layer.id as any)}
            className={`px-2.5 py-1 rounded-sm font-mono font-semibold transition-colors flex items-center space-x-1 ${
              activeLayer === layer.id
                ? 'bg-blue-600/40 text-cyan-300 border border-blue-500/60 font-bold shadow-[0_0_10px_rgba(56,189,248,0.2)]'
                : 'text-slate-400 hover:text-slate-200 hover:bg-[#1e293b]'
            }`}
          >
            <span>{layer.label}</span>
          </button>
        ))}
      </div>

      {/* ── Floating Bottom Right Scale Bar & Fit NCR Button ──────────────────── */}
      <div className="absolute bottom-3 right-3 z-[1000] flex items-center space-x-3">
        <div className="bg-[#0c1017]/90 border border-[#1e293b] px-2.5 py-1 rounded-xs text-[10px] text-slate-300 font-mono flex items-center space-x-2">
          <span>10 km</span>
          <div className="w-8 h-1 bg-slate-500 border-x border-white" />
        </div>

        <button
          onClick={handleFitNCR}
          className="bg-[#0c1017]/95 hover:bg-[#1e293b] border border-[#1e293b] px-3 py-1 rounded-xs text-[10px] font-mono font-bold text-cyan-400 hover:text-white transition-colors flex items-center space-x-1.5 shadow-xl"
        >
          <Maximize2 className="w-3 h-3" />
          <span>Fit NCR</span>
        </button>
      </div>

      {/* ── Leaflet Interactive Map Container ────────────────────────────────── */}
      <MapContainer
        center={centerNCR}
        zoom={11}
        zoomControl={false}
        style={{ width: '100%', height: '100%', background: '#070a0f' }}
        scrollWheelZoom={true}
        ref={setMapInstance}
      >
        {/* Esri Dark Gray Canvas Base Tile Layer */}
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          url={
            activeLayer === 'satellite'
              ? 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
              : 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}'
          }
          maxZoom={19}
          className="civix-tactical-map-tiles"
        />

        <MapController cases={cases} selectedId={selectedCaseId} />
        <MapControls onFitNCR={handleFitNCR} />

        {/* Render Landmark City Labels on the Map */}
        {NCR_LANDMARKS.map((lm) => (
          <Marker
            key={lm.id}
            position={lm.coords}
            icon={createCityLabelIcon(lm.name)}
            interactive={false}
          />
        ))}

        {/* Render Constellation Network Lines between spatial case nodes */}
        {networkLines.map((line) => (
          <Polyline
            key={line.id}
            positions={line.coords}
            className="civix-animated-polyline"
            pathOptions={{
              color: line.color,
              weight: 1.8,
              opacity: 0.8
            }}
          />
        ))}

        {/* Render Database Spatial Footprints (Filtered to Critical/Selected by default) */}
        {visibleCases.map((feat) => {
          const { case_id, case_number, title, jurisdiction } = feat.properties;
          const [lon, lat] = feat.geometry.coordinates;
          const isSelected = case_id === selectedCaseId;

          return (
            <Marker
              key={case_id}
              position={[lat, lon]}
              icon={createCustomCaseMarkerIcon(feat, isSelected)}
              eventHandlers={{
                click: () => onSelectCase(case_id)
              }}
            >
              <Popup className="civix-map-hud-popup">
                <div className="p-1 max-w-xs font-mono text-slate-100 bg-[#0c1017]">
                  <div className="flex items-center justify-between gap-2 border-b border-[#1e293b] pb-1.5 mb-1.5">
                    <span className="text-xs font-extrabold text-cyan-400">
                      {jurisdiction || 'Delhi Sector'}
                    </span>
                  </div>

                  <p className="text-[9px] text-amber-400 font-extrabold font-mono">
                    {case_number}
                  </p>
                  <p className="text-[11px] font-bold text-slate-200 mt-0.5">
                    {title}
                  </p>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenCaseWorkspace(case_id);
                    }}
                    className="mt-3 w-full bg-blue-600 hover:bg-blue-500 text-white py-1.5 px-3 rounded-xs text-[10px] font-mono font-bold flex items-center justify-center space-x-1 transition-colors"
                  >
                    <span>Open Case →</span>
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
