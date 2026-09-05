import React, { useEffect, useRef, useState, useMemo } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { 
  Radio, 
  Shield, 
  MapPin, 
  Phone, 
  X, 
  CheckCircle2, 
  Filter, 
  Maximize2,
  RefreshCw,
  Navigation
} from 'lucide-react';
import { 
  PoliceStations, 
  SYNTHETIC_PCR_UNITS, 
  getPcrUnitPosition
} from '../../data/syntheticPcrTelemetry';
import type { 
  PoliceStationData, 
  PcrUnit,
  PcrStatus
} from '../../data/syntheticPcrTelemetry';

interface FieldOperationsMapProps {
  className?: string;
}

// Marker Factory for Police Station (Red Pin Shield)
function createStationMarkerIcon(station: PoliceStationData, isSelected: boolean) {
  const size = isSelected ? 28 : 22;
  const html = `
    <div style="
      width: ${size}px;
      height: ${size}px;
      background: #090C12;
      border: 2px solid ${isSelected ? '#E6B325' : '#ef4444'};
      border-radius: 4px;
      box-shadow: ${isSelected ? '0 0 12px rgba(230, 179, 37, 0.8)' : '0 2px 8px rgba(0,0,0,0.6)'};
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: transform 0.2s ease;
    ">
      <svg width="${size - 8}" height="${size - 8}" viewBox="0 0 24 24" fill="none" stroke="${isSelected ? '#E6B325' : '#ef4444'}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
    </div>
  `;

  return L.divIcon({
    className: 'civix-station-marker',
    html,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  });
}

// Color map by PCR Status
const STATUS_COLORS: Record<PcrStatus, { bg: string; border: string; shadow: string }> = {
  'EN ROUTE': { bg: '#ef4444', border: '#fca5a5', shadow: 'rgba(239, 68, 68, 0.8)' },
  'ON SCENE': { bg: '#f59e0b', border: '#fde68a', shadow: 'rgba(245, 158, 11, 0.8)' },
  'PATROL': { bg: '#3b82f6', border: '#93c5fd', shadow: 'rgba(59, 130, 246, 0.7)' },
  'AVAILABLE': { bg: '#10b981', border: '#a7f3d0', shadow: 'rgba(16, 185, 129, 0.7)' },
  'RETURNING': { bg: '#64748b', border: '#cbd5e1', shadow: 'rgba(100, 116, 139, 0.5)' }
};

// Marker Factory for PCR Unit (Small Glowing Dot)
function createPcrMarkerIcon(unit: PcrUnit, isFocused: boolean) {
  const { bg, border, shadow } = STATUS_COLORS[unit.status] || STATUS_COLORS['PATROL'];
  const size = isFocused ? 14 : 10;

  const html = `
    <div style="
      width: ${size}px;
      height: ${size}px;
      background-color: ${bg};
      border: 1.5px solid ${border};
      border-radius: 50%;
      box-shadow: ${isFocused ? `0 0 14px 4px ${shadow}` : `0 0 8px ${shadow}`};
      cursor: pointer;
      transition: box-shadow 0.2s ease, transform 0.2s ease;
    "></div>
  `;

  return L.divIcon({
    className: `civix-pcr-marker-${unit.unit_id}`,
    html,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2]
  });
}

// Custom Map Controller & 60 FPS Movement Animation Engine
const MapAnimationEngine: React.FC<{
  filterMode: 'ALL' | 'PCR' | 'STATIONS';
  selectedStationId: string | null;
  selectedPcrId: string | null;
  onSelectPcr: (unit: PcrUnit) => void;
  onSelectStation: (station: PoliceStationData) => void;
}> = ({ filterMode, selectedStationId, selectedPcrId, onSelectPcr, onSelectStation }) => {
  const map = useMap();
  const stationMarkersRef = useRef<Map<string, L.Marker>>(new Map());
  const pcrMarkersRef = useRef<Map<string, L.Marker>>(new Map());
  const animationFrameRef = useRef<number | null>(null);

  // Invalidate map size on load
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 200);
    return () => clearTimeout(timer);
  }, [map]);

  // 1. Initialize Police Station Markers
  useEffect(() => {
    // Clear old station markers
    stationMarkersRef.current.forEach(m => m.remove());
    stationMarkersRef.current.clear();

    if (filterMode === 'PCR') return;

    PoliceStations.forEach((station) => {
      const isSelected = station.id === selectedStationId;
      const marker = L.marker([station.lat, station.lon], {
        icon: createStationMarkerIcon(station, isSelected),
        zIndexOffset: 500
      });

      // Bind click handler
      marker.on('click', () => {
        onSelectStation(station);
      });

      marker.addTo(map);
      stationMarkersRef.current.set(station.id, marker);
    });

    return () => {
      stationMarkersRef.current.forEach(m => m.remove());
      stationMarkersRef.current.clear();
    };
  }, [map, filterMode, selectedStationId, onSelectStation]);

  // 2. Initialize PCR Markers
  useEffect(() => {
    // Clear old PCR markers
    pcrMarkersRef.current.forEach(m => m.remove());
    pcrMarkersRef.current.clear();

    if (filterMode === 'STATIONS') return;

    const now = Date.now();

    SYNTHETIC_PCR_UNITS.forEach((unit) => {
      // If a station is selected, filter units assigned to that station if filter active
      if (selectedStationId && unit.assigned_station_id !== selectedStationId && filterMode !== 'ALL') {
        return;
      }

      const isFocused = unit.unit_id === selectedPcrId || unit.assigned_station_id === selectedStationId;
      const pos = getPcrUnitPosition(unit, now);

      const marker = L.marker([pos.lat, pos.lng], {
        icon: createPcrMarkerIcon(unit, isFocused),
        zIndexOffset: isFocused ? 1000 : 200
      });

      marker.on('click', () => {
        onSelectPcr(unit);
      });

      marker.addTo(map);
      pcrMarkersRef.current.set(unit.unit_id, marker);
    });

    return () => {
      pcrMarkersRef.current.forEach(m => m.remove());
      pcrMarkersRef.current.clear();
    };
  }, [map, filterMode, selectedStationId, selectedPcrId, onSelectPcr]);

  // 3. 60 FPS requestAnimationFrame Tick Engine (Direct Leaflet Marker Mutation)
  useEffect(() => {
    if (filterMode === 'STATIONS') return;

    const animate = () => {
      if (document.hidden) {
        // Pause animation when tab is inactive to save performance
        animationFrameRef.current = requestAnimationFrame(animate);
        return;
      }

      const now = Date.now();
      pcrMarkersRef.current.forEach((marker, unitId) => {
        const unit = SYNTHETIC_PCR_UNITS.find(u => u.unit_id === unitId);
        if (unit) {
          const pos = getPcrUnitPosition(unit, now);
          marker.setLatLng([pos.lat, pos.lng]);
        }
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [filterMode]);

  return null;
};


export const FieldOperationsMap: React.FC<FieldOperationsMapProps> = ({ className = '' }) => {
  const center: [number, number] = [28.6139, 77.2090]; // Delhi NCR Operational Center
  const [filterMode, setFilterMode] = useState<'ALL' | 'PCR' | 'STATIONS'>('ALL');
  const [selectedStation, setSelectedStation] = useState<PoliceStationData | null>(null);
  const [selectedPcr, setSelectedPcr] = useState<PcrUnit | null>(null);
  const [dispatchingUnit, setDispatchingUnit] = useState<PcrUnit | null>(null);

  // Compute live telemetry summary metrics from deterministic dataset
  const metrics = useMemo(() => {
    let activeResponses = 0;
    let patrolCount = 0;
    let availableCount = 0;

    SYNTHETIC_PCR_UNITS.forEach(u => {
      if (u.status === 'EN ROUTE' || u.status === 'ON SCENE') activeResponses++;
      else if (u.status === 'PATROL') patrolCount++;
      else if (u.status === 'AVAILABLE') availableCount++;
    });

    return {
      totalStations: PoliceStations.length,
      totalPcr: SYNTHETIC_PCR_UNITS.length,
      activeResponses,
      patrolCount,
      availableCount
    };
  }, []);

  // Compute assigned PCR breakdown for selected station
  const stationPcrBreakdown = useMemo(() => {
    if (!selectedStation) return null;
    const assigned = SYNTHETIC_PCR_UNITS.filter(u => u.assigned_station_id === selectedStation.id);
    const active = assigned.filter(u => u.status === 'EN ROUTE' || u.status === 'ON SCENE').length;
    const patrol = assigned.filter(u => u.status === 'PATROL').length;
    const available = assigned.filter(u => u.status === 'AVAILABLE').length;

    return { total: assigned.length, active, patrol, available, units: assigned };
  }, [selectedStation]);

  return (
    <div className={`w-full h-full min-h-[440px] relative rounded-xl border border-[#1E2430] bg-[#090C12] overflow-hidden shadow-2xl flex flex-col ${className}`}>
      
      {/* ── 1. MAP HEADER BAR ────────────────────────────────────────────────── */}
      <div className="bg-[#0D1017] border-b border-[#1E2430] px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 z-10 select-none">
        
        {/* Left Title & Telemetry Provenance */}
        <div className="flex items-center space-x-3">
          <div className="p-1.5 bg-red-600/20 border border-red-500/50 rounded-lg text-red-500 animate-pulse">
            <Radio className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-black text-white uppercase tracking-wider">
                FIELD OPERATIONS
              </h2>
              <span className="bg-red-950/80 text-red-400 border border-red-800/60 font-mono text-[9px] font-bold px-2 py-0.5 rounded tracking-wide">
                SYNTHETIC OPERATIONAL TELEMETRY
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono">
              Delhi NCR Tactical Response Map · Real-Time Sector Positions
            </p>
          </div>
        </div>

        {/* Center Live Metric Pills */}
        <div className="hidden md:flex items-center space-x-2.5 font-mono text-xs">
          <div className="bg-[#141824] border border-[#1E2430] px-2.5 py-1 rounded-md text-slate-300">
            <span className="text-slate-400 mr-1.5 font-sans text-[11px]">STATIONS:</span>
            <span className="font-bold text-white">{metrics.totalStations}</span>
          </div>

          <div className="bg-[#141824] border border-[#1E2430] px-2.5 py-1 rounded-md text-slate-300">
            <span className="text-slate-400 mr-1.5 font-sans text-[11px]">PCR UNITS:</span>
            <span className="font-bold text-[#E6B325]">{metrics.totalPcr}</span>
          </div>

          <div className="bg-[#141824] border border-[#1E2430] px-2.5 py-1 rounded-md text-slate-300">
            <span className="text-slate-400 mr-1.5 font-sans text-[11px]">ACTIVE RESPONSES:</span>
            <span className="font-bold text-red-400">{metrics.activeResponses}</span>
          </div>
        </div>

        {/* Right Filter Toolbar */}
        <div className="flex items-center space-x-1.5 bg-[#141824] border border-[#1E2430] p-1 rounded-lg">
          <button
            onClick={() => setFilterMode('ALL')}
            className={`px-2.5 py-1 rounded text-[11px] font-bold font-mono transition-colors ${
              filterMode === 'ALL' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            ALL
          </button>
          <button
            onClick={() => setFilterMode('PCR')}
            className={`px-2.5 py-1 rounded text-[11px] font-bold font-mono transition-colors ${
              filterMode === 'PCR' ? 'bg-red-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            PCR (108)
          </button>
          <button
            onClick={() => setFilterMode('STATIONS')}
            className={`px-2.5 py-1 rounded text-[11px] font-bold font-mono transition-colors ${
              filterMode === 'STATIONS' ? 'bg-amber-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            STATIONS (22)
          </button>
        </div>

      </div>

      {/* ── 2. LEAFLET MAP CONTAINER ─────────────────────────────────────────── */}
      <div className="flex-1 w-full relative z-0">
        <MapContainer
          center={center}
          zoom={10}
          style={{ width: '100%', height: '100%', minHeight: '380px', backgroundColor: '#07090E' }}
          scrollWheelZoom={true}
          zoomControl={true}
        >
          <TileLayer
            attribution='Tiles &copy; Esri &mdash; Dark Gray Canvas'
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          />

          <MapAnimationEngine
            filterMode={filterMode}
            selectedStationId={selectedStation?.id || null}
            selectedPcrId={selectedPcr?.unit_id || null}
            onSelectPcr={(unit) => {
              setSelectedPcr(unit);
              setSelectedStation(null);
            }}
            onSelectStation={(station) => {
              setSelectedStation(station);
              setSelectedPcr(null);
            }}
          />
        </MapContainer>

        {/* ── 3. FLOATING COMPACT PCR OPERATIONAL POPUP ───────────────────────── */}
        {selectedPcr && (
          <div className="absolute bottom-4 left-4 z-[1000] w-80 bg-[#0D1017]/95 backdrop-blur-md border border-[#1E2430] rounded-xl p-4 shadow-2xl font-sans text-xs text-white">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1E2430] pb-2 mb-3">
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-sm text-white font-mono">{selectedPcr.unit_id}</span>
                <span className={`px-2 py-0.5 rounded text-[9px] font-extrabold font-mono uppercase ${
                  selectedPcr.status === 'EN ROUTE' ? 'bg-red-950 text-red-400 border border-red-700/60' :
                  selectedPcr.status === 'ON SCENE' ? 'bg-amber-950 text-amber-400 border border-amber-700/60' :
                  selectedPcr.status === 'PATROL' ? 'bg-blue-950 text-blue-400 border border-blue-700/60' :
                  'bg-emerald-950 text-emerald-400 border border-emerald-700/60'
                }`}>
                  ● {selectedPcr.status}
                </span>
              </div>
              <button 
                onClick={() => setSelectedPcr(null)}
                className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800/60 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content Details */}
            <div className="space-y-2 font-mono text-[11px] mb-3">
              <div className="flex justify-between items-center bg-[#141824] p-1.5 rounded border border-[#1E2430]">
                <span className="text-slate-400">CALL ID:</span>
                <span className="font-bold text-[#E6B325]">{selectedPcr.call_id}</span>
              </div>

              <div className="flex justify-between items-center bg-[#141824] p-1.5 rounded border border-[#1E2430]">
                <span className="text-slate-400">CURRENT AREA:</span>
                <span className="font-semibold text-white">{selectedPcr.current_area}</span>
              </div>

              <div className="flex justify-between items-center bg-[#141824] p-1.5 rounded border border-[#1E2430]">
                <span className="text-slate-400">ASSIGNED STATION:</span>
                <span className="font-semibold text-blue-300">{selectedPcr.assigned_station_name}</span>
              </div>

              <div className="flex justify-between items-center bg-[#141824] p-1.5 rounded border border-[#1E2430]">
                <span className="text-slate-400">SPEED / PROVENANCE:</span>
                <span className="text-slate-300">{selectedPcr.speed_kmh} km/h · Synthetic</span>
              </div>
            </div>

            {/* Action */}
            <button
              onClick={() => setDispatchingUnit(selectedPcr)}
              className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-1.5 px-3 rounded-lg border border-red-500/60 shadow flex items-center justify-center space-x-2 transition-colors"
            >
              <Phone className="w-3.5 h-3.5" />
              <span>CALL UNIT (DEMO DISPATCH)</span>
            </button>
          </div>
        )}

        {/* ── 4. FLOATING COMPACT POLICE STATION POPUP ───────────────────────── */}
        {selectedStation && stationPcrBreakdown && (
          <div className="absolute bottom-4 left-4 z-[1000] w-80 bg-[#0D1017]/95 backdrop-blur-md border border-[#1E2430] rounded-xl p-4 shadow-2xl font-sans text-xs text-white">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1E2430] pb-2 mb-3">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-red-500" />
                <h3 className="font-extrabold text-sm text-white">{selectedStation.name}</h3>
              </div>
              <button 
                onClick={() => setSelectedStation(null)}
                className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800/60 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="text-[11px] text-slate-400 mb-2.5 font-mono">
              JURISDICTION: <span className="text-slate-200 font-bold">{selectedStation.district} ({selectedStation.zone})</span>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-2 gap-2 font-mono text-[11px] mb-3">
              <div className="bg-[#141824] p-2 rounded border border-[#1E2430] flex flex-col">
                <span className="text-[10px] text-slate-400">ASSIGNED PCR:</span>
                <span className="text-sm font-bold text-[#E6B325]">{stationPcrBreakdown.total} Units</span>
              </div>

              <div className="bg-[#141824] p-2 rounded border border-[#1E2430] flex flex-col">
                <span className="text-[10px] text-slate-400">ACTIVE RESPONSES:</span>
                <span className="text-sm font-bold text-red-400">{stationPcrBreakdown.active} Active</span>
              </div>

              <div className="bg-[#141824] p-2 rounded border border-[#1E2430] flex flex-col">
                <span className="text-[10px] text-slate-400">ON PATROL:</span>
                <span className="text-sm font-bold text-blue-400">{stationPcrBreakdown.patrol} Units</span>
              </div>

              <div className="bg-[#141824] p-2 rounded border border-[#1E2430] flex flex-col">
                <span className="text-[10px] text-slate-400">AVAILABLE:</span>
                <span className="text-sm font-bold text-emerald-400">{stationPcrBreakdown.available} Standby</span>
              </div>
            </div>

            {/* Assigned Units List Pill Preview */}
            <div className="bg-[#141824] p-2 rounded border border-[#1E2430] mb-3 max-h-24 overflow-y-auto space-y-1">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Assigned Fleet</div>
              {stationPcrBreakdown.units.map(u => (
                <div key={u.unit_id} className="flex justify-between items-center text-[10px] font-mono border-b border-[#1E2430]/40 pb-0.5">
                  <span className="text-white font-bold">{u.unit_id}</span>
                  <span className="text-slate-400">{u.current_area}</span>
                  <span className="text-amber-400 font-semibold">{u.status}</span>
                </div>
              ))}
            </div>

            <button
              onClick={() => {
                setFilterMode('ALL');
                // Focus camera on station area
              }}
              className="w-full bg-[#1A202C] hover:bg-slate-800 text-slate-200 font-bold py-1.5 px-3 rounded-lg border border-[#1E2430] flex items-center justify-center space-x-2 transition-colors text-xs"
            >
              <Navigation className="w-3.5 h-3.5 text-blue-400" />
              <span>EMPHASIZE STATION PCR FLEET</span>
            </button>
          </div>
        )}

      </div>

      {/* ── 5. TACTICAL DISPATCH DEMO MODAL ──────────────────────────────────── */}
      {dispatchingUnit && (
        <div className="fixed inset-0 z-[5000] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0D1017] border border-red-500/50 rounded-xl p-5 max-w-md w-full shadow-2xl text-white font-sans">
            <div className="flex items-start justify-between border-b border-[#1E2430] pb-3 mb-4">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 bg-red-600/30 text-red-400 rounded-lg border border-red-500/50 animate-pulse">
                  <Phone className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-extrabold text-sm text-white">TACTICAL DISPATCH CONNECTED</h3>
                  <div className="text-[10px] font-mono text-red-400">DEMO SIMULATION DISPATCH CHANNEL</div>
                </div>
              </div>
              <button 
                onClick={() => setDispatchingUnit(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2.5 font-mono text-xs bg-[#141824] p-3 rounded-lg border border-[#1E2430] mb-4">
              <div className="flex justify-between">
                <span className="text-slate-400">TARGET UNIT:</span>
                <span className="font-bold text-white">{dispatchingUnit.unit_id}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-slate-400">ASSIGNED STATION:</span>
                <span className="text-blue-300 font-semibold">{dispatchingUnit.assigned_station_name}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-slate-400">TACTICAL FREQUENCY:</span>
                <span className="text-[#E6B325] font-bold">412.85 MHz (Sector Encrypted)</span>
              </div>

              <div className="flex justify-between">
                <span className="text-slate-400">ACTIVE CALL ID:</span>
                <span className="text-slate-200">{dispatchingUnit.call_id}</span>
              </div>

              <div className="flex justify-between">
                <span className="text-slate-400">SECTOR LOCATION:</span>
                <span className="text-white font-semibold">{dispatchingUnit.current_area}</span>
              </div>
            </div>

            <div className="p-2.5 rounded bg-emerald-950/40 border border-emerald-800/50 text-[11px] text-emerald-300 flex items-center space-x-2 mb-4">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Voice radio channel open. Synthetic dispatch telemetry simulation active.</span>
            </div>

            <button
              onClick={() => setDispatchingUnit(null)}
              className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 rounded-lg transition-colors text-xs uppercase tracking-wider shadow"
            >
              DISCONNECT DISPATCH CHANNEL
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
