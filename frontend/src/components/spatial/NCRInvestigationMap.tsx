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
  { name: 'NORTH', center: [28.75, 77.15] as [number, number] },
  { name: 'NORTH WEST', center: [28.72, 77.05] as [number, number] },
  { name: 'NORTH EAST', center: [28.70, 77.26] as [number, number] },
  { name: 'WEST', center: [28.65, 77.08] as [number, number] },
  { name: 'CENTRAL', center: [28.64, 77.21] as [number, number] },
  { name: 'EAST', center: [28.63, 77.30] as [number, number] },
  { name: 'SOUTH WEST', center: [28.56, 77.02] as [number, number] },
  { name: 'SOUTH', center: [28.52, 77.22] as [number, number] },
  { name: 'SOUTH EAST', center: [28.54, 77.28] as [number, number] },
  { name: 'NEW DELHI', center: [28.61, 77.20] as [number, number] },
];

// Rich Tactical Heatmap Density Nodes across Delhi NCR
const HEATMAP_NODES = [
  { lat: 28.5921, lon: 77.0511, intensity: 1.0, radius: 55 }, // Dwarka
  { lat: 28.7324, lon: 77.1211, intensity: 0.95, radius: 50 }, // Rohini
  { lat: 28.6506, lon: 77.2300, intensity: 0.9, radius: 45 },  // Central / Sadar Bazar
  { lat: 28.6280, lon: 77.2400, intensity: 0.85, radius: 42 }, // Connaught Place
  { lat: 28.5300, lon: 77.2790, intensity: 0.8, radius: 42 },  // Lajpat Nagar / Saket
  { lat: 28.6732, lon: 77.2882, intensity: 0.75, radius: 40 }, // Shahdara
  { lat: 28.4595, lon: 77.0266, intensity: 0.7, radius: 38 },  // Gurugram
  { lat: 28.5562, lon: 77.1000, intensity: 0.65, radius: 35 }, // IGI Airport
  { lat: 28.6090, lon: 76.9855, intensity: 0.85, radius: 40 }, // Najafgarh
  { lat: 28.5800, lon: 77.3200, intensity: 0.75, radius: 38 }, // Noida Sector 18
  { lat: 28.6700, lon: 77.4200, intensity: 0.70, radius: 35 }, // Ghaziabad
  { lat: 28.4089, lon: 77.3178, intensity: 0.65, radius: 35 }, // Faridabad
];

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
    heroCases: false,
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
    <div className="w-full h-full min-h-[550px] relative rounded-md overflow-hidden border border-[#1E2430] bg-[#090C12] select-none">
      
      {/* Top Right Checkbox Layer Control Box */}
      <div className="absolute top-4 right-4 z-[1000] bg-[#0D111A]/95 backdrop-blur-md border border-[#1E2430] rounded-lg p-3.5 shadow-xl w-44 text-xs font-sans">
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
              checked={activeLayers.heatmap}
              onChange={() => handleCheckboxChange('heatmap')}
              className="rounded bg-[#161922] border-[#1E2430] text-blue-500 focus:ring-0 w-3.5 h-3.5 cursor-pointer accent-blue-600"
            />
            <span className="text-xs font-semibold">Crime Heatmap</span>
          </label>
        </div>
      </div>

      {/* Bottom Left Case Density Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-[#0D111A]/95 backdrop-blur-md border border-[#1E2430] rounded-lg p-3 shadow-xl w-52 text-xs font-mono">
        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1.5">
          Crime Density
        </span>
        <div className="h-2.5 w-full rounded bg-gradient-to-r from-blue-600 via-yellow-500 to-red-600 mb-1" />
        <div className="flex justify-between text-[10px] text-slate-400 font-bold">
          <span>Low Intensity</span>
          <span>High Intensity</span>
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
        zoom={10.8}
        style={{ width: '100%', height: '100%', backgroundColor: '#090C12' }}
        scrollWheelZoom={true}
        zoomControl={true}
      >
        {/* Esri World Dark Gray Base Tile Layer (100% Free, Zero Watermark, Clean Tactical Dark) */}
        <TileLayer
          attribution='&copy; Esri, DeLorme, NAVTEQ &mdash; Map data &copy; OpenStreetMap'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          maxZoom={16}
        />

        {/* Esri World Dark Gray Reference Layer (Sharp Place Names, Cities, Neighborhood Labels Overlay) */}
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
          maxZoom={16}
        />

        <MapController cases={cases} selectedId={selectedCaseId} />

        {/* Heatmap Density Glow Nodes Layer across Delhi NCR */}
        {activeLayers.heatmap && HEATMAP_NODES.map((node, idx) => (
          <Marker
            key={`heat-${idx}`}
            position={[node.lat, node.lon]}
            icon={L.divIcon({
              className: 'heat-glow-node',
              html: `<div style="
                width: ${node.radius * 2}px;
                height: ${node.radius * 2}px;
                background: radial-gradient(circle, rgba(239,68,68,${node.intensity * 0.85}) 0%, rgba(245,158,11,${node.intensity * 0.55}) 40%, rgba(59,130,246,0.18) 75%, transparent 100%);
                border-radius: 50%;
                filter: blur(5px);
                pointer-events: none;
              "></div>`,
              iconSize: [node.radius * 2, node.radius * 2],
              iconAnchor: [node.radius, node.radius]
            })}
          />
        ))}

        {/* Delhi Regional District Overlay Labels */}
        {activeLayers.districts && DELHI_REGIONS.map((reg) => (
          <Marker
            key={reg.name}
            position={reg.center}
            icon={L.divIcon({
              className: 'delhi-region-label',
              html: `<div style="
                color: #e2e8f0;
                font-size: 11px;
                font-weight: 800;
                font-family: monospace;
                letter-spacing: 0.12em;
                text-shadow: 0 0 6px rgba(0,0,0,0.95), 0 0 12px rgba(0,0,0,1), 0 0 20px #3b82f6;
                white-space: nowrap;
                pointer-events: none;
              ">${reg.name}</div>`,
              iconSize: [100, 20],
              iconAnchor: [50, 10]
            })}
          />
        ))}
      </MapContainer>
    </div>
  );
};


