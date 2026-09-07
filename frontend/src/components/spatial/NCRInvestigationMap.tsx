import React, { useEffect, useMemo, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet';
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

// Delhi Region Coordinates & Labels
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

// Multi-tier Dynamic Crime Heatmap Density Nodes (Overview -> Neighborhood -> Street level)
const MULTI_TIER_HEATMAP_NODES = [
  // Tier 1: Regional Macro Hotspots (Visible at Zoom < 11.5)
  { lat: 28.5921, lon: 77.0511, intensity: 1.0, baseRadius: 55, minZoom: 0, maxZoom: 20 }, // Dwarka
  { lat: 28.7324, lon: 77.1211, intensity: 0.95, baseRadius: 50, minZoom: 0, maxZoom: 20 }, // Rohini
  { lat: 28.6506, lon: 77.2300, intensity: 0.9, baseRadius: 45, minZoom: 0, maxZoom: 20 },  // Sadar Bazar / Central
  { lat: 28.6280, lon: 77.2400, intensity: 0.85, baseRadius: 42, minZoom: 0, maxZoom: 20 }, // Connaught Place
  { lat: 28.5300, lon: 77.2790, intensity: 0.8, baseRadius: 42, minZoom: 0, maxZoom: 20 },  // Lajpat Nagar / Saket
  { lat: 28.6732, lon: 77.2882, intensity: 0.75, baseRadius: 40, minZoom: 0, maxZoom: 20 }, // Shahdara
  { lat: 28.4595, lon: 77.0266, intensity: 0.7, baseRadius: 38, minZoom: 0, maxZoom: 20 },  // Gurugram
  { lat: 28.5562, lon: 77.1000, intensity: 0.65, baseRadius: 35, minZoom: 0, maxZoom: 20 }, // IGI Airport
  { lat: 28.6090, lon: 76.9855, intensity: 0.85, baseRadius: 40, minZoom: 0, maxZoom: 20 }, // Najafgarh
  { lat: 28.5800, lon: 77.3200, intensity: 0.75, baseRadius: 38, minZoom: 0, maxZoom: 20 }, // Noida Sector 18
  { lat: 28.6700, lon: 77.4200, intensity: 0.70, baseRadius: 35, minZoom: 0, maxZoom: 20 }, // Ghaziabad
  { lat: 28.4089, lon: 77.3178, intensity: 0.65, baseRadius: 35, minZoom: 0, maxZoom: 20 }, // Faridabad

  // Tier 2: Mid-Level Neighborhood Hotspots (Visible at Zoom >= 11)
  { lat: 28.5710, lon: 77.0650, intensity: 0.95, baseRadius: 32, minZoom: 11, maxZoom: 20 }, // Dwarka Sec 23 Cash Van Site
  { lat: 28.5860, lon: 77.0420, intensity: 0.88, baseRadius: 30, minZoom: 11, maxZoom: 20 }, // Dwarka Sec 10 Metro
  { lat: 28.5980, lon: 77.0250, intensity: 0.82, baseRadius: 28, minZoom: 11, maxZoom: 20 }, // Dwarka Sec 21 Terminal
  { lat: 28.7180, lon: 77.1120, intensity: 0.90, baseRadius: 30, minZoom: 11, maxZoom: 20 }, // Rohini Sec 7 Market
  { lat: 28.7450, lon: 77.1350, intensity: 0.85, baseRadius: 28, minZoom: 11, maxZoom: 20 }, // Rohini Sec 24 Hub
  { lat: 28.6330, lon: 77.2180, intensity: 0.92, baseRadius: 32, minZoom: 11, maxZoom: 20 }, // Connaught Place Outer Circle
  { lat: 28.6560, lon: 77.2280, intensity: 0.94, baseRadius: 34, minZoom: 11, maxZoom: 20 }, // Sadar Bazar Wholesale Market
  { lat: 28.6520, lon: 77.2340, intensity: 0.89, baseRadius: 30, minZoom: 11, maxZoom: 20 }, // Chandni Chowk Main Market
  { lat: 28.6510, lon: 77.1910, intensity: 0.87, baseRadius: 28, minZoom: 11, maxZoom: 20 }, // Karol Bagh Market
  { lat: 28.5690, lon: 77.2430, intensity: 0.86, baseRadius: 30, minZoom: 11, maxZoom: 20 }, // Lajpat Nagar Central Market
  { lat: 28.5280, lon: 77.2190, intensity: 0.88, baseRadius: 32, minZoom: 11, maxZoom: 20 }, // Saket District Centre
  { lat: 28.5530, lon: 77.2060, intensity: 0.80, baseRadius: 26, minZoom: 11, maxZoom: 20 }, // Hauz Khas Village
  { lat: 28.5350, lon: 77.2710, intensity: 0.84, baseRadius: 30, minZoom: 11, maxZoom: 20 }, // Okhla Industrial Area Ph 3
  { lat: 28.6290, lon: 77.0870, intensity: 0.86, baseRadius: 30, minZoom: 11, maxZoom: 20 }, // Janakpuri District Centre
  { lat: 28.6470, lon: 77.1210, intensity: 0.82, baseRadius: 28, minZoom: 11, maxZoom: 20 }, // Rajouri Garden Main Market
  { lat: 28.6970, lon: 77.1420, intensity: 0.80, baseRadius: 28, minZoom: 11, maxZoom: 20 }, // Pitampura TV Tower Circle
  { lat: 28.6310, lon: 77.2770, intensity: 0.85, baseRadius: 30, minZoom: 11, maxZoom: 20 }, // Laxmi Nagar Vikas Marg
  { lat: 28.4980, lon: 77.0900, intensity: 0.88, baseRadius: 30, minZoom: 11, maxZoom: 20 }, // Gurugram Cyber City Ph 2
  { lat: 28.5720, lon: 77.3540, intensity: 0.84, baseRadius: 28, minZoom: 11, maxZoom: 20 }, // Noida Sector 62 IT Park

  // Tier 3: Street / Micro Intersections (Visible at Zoom >= 13)
  { lat: 28.5685, lon: 77.0621, intensity: 0.98, baseRadius: 24, minZoom: 13, maxZoom: 20 }, // Sector 23 Robbery Intersection
  { lat: 28.5742, lon: 77.0688, intensity: 0.92, baseRadius: 22, minZoom: 13, maxZoom: 20 }, // Sector 23 Market Police Post
  { lat: 28.5875, lon: 77.0450, intensity: 0.89, baseRadius: 20, minZoom: 13, maxZoom: 20 }, // Sector 10 Metro Gate 2
  { lat: 28.7195, lon: 77.1085, intensity: 0.91, baseRadius: 22, minZoom: 13, maxZoom: 20 }, // Rohini Sector 7 Flyover
  { lat: 28.6345, lon: 77.2195, intensity: 0.95, baseRadius: 25, minZoom: 13, maxZoom: 20 }, // CP Inner Circle Radial 3
  { lat: 28.6580, lon: 77.2295, intensity: 0.96, baseRadius: 25, minZoom: 13, maxZoom: 20 }, // Sadar Bazar Spice Chowk
  { lat: 28.6535, lon: 77.2360, intensity: 0.90, baseRadius: 22, minZoom: 13, maxZoom: 20 }, // Town Hall Fountain Chowk
  { lat: 28.5705, lon: 77.2450, intensity: 0.88, baseRadius: 22, minZoom: 13, maxZoom: 20 }, // Lajpat Market Block B Alley
  { lat: 28.5295, lon: 77.2175, intensity: 0.90, baseRadius: 24, minZoom: 13, maxZoom: 20 }, // Select Citywalk Mall Road
  { lat: 28.5510, lon: 77.2540, intensity: 0.87, baseRadius: 20, minZoom: 13, maxZoom: 20 }, // Nehru Place Bus Terminal
  { lat: 28.5580, lon: 77.0920, intensity: 0.88, baseRadius: 22, minZoom: 13, maxZoom: 20 }, // IGI Cargo Gate 4
  { lat: 28.6305, lon: 77.0890, intensity: 0.88, baseRadius: 22, minZoom: 13, maxZoom: 20 }, // Janakpuri West Flyover
  { lat: 28.5010, lon: 77.0930, intensity: 0.92, baseRadius: 24, minZoom: 13, maxZoom: 20 }, // DLF Cyber Hub Ramp
];

const MapController: React.FC<{ 
  cases: SpatialCaseFeature[]; 
  selectedId: string | null;
  onZoomChange: (zoom: number) => void;
}> = ({ cases, selectedId, onZoomChange }) => {
  const map = useMap();

  useMapEvents({
    zoomend: () => {
      onZoomChange(map.getZoom());
    },
  });

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
        map.flyTo([lat, lon], 13.5, { duration: 1.2 });
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
  const [currentZoom, setCurrentZoom] = useState<number>(10.8);

  useEffect(() => {
    setActiveLayers(layers);
  }, [layers]);

  const handleCheckboxChange = (key: string) => {
    setActiveLayers(prev => ({ ...prev, [key]: !prev[key as keyof typeof prev] }));
    if (onToggleLayer) onToggleLayer(key);
  };

  // Filter & Compute Dynamic Heatmap Nodes based on Current Map Zoom Level
  const activeHeatmapNodes = useMemo(() => {
    const zoomFactor = Math.pow(1.24, Math.max(0, currentZoom - 10.5));
    
    return MULTI_TIER_HEATMAP_NODES
      .filter(node => currentZoom >= node.minZoom && currentZoom <= node.maxZoom)
      .map(node => {
        const radius = Math.round(node.baseRadius * zoomFactor);
        return {
          ...node,
          radius: Math.min(120, Math.max(16, radius)),
        };
      });
  }, [currentZoom]);

  return (
    <div className="w-full h-full min-h-[550px] relative rounded-md overflow-hidden border border-[#1E2430] bg-[#090C12] select-none">
      
      {/* Top Right Checkbox Layer Control Box */}
      <div className="absolute top-4 right-4 z-[1000] bg-[#0D111A]/95 backdrop-blur-md border border-[#1E2430] rounded-lg p-3.5 shadow-xl w-48 text-xs font-sans">
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
            <span className="text-xs font-semibold">Dynamic Heatmap</span>
          </label>
        </div>

        {/* Live Zoom Detail Level Indicator */}
        <div className="mt-3 pt-2 border-t border-[#1E2430] font-mono text-[10px] text-slate-400 flex items-center justify-between">
          <span>Zoom: {currentZoom.toFixed(1)}</span>
          <span className="text-cyan-400 font-extrabold uppercase">
            {currentZoom >= 13 ? 'Street Detail' : currentZoom >= 11 ? 'District Detail' : 'Regional View'}
          </span>
        </div>
      </div>

      {/* Bottom Left Case Density Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-[#0D111A]/95 backdrop-blur-md border border-[#1E2430] rounded-lg p-3 shadow-xl w-56 text-xs font-mono">
        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1.5 flex justify-between">
          <span>Crime Density</span>
          <span className="text-blue-400">{activeHeatmapNodes.length} Hotspots</span>
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
        {/* Esri World Dark Gray Base Tile Layer (Clean Tactical Dark, Free, Zero Watermark) */}
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

        <MapController 
          cases={cases} 
          selectedId={selectedCaseId} 
          onZoomChange={(z) => setCurrentZoom(z)} 
        />

        {/* Multi-Tier Dynamic Heatmap Density Glow Nodes Layer */}
        {activeLayers.heatmap && activeHeatmapNodes.map((node, idx) => (
          <Marker
            key={`heat-${node.lat}-${node.lon}-${idx}`}
            position={[node.lat, node.lon]}
            icon={L.divIcon({
              className: 'heat-glow-node',
              html: `<div style="
                width: ${node.radius * 2}px;
                height: ${node.radius * 2}px;
                background: radial-gradient(circle, rgba(239,68,68,${node.intensity * 0.9}) 0%, rgba(245,158,11,${node.intensity * 0.6}) 38%, rgba(6,182,212,0.25) 70%, transparent 100%);
                border-radius: 50%;
                filter: blur(${Math.max(3, Math.round(node.radius / 8))}px);
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
                font-size: ${currentZoom >= 12 ? '13px' : '11px'};
                font-weight: 800;
                font-family: monospace;
                letter-spacing: 0.12em;
                text-shadow: 0 0 6px rgba(0,0,0,0.95), 0 0 12px rgba(0,0,0,1), 0 0 20px #3b82f6;
                white-space: nowrap;
                pointer-events: none;
              ">${reg.name}</div>`,
              iconSize: [120, 20],
              iconAnchor: [60, 10]
            })}
          />
        ))}
      </MapContainer>
    </div>
  );
};



