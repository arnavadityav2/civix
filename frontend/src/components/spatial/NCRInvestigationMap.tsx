import React, { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Polygon, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import type { SpatialCaseFeature } from '../../api/spatial';

interface NCRInvestigationMapProps {
  cases: SpatialCaseFeature[];
  selectedCaseId: string | null;
  onSelectCase: (caseId: string) => void;
  layers?: {
    districts: boolean;
    roads: boolean;
    metro: boolean;
    heatmap: boolean;
    eventLocations: boolean;
    heroCases: boolean;
  };
  onToggleLayer?: (layerKey: string) => void;
}

// Delhi Region Coordinates & Labels (Approximated Regional Bounding Polygons)
const DELHI_REGIONS = [
  { name: 'NORTH', center: [28.75, 77.15] as [number, number], color: '#3b82f6' },
  { name: 'NORTH WEST', center: [28.72, 77.05] as [number, number], color: '#ef4444' },
  { name: 'NORTH EAST', center: [28.70, 77.26] as [number, number], color: '#f59e0b' },
  { name: 'WEST', center: [28.65, 77.08] as [number, number], color: '#ef4444' },
  { name: 'CENTRAL', center: [28.64, 77.21] as [number, number], color: '#ef4444' },
  { name: 'EAST', center: [28.63, 77.30] as [number, number], color: '#3b82f6' },
  { name: 'SOUTH WEST', center: [28.56, 77.02] as [number, number], color: '#ef4444' },
  { name: 'SOUTH', center: [28.52, 77.22] as [number, number], color: '#f59e0b' },
  { name: 'SOUTH EAST', center: [28.54, 77.28] as [number, number], color: '#3b82f6' },
  { name: 'NEW DELHI', center: [28.61, 77.20] as [number, number], color: '#ef4444' },
];

// Heatmap / Density Nodes across Delhi NCR
const HEATMAP_NODES = [
  { lat: 28.5921, lon: 77.0511, intensity: 1.0, radius: 45 }, // Dwarka
  { lat: 28.7324, lon: 77.1211, intensity: 0.95, radius: 40 }, // Rohini
  { lat: 28.6506, lon: 77.2300, intensity: 0.9, radius: 38 },  // Central / Sadar Bazar
  { lat: 28.6280, lon: 77.2400, intensity: 0.85, radius: 35 }, // Connaught Place
  { lat: 28.5300, lon: 77.2790, intensity: 0.8, radius: 35 },  // Lajpat Nagar / Saket
  { lat: 28.6732, lon: 77.2882, intensity: 0.75, radius: 32 }, // Shahdara
  { lat: 28.4595, lon: 77.0266, intensity: 0.7, radius: 30 },  // Gurugram
  { lat: 28.5562, lon: 77.1000, intensity: 0.65, radius: 28 }, // IGI Airport
  { lat: 28.6090, lon: 76.9855, intensity: 0.85, radius: 35 }, // Najafgarh
];

const getMarkerStyle = (priority: string, isSelected: boolean) => {
  const isCritical = priority === 'CRITICAL';
  const isHigh = priority === 'HIGH';
  const bg = isCritical ? '#ef4444' : isHigh ? '#f59e0b' : '#3b82f6';
  const size = isSelected ? 26 : 20;

  const html = `
    <div style="
      position: relative;
      width: ${size}px;
      height: ${size}px;
      background-color: ${bg};
      border: 2px solid #090C12;
      border-radius: 50%;
      box-shadow: 0 0 12px ${bg}, ${isSelected ? `0 0 0 6px ${bg}44` : '0 2px 4px rgba(0,0,0,0.8)'};
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    ">
      <div style="width: 6px; height: 6px; background-color: #ffffff; border-radius: 50%;"></div>
    </div>
  `;

  return L.divIcon({
    className: 'civix-hero-marker',
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
        map.flyTo([lat, lon], 12.5, { duration: 1.2 });
      }
    }
  }, [selectedId, cases, map]);

  return null;
};

export const NCRInvestigationMap: React.FC<NCRInvestigationMapProps> = ({
  cases,
  selectedCaseId,
  onSelectCase,
  layers = {
    districts: true,
    roads: true,
    metro: false,
    heatmap: true,
    eventLocations: false,
    heroCases: true,
  },
  onToggleLayer
}) => {
  const center: [number, number] = [28.6139, 77.2090]; // Delhi NCR Operational Center

  const [activeLayers, setActiveLayers] = useState(layers);

  useEffect(() => {
    setActiveLayers(layers);
  }, [layers]);

  const handleCheckboxChange = (key: string) => {
    setActiveLayers(prev => ({ ...prev, [key]: !prev[key as keyof typeof prev] }));
    if (onToggleLayer) onToggleLayer(key);
  };

  return (
    <div className="w-full h-full min-h-[500px] relative rounded-md overflow-hidden border border-[#1E2430] bg-[#090C12] select-none">
      
      {/* Top Right Checkbox Layer Control Box (Matching Visual Lock) */}
      <div className="absolute top-4 right-4 z-[1000] bg-[#0D111A]/90 backdrop-blur-md border border-[#1E2430] rounded-lg p-3.5 shadow-xl w-44 text-xs font-sans">
        <div className="space-y-2 text-slate-300">
          <label className="flex items-center space-x-2 cursor-pointer hover:text-white transition-colors">
            <input 
              type="checkbox" 
              checked={activeLayers.districts}
              onChange={() => handleCheckboxChange('districts')}
              className="rounded bg-[#161922] border-[#1E2430] text-blue-500 focus:ring-0 w-3.5 h-3.5 cursor-pointer accent-blue-600"
            />
            <span className="text-xs font-semibold">Police Districts</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer hover:text-white transition-colors">
            <input 
              type="checkbox" 
              checked={activeLayers.roads}
              onChange={() => handleCheckboxChange('roads')}
              className="rounded bg-[#161922] border-[#1E2430] text-blue-500 focus:ring-0 w-3.5 h-3.5 cursor-pointer accent-blue-600"
            />
            <span className="text-xs font-semibold">Major Roads</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer hover:text-white transition-colors">
            <input 
              type="checkbox" 
              checked={activeLayers.metro}
              onChange={() => handleCheckboxChange('metro')}
              className="rounded bg-[#161922] border-[#1E2430] text-blue-500 focus:ring-0 w-3.5 h-3.5 cursor-pointer accent-blue-600"
            />
            <span className="text-xs font-semibold text-slate-400">Metro Network</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer hover:text-white transition-colors">
            <input 
              type="checkbox" 
              checked={activeLayers.heatmap}
              onChange={() => handleCheckboxChange('heatmap')}
              className="rounded bg-[#161922] border-[#1E2430] text-blue-500 focus:ring-0 w-3.5 h-3.5 cursor-pointer accent-blue-600"
            />
            <span className="text-xs font-semibold">Case Heatmap</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer hover:text-white transition-colors">
            <input 
              type="checkbox" 
              checked={activeLayers.eventLocations}
              onChange={() => handleCheckboxChange('eventLocations')}
              className="rounded bg-[#161922] border-[#1E2430] text-blue-500 focus:ring-0 w-3.5 h-3.5 cursor-pointer accent-blue-600"
            />
            <span className="text-xs font-semibold text-slate-400">Event Locations</span>
          </label>

          <label className="flex items-center space-x-2 cursor-pointer hover:text-white transition-colors">
            <input 
              type="checkbox" 
              checked={activeLayers.heroCases}
              onChange={() => handleCheckboxChange('heroCases')}
              className="rounded bg-[#161922] border-[#1E2430] text-blue-500 focus:ring-0 w-3.5 h-3.5 cursor-pointer accent-blue-600"
            />
            <span className="text-xs font-semibold">Hero Cases</span>
          </label>
        </div>
      </div>

      {/* Bottom Left Case Density Legend (Matching Visual Lock) */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-[#0D111A]/90 backdrop-blur-md border border-[#1E2430] rounded-lg p-3 shadow-xl w-52 text-xs font-mono">
        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1.5">
          Case Density
        </span>
        <div className="h-2.5 w-full rounded bg-gradient-to-r from-blue-600 via-yellow-500 to-red-600 mb-1" />
        <div className="flex justify-between text-[10px] text-slate-400 font-bold">
          <span>Low</span>
          <span>High</span>
        </div>

        {/* Scale Bar */}
        <div className="mt-3 pt-2 border-t border-[#1E2430] flex items-center justify-between text-[9px] text-slate-400">
          <span>0</span>
          <span>5</span>
          <span>10</span>
          <span>20 km</span>
        </div>
      </div>

      <MapContainer
        center={center}
        zoom={10.5}
        style={{ width: '100%', height: '100%', backgroundColor: '#090C12' }}
        scrollWheelZoom={true}
        zoomControl={true}
      >
        {/* Dark Tactical Basemap Tiles */}
        <TileLayer
          attribution='&copy; CartoDB &mdash; Map data &copy; OpenStreetMap'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          maxZoom={18}
        />

        <MapController cases={cases} selectedId={selectedCaseId} />

        {/* Delhi Regional Area Labels Overlay */}
        {activeLayers.districts && DELHI_REGIONS.map((reg) => (
          <Marker
            key={reg.name}
            position={reg.center}
            icon={L.divIcon({
              className: 'delhi-region-label',
              html: `<div style="
                color: #94a3b8;
                font-size: 11px;
                font-weight: 800;
                font-family: monospace;
                letter-spacing: 0.1em;
                text-shadow: 0 0 6px rgba(0,0,0,0.9), 0 0 12px rgba(0,0,0,1);
                white-space: nowrap;
                pointer-events: none;
              ">${reg.name}</div>`,
              iconSize: [100, 20],
              iconAnchor: [50, 10]
            })}
          />
        ))}

        {/* Heatmap Density Glow Nodes Layer */}
        {activeLayers.heatmap && HEATMAP_NODES.map((node, idx) => (
          <Marker
            key={`heat-${idx}`}
            position={[node.lat, node.lon]}
            icon={L.divIcon({
              className: 'heat-glow-node',
              html: `<div style="
                width: ${node.radius * 2}px;
                height: ${node.radius * 2}px;
                background: radial-gradient(circle, rgba(239,68,68,${node.intensity * 0.8}) 0%, rgba(245,158,11,${node.intensity * 0.5}) 40%, rgba(59,130,246,0.15) 75%, transparent 100%);
                border-radius: 50%;
                filter: blur(4px);
                pointer-events: none;
              "></div>`,
              iconSize: [node.radius * 2, node.radius * 2],
              iconAnchor: [node.radius, node.radius]
            })}
          />
        ))}

        {/* Hero Case Markers Layer */}
        {activeLayers.heroCases && cases.map((feat) => {
          const { case_id, title, case_number, priority, status } = feat.properties;
          const [lon, lat] = feat.geometry.coordinates;
          const isSelected = case_id === selectedCaseId;

          return (
            <Marker
              key={case_id}
              position={[lat, lon]}
              icon={getMarkerStyle(priority, isSelected)}
              eventHandlers={{
                click: () => onSelectCase(case_id)
              }}
            >
              <Popup className="civix-map-popup">
                <div className="p-2 max-w-xs font-sans text-white bg-[#0D111A] rounded border border-[#1E2430]">
                  <span className="font-mono text-[10px] text-blue-400 font-bold uppercase">{case_number}</span>
                  <h3 className="font-bold text-white text-xs mt-0.5 leading-tight">{title}</h3>
                  <div className="flex items-center space-x-1.5 mt-2">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase border ${
                      priority === 'CRITICAL' ? 'bg-red-950 text-red-400 border-red-600/50' :
                      priority === 'HIGH' ? 'bg-amber-950 text-amber-400 border-amber-600/50' :
                      'bg-blue-950 text-blue-400 border-blue-600/40'
                    }`}>
                      {priority}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">{status}</span>
                  </div>
                  <button
                    onClick={() => onSelectCase(case_id)}
                    className="mt-2.5 w-full bg-[#161922] hover:bg-blue-600 hover:text-white border border-[#1E2430] text-slate-300 py-1 px-2 text-[11px] font-bold rounded transition-colors"
                  >
                    Select Case
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

