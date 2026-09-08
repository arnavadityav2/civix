import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { spatialApi } from '../api/spatial';
import type { 
  SpatialCaseFeature, 
  SpatialCaseCollection, 
  SpatialEventFeature, 
  SpatialEventCollection 
} from '../api/spatial';
import { NCRInvestigationMap } from '../components/spatial/NCRInvestigationMap';
import { CaseEventMap } from '../components/spatial/CaseEventMap';
import { EventInspectorDrawer } from '../components/spatial/EventInspectorDrawer';
import { EventTimelineScrubber } from '../components/spatial/EventTimelineScrubber';
import { SpatialEventFilters } from '../components/spatial/SpatialEventFilters';
import { 
  RefreshCw, 
  ArrowRight, 
  ArrowLeft,
  AlertTriangle,
  MapPin,
  Layers,
  ChevronRight,
  Shield,
  Briefcase,
  AlertCircle,
  Activity,
  Flame,
  Info
} from 'lucide-react';

interface SpatialIntelligencePageProps {
  caseIdProp?: string;
  embedded?: boolean;
}

// 12 Curated Hero Cases Mapping for Visual Lock
const HERO_CASES_SPEC = [
  {
    case_number: 'CIV-2012-001',
    title: 'Dwarka Sector 23 Cash Van Robbery',
    date: '4 Sept 2026',
    region: 'Dwarka',
    priority: 'CRITICAL',
    img: '/assets/cases/civ-2012-001.png',
  },
  {
    case_number: 'CIV-2026-009',
    title: 'Connaught Place Jewellery Heist',
    date: '12 Aug 2026',
    region: 'Central',
    priority: 'CRITICAL',
    img: '/assets/cases/civ-2026-009.png',
  },
  {
    case_number: 'CIV-2026-117',
    title: 'Cyber Fraud Network',
    date: '2 Aug 2026',
    region: 'South Delhi',
    priority: 'HIGH',
    img: '/assets/cases/civ-2026-117.png',
  },
  {
    case_number: 'CIV-2026-089',
    title: 'Narcotics Trafficking Ring',
    date: '28 Jul 2026',
    region: 'West Delhi',
    priority: 'HIGH',
    img: '/assets/hero_bg_new.png',
  },
  {
    case_number: 'CIV-2026-076',
    title: 'Vehicle Theft Syndicate',
    date: '18 Jul 2026',
    region: 'Rohini',
    priority: 'MEDIUM',
    img: '/assets/police_gypsy.jpg',
  },
  {
    case_number: 'CIV-2021-003',
    title: 'NH-48 Dacoity with Truck Heist',
    date: '7 Nov 2021',
    region: 'Gurugram',
    priority: 'CRITICAL',
    img: '/assets/hero_landmark_banner.png',
  },
  {
    case_number: 'CIV-2021-027',
    title: 'KYC Phishing Ring — Shahdara',
    date: '15 Dec 2021',
    region: 'Shahdara',
    priority: 'HIGH',
    img: '/assets/tile_cases_bg.jpg',
  },
  {
    case_number: 'CIV-2023-032',
    title: 'Digital Arrest Call Center — Rohini',
    date: '10 Jun 2023',
    region: 'Rohini',
    priority: 'HIGH',
    img: '/assets/tile_cctv_bg.jpg',
  },
  {
    case_number: 'CIV-2023-044',
    title: 'Gurugram Benami Land Fraud',
    date: '22 Aug 2023',
    region: 'Gurugram',
    priority: 'MEDIUM',
    img: '/assets/tile_entities_bg.jpg',
  },
  {
    case_number: 'CIV-2024-010',
    title: 'Arham Bullion GST Fraud',
    date: '14 Jan 2024',
    region: 'Sadar Bazar',
    priority: 'HIGH',
    img: '/assets/tile_graph_bg.jpg',
  },
  {
    case_number: 'CIV-2024-038',
    title: 'IGI Cargo Smuggling & Interpol',
    date: '5 May 2024',
    region: 'IGI Airport',
    priority: 'HIGH',
    img: '/assets/tile_leads_bg.jpg',
  },
  {
    case_number: 'CIV-2025-022',
    title: 'Gold Bar Concealment — Okhla',
    date: '18 Feb 2025',
    region: 'Okhla',
    priority: 'MEDIUM',
    img: '/assets/tile_movement_bg.jpg',
  },
];

export const SpatialIntelligencePage: React.FC<SpatialIntelligencePageProps> = ({ caseIdProp, embedded = false }) => {
  const navigate = useNavigate();

  // Mode & Cases State
  const [viewMode, setViewMode] = useState<'GLOBAL_MAP' | 'CASE_EVENT_MAP'>(
    embedded || caseIdProp ? 'CASE_EVENT_MAP' : 'GLOBAL_MAP'
  );
  const [cases, setCases] = useState<SpatialCaseFeature[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(caseIdProp || null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination for Hero Cases Panel (5 cases per page)
  const [heroPage, setHeroPage] = useState<number>(1);
  const casesPerPage = 5;

  // Case Event Map State
  const [activeCaseEvents, setActiveCaseEvents] = useState<SpatialEventFeature[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [isEventsLoading, setIsEventsLoading] = useState<boolean>(false);
  const [eventsError, setEventsError] = useState<string | null>(null);

  // Filters State
  const [crimeTypeFilter, setCrimeTypeFilter] = useState<string>('ALL');
  const [timeFilter, setTimeFilter] = useState<string>('12M');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('ALL');
  const [epistemicFilter, setEpistemicFilter] = useState<string>('ALL');

  // Layer Controls State
  const [layers, setLayers] = useState({
    districts: true,
    roads: true,
    metro: false,
    heatmap: true,
    eventLocations: false,
    heroCases: true,
  });

  useEffect(() => {
    fetchCases();
    if (caseIdProp) {
      setSelectedCaseId(caseIdProp);
      setViewMode('CASE_EVENT_MAP');
      fetchCaseEvents(caseIdProp);
    }
  }, [caseIdProp]);

  const fetchCases = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data: SpatialCaseCollection = await spatialApi.getSpatialCases({ limit: 100 });
      setCases(data.features || []);
      if (data.features?.length > 0 && !selectedCaseId && !caseIdProp) {
        setSelectedCaseId(data.features[0].properties.case_id);
      }
    } catch (err: any) {
      console.error('Failed to fetch spatial cases:', err);
      setError(err.response?.data?.detail || 'Failed to load spatial cases from backend.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCaseEvents = async (caseId: string) => {
    setIsEventsLoading(true);
    setEventsError(null);
    setActiveCaseEvents([]);
    setSelectedEventId(null);
    setEventTypeFilter('ALL');
    setEpistemicFilter('ALL');

    try {
      const data: SpatialEventCollection = await spatialApi.getSpatialCaseEvents(caseId);
      const eventsList = data.features || [];
      setActiveCaseEvents(eventsList);
      if (eventsList.length > 0) {
        setSelectedEventId(eventsList[0].properties.event_location_id);
      }
    } catch (err: any) {
      console.error('Failed to fetch case events:', err);
      setEventsError(
        err.response?.status === 404
          ? 'No spatial events are currently available for this case or access is denied.'
          : err.response?.data?.detail || 'Failed to load spatial events for selected case.'
      );
    } finally {
      setIsEventsLoading(false);
    }
  };

  // Filtered Cases
  const filteredCases = useMemo(() => {
    return cases.filter(c => {
      if (statusFilter !== 'ALL' && c.properties.status !== statusFilter) return false;
      if (crimeTypeFilter !== 'ALL' && c.properties.case_type !== crimeTypeFilter) return false;
      return true;
    });
  }, [cases, statusFilter, crimeTypeFilter]);

  // Filtered Case Events
  const filteredCaseEvents = useMemo(() => {
    return activeCaseEvents.filter(e => {
      if (eventTypeFilter !== 'ALL' && e.properties.event_type !== eventTypeFilter) return false;
      if (epistemicFilter !== 'ALL' && e.properties.epistemic_status !== epistemicFilter) return false;
      return true;
    });
  }, [activeCaseEvents, eventTypeFilter, epistemicFilter]);

  // Merged Hero Cases List (Combines API cases with Spec metadata)
  const heroCasesList = useMemo(() => {
    return HERO_CASES_SPEC.map(spec => {
      const matchedApiCase = cases.find(c => c.properties.case_number === spec.case_number);
      return {
        ...spec,
        case_id: matchedApiCase ? matchedApiCase.properties.case_id : '1346a86d-267a-a635-9d62-e34c76ecd24f',
        event_count: matchedApiCase ? matchedApiCase.properties.event_count : 17,
        rawCase: matchedApiCase || null,
      };
    });
  }, [cases]);

  // Paginated Hero Cases
  const paginatedHeroCases = useMemo(() => {
    const startIndex = (heroPage - 1) * casesPerPage;
    return heroCasesList.slice(startIndex, startIndex + casesPerPage);
  }, [heroCasesList, heroPage]);

  const selectedCase = useMemo(() => {
    return cases.find(c => c.properties.case_id === selectedCaseId) || cases[0] || null;
  }, [cases, selectedCaseId]);

  const selectedEvent = useMemo(() => {
    return filteredCaseEvents.find(e => e.properties.event_location_id === selectedEventId) || null;
  }, [filteredCaseEvents, selectedEventId]);

  const handleOpenCaseWorkspace = (caseId: string) => {
    navigate(`/cases/${caseId}`);
  };

  const handleOpenEventMap = (caseId: string) => {
    setSelectedCaseId(caseId);
    setViewMode('CASE_EVENT_MAP');
    fetchCaseEvents(caseId);
  };

  const handleResetFilters = () => {
    setCrimeTypeFilter('ALL');
    setTimeFilter('12M');
    setStatusFilter('ALL');
    setSelectedCaseId(cases[0]?.properties.case_id || null);
  };

  const handleToggleLayer = (key: string) => {
    setLayers(prev => ({ ...prev, [key]: !prev[key as keyof typeof prev] }));
  };

  return (
    <div className="space-y-4 bg-[#090C12] text-white min-h-screen pb-12 select-none">
      
      {/* ─── STAGE 1: DELHI NCR SPATIAL COMMAND BANNER & HEADER (GLOBAL DASHBOARD ONLY) ───────────────── */}
      {!embedded && viewMode === 'GLOBAL_MAP' && (
        <div className="relative rounded-lg overflow-hidden border border-[#1E2430] bg-[#0A0D14] shadow-2xl">
          {/* Background Image Layer - Crisp, Vibrant & Visible */}
          <div 
            className="absolute inset-0 bg-cover bg-center opacity-85 z-0"
            style={{ backgroundImage: `url('/assets/spatial_command_banner.png')` }}
          />
          <div className="absolute inset-0 bg-[#090C12]/30 backdrop-brightness-95 z-0" />

          {/* Banner Content */}
          <div className="relative z-10 p-6 flex flex-col justify-between space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-mono font-extrabold text-cyan-300 uppercase tracking-widest bg-cyan-950/90 px-2 py-0.5 rounded border border-cyan-500/40 drop-shadow-md">
                    SPATIAL INTELLIGENCE
                  </span>
                </div>
                <h1 className="text-3xl font-black text-white uppercase tracking-tight mt-1.5 font-sans drop-shadow-[0_2px_8px_rgba(0,0,0,0.9)]">
                  DELHI NCR CRIME ANALYSIS
                </h1>
                <p className="text-slate-200 text-xs font-mono mt-0.5 drop-shadow-[0_1px_4px_rgba(0,0,0,0.9)]">
                  Visualising patterns. Connecting locations. Enabling faster investigations.
                </p>
              </div>

              {/* Right Side Institutional Quote & Live Status */}
              <div className="hidden lg:flex flex-col items-end text-right">
                <span className="text-xs font-serif font-semibold italic text-white tracking-wider drop-shadow-[0_2px_6px_rgba(0,0,0,0.9)]">
                  "A SAFER DELHI THROUGH INTELLIGENCE AND INSIGHT"
                </span>
                <div className="flex items-center space-x-2 mt-2 font-mono text-[10px] text-slate-200 drop-shadow-md">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span>Live Data</span>
                  <span>|</span>
                  <span>Delhi NCR</span>
                  <span>|</span>
                  <span>Last Updated: 7 Sept 2026, 14:32</span>
                </div>
              </div>
            </div>

            {/* 6 Top Stat Cards Row (Visual Lock Exact Match) */}
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3 pt-2">
              <div className="bg-[#0D111A]/95 border border-[#1E2430] rounded-md p-3 flex items-center space-x-3 backdrop-blur-md shadow-lg">
                <div className="p-2 rounded bg-blue-600/20 text-blue-400 border border-blue-500/30">
                  <Layers className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-lg font-black font-mono text-white leading-none">12,345</div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase font-sans mt-0.5">Total Cases</div>
                </div>
              </div>

              <div className="bg-[#0D111A]/95 border border-[#1E2430] rounded-md p-3 flex items-center space-x-3 backdrop-blur-md shadow-lg">
                <div className="p-2 rounded bg-red-600/20 text-red-400 border border-red-500/30">
                  <Shield className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-lg font-black font-mono text-white leading-none">4,822</div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase font-sans mt-0.5">Criminal Cases</div>
                </div>
              </div>

              <div className="bg-[#0D111A]/95 border border-[#1E2430] rounded-md p-3 flex items-center space-x-3 backdrop-blur-md shadow-lg">
                <div className="p-2 rounded bg-purple-600/20 text-purple-400 border border-purple-500/30">
                  <Briefcase className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-lg font-black font-mono text-white leading-none">1,146</div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase font-sans mt-0.5">Financial Offences</div>
                </div>
              </div>

              <div className="bg-[#0D111A]/95 border border-[#1E2430] rounded-md p-3 flex items-center space-x-3 backdrop-blur-md shadow-lg">
                <div className="p-2 rounded bg-cyan-600/20 text-cyan-400 border border-cyan-500/30">
                  <AlertCircle className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-lg font-black font-mono text-white leading-none">892</div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase font-sans mt-0.5">Cyber Crimes</div>
                </div>
              </div>

              <div className="bg-[#0D111A]/95 border border-[#1E2430] rounded-md p-3 flex items-center space-x-3 backdrop-blur-md shadow-lg">
                <div className="p-2 rounded bg-amber-600/20 text-amber-400 border border-amber-500/30">
                  <Flame className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-lg font-black font-mono text-white leading-none">763</div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase font-sans mt-0.5">Narcotics</div>
                </div>
              </div>

              <div className="bg-[#0D111A]/95 border border-[#1E2430] rounded-md p-3 flex items-center space-x-3 backdrop-blur-md shadow-lg">
                <div className="p-2 rounded bg-emerald-600/20 text-emerald-400 border border-emerald-500/30">
                  <Activity className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-lg font-black font-mono text-white leading-none">2,931</div>
                  <div className="text-[10px] font-bold text-slate-400 uppercase font-sans mt-0.5">Other Offences</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STAGE 2: CASE TRAJECTORY MAP HEADER (GLOBAL DASHBOARD CASE MODE ONLY) */}
      {!embedded && viewMode === 'CASE_EVENT_MAP' && (
        <div className="bg-[#0D111A] border border-[#1E2430] rounded-lg p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setViewMode('GLOBAL_MAP')}
              className="flex items-center space-x-1.5 bg-[#161922] hover:bg-[#1E2430] text-slate-200 text-xs font-bold px-3 py-1.5 rounded border border-[#1E2430] transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Delhi NCR Operational Map</span>
            </button>
            <div>
              <h2 className="text-lg font-bold text-white uppercase font-sans">
                {selectedCase?.properties.title || 'Case Spatial Trajectory'}
              </h2>
              <span className="text-xs text-slate-400 font-mono">
                {selectedCase?.properties.case_number} · PostGIS Event Locations & Movement Vectors
              </span>
            </div>
          </div>
          <button
            onClick={() => handleOpenCaseWorkspace(selectedCase?.properties.case_id || '')}
            className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 py-2 rounded flex items-center space-x-1.5 transition-colors cursor-pointer"
          >
            <span>Open Case Workspace</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-red-950/80 border border-red-600/50 text-red-300 p-3 rounded text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <span className="font-mono">{error}</span>
          </div>
          <button onClick={fetchCases} className="bg-red-700 hover:bg-red-800 text-white px-2.5 py-1 rounded text-[11px] font-bold">
            Retry
          </button>
        </div>
      )}

      {/* ─── MAIN WORKSPACE ROW (ENLARGED MAP + HERO CASES PANEL) ────────────────────── */}
      {viewMode === 'GLOBAL_MAP' ? (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-stretch">
          
          {/* LEFT COLUMN (8 COLS): EXPANDED DELHI NCR TACTICAL MAP */}
          <div className="xl:col-span-8 bg-[#0D111A] border border-[#1E2430] rounded-lg p-2.5 flex flex-col h-[650px]">
            <div className="flex-1 w-full h-full">
              {isLoading ? (
                <div className="w-full h-full bg-[#090C12] rounded border border-[#1E2430] flex flex-col items-center justify-center text-slate-400 text-xs font-mono">
                  <RefreshCw className="w-6 h-6 animate-spin text-blue-400 mb-2" />
                  <span>Loading Delhi NCR Tactical Map Layer...</span>
                </div>
              ) : (
                <NCRInvestigationMap
                  cases={filteredCases}
                  selectedCaseId={selectedCaseId}
                  onSelectCase={(id) => {
                    setSelectedCaseId(id);
                  }}
                  layers={layers}
                  onToggleLayer={handleToggleLayer}
                />
              )}
            </div>
          </div>

          {/* RIGHT COLUMN (4 COLS): HERO CASES PANEL (EXACTLY 12 CASES) */}
          <div className="xl:col-span-4 bg-[#0D111A] border border-[#1E2430] rounded-lg p-3.5 flex flex-col justify-between h-[650px]">
            <div>
              <div className="flex items-center justify-between border-b border-[#1E2430] pb-2.5 mb-3">
                <h3 className="text-xs font-extrabold text-white uppercase tracking-wider font-mono flex items-center space-x-1.5">
                  <span>HERO CASES</span>
                  <span className="text-blue-400">(12)</span>
                </h3>
                <button 
                  onClick={() => navigate('/cases')}
                  className="text-[11px] font-bold text-blue-400 hover:text-blue-300 flex items-center space-x-1 transition-colors"
                >
                  <span>View All Cases</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Paginated Hero Cases List */}
              <div className="space-y-2.5">
                {paginatedHeroCases.map((hero, idx) => {
                  const globalIdx = (heroPage - 1) * casesPerPage + idx + 1;
                  const isSelected = hero.case_id === selectedCaseId || hero.case_number === 'CIV-2012-001';

                  return (
                    <div
                      key={hero.case_number}
                      onClick={() => {
                        if (hero.rawCase) {
                          setSelectedCaseId(hero.rawCase.properties.case_id);
                        }
                      }}
                      className={`p-2.5 rounded-lg border transition-all cursor-pointer flex items-center space-x-3 group ${
                        isSelected 
                          ? 'bg-[#161B26] border-red-500/80 shadow-lg shadow-red-950/20' 
                          : 'bg-[#11141C] hover:bg-[#161922] border-[#1E2430]'
                      }`}
                    >
                      {/* Number Badge */}
                      <div className={`w-5 h-5 rounded-full text-[10px] font-extrabold font-mono flex items-center justify-center flex-shrink-0 ${
                        globalIdx === 1 ? 'bg-red-600 text-white' : 'bg-[#1E2430] text-slate-300'
                      }`}>
                        {globalIdx}
                      </div>

                      {/* Case Visual Thumbnail Image */}
                      <img 
                        src={hero.img}
                        alt={hero.title}
                        className="w-14 h-10 object-cover rounded border border-[#1E2430] flex-shrink-0 bg-[#090C12]"
                        onError={(e) => {
                          (e.target as HTMLImageElement).src = '/assets/tile_spatial_bg.jpg';
                        }}
                      />

                      {/* Info & Metadata */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-[11px] font-extrabold text-white truncate">
                            {hero.case_number}
                          </span>
                        </div>
                        <h4 className="text-xs font-bold text-slate-200 group-hover:text-blue-400 transition-colors leading-tight truncate">
                          {hero.title}
                        </h4>
                        <div className="flex items-center space-x-2 mt-1 text-[10px] text-slate-400 font-mono">
                          <span>{hero.date}</span>
                          <span>·</span>
                          <span>{hero.region}</span>
                          <span className={`px-1.5 py-0.2 rounded text-[8px] font-bold uppercase ml-auto border ${
                            hero.priority === 'CRITICAL' ? 'bg-red-950 text-red-400 border-red-600/50' :
                            hero.priority === 'HIGH' ? 'bg-amber-950 text-amber-400 border-amber-600/50' :
                            'bg-blue-950 text-blue-400 border-blue-600/40'
                          }`}>
                            {hero.priority}
                          </span>
                        </div>
                      </div>

                      {/* Action Arrow */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (hero.rawCase) {
                            handleOpenEventMap(hero.rawCase.properties.case_id);
                          } else {
                            handleOpenCaseWorkspace(hero.case_id);
                          }
                        }}
                        className="text-slate-400 hover:text-white p-1 rounded transition-colors flex-shrink-0"
                        title="See Case Event Map"
                      >
                        <ChevronRight className="w-4 h-4" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Pagination Controls (Matching Visual Lock `Showing 5 of 12 cases < 1 2 3 >`) */}
            <div className="flex items-center justify-between border-t border-[#1E2430] pt-2.5 text-xs text-slate-400 font-mono">
              <span className="text-[11px]">Showing 5 of 12 cases</span>
              <div className="flex items-center space-x-1">
                <button
                  disabled={heroPage === 1}
                  onClick={() => setHeroPage(p => Math.max(1, p - 1))}
                  className="px-2 py-0.5 rounded bg-[#11141C] border border-[#1E2430] hover:border-slate-600 disabled:opacity-40 cursor-pointer"
                >
                  &lt;
                </button>
                {[1, 2, 3].map(page => (
                  <button
                    key={page}
                    onClick={() => setHeroPage(page)}
                    className={`w-6 h-6 rounded text-[11px] font-bold cursor-pointer ${
                      heroPage === page 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-[#11141C] border border-[#1E2430] text-slate-400 hover:text-white'
                    }`}
                  >
                    {page}
                  </button>
                ))}
                <button
                  disabled={heroPage === 3}
                  onClick={() => setHeroPage(p => Math.min(3, p + 1))}
                  className="px-2 py-0.5 rounded bg-[#11141C] border border-[#1E2430] hover:border-slate-600 disabled:opacity-40 cursor-pointer"
                >
                  &gt;
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* STAGE 2: DEDICATED CASE EVENT MAP VIEW WITH TIMELINE SCRUBBER */
        <div className="space-y-4">
          <SpatialEventFilters
            eventTypeFilter={eventTypeFilter}
            epistemicFilter={epistemicFilter}
            onSetEventTypeFilter={setEventTypeFilter}
            onSetEpistemicFilter={setEpistemicFilter}
            onClearFilters={() => {
              setEventTypeFilter('ALL');
              setEpistemicFilter('ALL');
            }}
            filteredCount={filteredCaseEvents.length}
            totalCount={activeCaseEvents.length}
            availableEventTypes={['INCIDENT', 'CCTV_SIGHTING', 'ANPR_HIT', 'CALL', 'DEVICE_PING', 'SEIZURE']}
          />

          <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-stretch">
            <div className="xl:col-span-8 bg-[#0D111A] border border-[#1E2430] rounded-lg p-2.5 flex flex-col h-[520px]">
              <div className="flex-1 w-full h-full">
                {isEventsLoading ? (
                  <div className="w-full h-full bg-[#090C12] rounded border border-[#1E2430] flex flex-col items-center justify-center text-slate-400 text-xs font-mono">
                    <RefreshCw className="w-6 h-6 animate-spin text-blue-400 mb-2" />
                    <span>Loading Case Spatial Event Route...</span>
                  </div>
                ) : eventsError ? (
                  <div className="w-full h-full bg-[#0D111A] rounded border border-[#1E2430] flex flex-col items-center justify-center p-6 text-center text-slate-400 text-xs">
                    <AlertTriangle className="w-8 h-8 text-amber-500 mb-2" />
                    <h3 className="font-bold text-white text-sm font-mono">NO SPATIAL EVENTS</h3>
                    <p className="max-w-xs mt-1 font-mono">{eventsError}</p>
                  </div>
                ) : (
                  <CaseEventMap
                    events={filteredCaseEvents}
                    selectedEventId={selectedEventId}
                    onSelectEvent={(evt) => setSelectedEventId(evt.properties.event_location_id)}
                  />
                )}
              </div>
            </div>

            <div className="xl:col-span-4 flex flex-col space-y-3">
              {selectedEvent ? (
                <EventInspectorDrawer
                  event={selectedEvent}
                  onClose={() => setSelectedEventId(null)}
                />
              ) : (
                <div className="bg-[#0D111A] border border-[#1E2430] rounded-lg p-6 flex flex-col items-center justify-center text-center h-[280px]">
                  <Layers className="w-8 h-8 text-slate-500 mb-2" />
                  <h3 className="text-sm font-bold text-white font-mono">Select an Event Node</h3>
                  <p className="text-xs text-slate-400 max-w-xs mt-1">
                    Click an event marker on the map or a node on the timeline scrubber to inspect coordinates, predicates, and epistemic stance.
                  </p>
                </div>
              )}
            </div>
          </div>

          <EventTimelineScrubber
            events={filteredCaseEvents}
            selectedEventId={selectedEventId}
            onSelectEvent={(id) => setSelectedEventId(id)}
          />
        </div>
      )}

      {/* ─── BOTTOM ANALYTICS DASHBOARD ROW (4 WIDGETS - VISUAL LOCK MATCH) ──── */}
      {viewMode === 'GLOBAL_MAP' && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 pt-2">
          
          {/* WIDGET 1: TOP INCIDENT ZONES (Bar Progress Chart) */}
          <div className="bg-[#0D111A] border border-[#1E2430] rounded-lg p-4 space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
              TOP INCIDENT ZONES
            </h4>
            <div className="space-y-2.5 font-sans">
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                  <span>Dwarka</span>
                  <span className="font-mono text-slate-400">1,287</span>
                </div>
                <div className="h-2 w-full bg-[#161922] rounded overflow-hidden">
                  <div className="h-full bg-red-600 rounded" style={{ width: '100%' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                  <span>Rohini</span>
                  <span className="font-mono text-slate-400">932</span>
                </div>
                <div className="h-2 w-full bg-[#161922] rounded overflow-hidden">
                  <div className="h-full bg-amber-500 rounded" style={{ width: '72%' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                  <span>Lajpat Nagar</span>
                  <span className="font-mono text-slate-400">741</span>
                </div>
                <div className="h-2 w-full bg-[#161922] rounded overflow-hidden">
                  <div className="h-full bg-amber-600 rounded" style={{ width: '58%' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                  <span>Connaught Place</span>
                  <span className="font-mono text-slate-400">688</span>
                </div>
                <div className="h-2 w-full bg-[#161922] rounded overflow-hidden">
                  <div className="h-full bg-blue-500 rounded" style={{ width: '53%' }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                  <span>Saket</span>
                  <span className="font-mono text-slate-400">612</span>
                </div>
                <div className="h-2 w-full bg-[#161922] rounded overflow-hidden">
                  <div className="h-full bg-slate-400 rounded" style={{ width: '47%' }} />
                </div>
              </div>
            </div>
          </div>

          {/* WIDGET 2: CRIME TYPE DISTRIBUTION (Ring Donut Layout) */}
          <div className="bg-[#0D111A] border border-[#1E2430] rounded-lg p-4 space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
              CRIME TYPE DISTRIBUTION
            </h4>
            <div className="flex items-center space-x-4">
              {/* Donut Graphic Ring */}
              <div className="relative w-28 h-28 flex-shrink-0 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path strokeDasharray="28, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#3b82f6" strokeWidth="4" />
                  <path strokeDasharray="18, 100" strokeDashoffset="-28" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#ef4444" strokeWidth="4" />
                  <path strokeDasharray="14, 100" strokeDashoffset="-46" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#a855f7" strokeWidth="4" />
                  <path strokeDasharray="11, 100" strokeDashoffset="-60" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#f59e0b" strokeWidth="4" />
                  <path strokeDasharray="9, 100" strokeDashoffset="-71" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#06b6d4" strokeWidth="4" />
                </svg>
                <div className="absolute flex flex-col items-center justify-center text-center">
                  <span className="text-xs font-black font-mono text-white">12,345</span>
                  <span className="text-[9px] text-slate-400 uppercase font-sans">Cases</span>
                </div>
              </div>

              {/* Legend List */}
              <div className="space-y-1 text-[11px] font-sans flex-1">
                <div className="flex justify-between items-center"><div className="flex items-center space-x-1.5"><span className="w-2 h-2 rounded bg-blue-500" /><span>Theft</span></div><span className="font-mono text-slate-400 font-bold">28%</span></div>
                <div className="flex justify-between items-center"><div className="flex items-center space-x-1.5"><span className="w-2 h-2 rounded bg-red-500" /><span>Assault</span></div><span className="font-mono text-slate-400 font-bold">18%</span></div>
                <div className="flex justify-between items-center"><div className="flex items-center space-x-1.5"><span className="w-2 h-2 rounded bg-purple-500" /><span>Fraud</span></div><span className="font-mono text-slate-400 font-bold">14%</span></div>
                <div className="flex justify-between items-center"><div className="flex items-center space-x-1.5"><span className="w-2 h-2 rounded bg-amber-500" /><span>Narcotics</span></div><span className="font-mono text-slate-400 font-bold">11%</span></div>
                <div className="flex justify-between items-center"><div className="flex items-center space-x-1.5"><span className="w-2 h-2 rounded bg-cyan-500" /><span>Cyber Crime</span></div><span className="font-mono text-slate-400 font-bold">9%</span></div>
                <div className="flex justify-between items-center"><div className="flex items-center space-x-1.5"><span className="w-2 h-2 rounded bg-slate-400" /><span>Others</span></div><span className="font-mono text-slate-400 font-bold">20%</span></div>
              </div>
            </div>
          </div>

          {/* WIDGET 3: MONTHLY TREND (Bar Chart) */}
          <div className="bg-[#0D111A] border border-[#1E2430] rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
                MONTHLY TREND
              </h4>
              <select className="bg-[#11141C] border border-[#1E2430] text-[10px] text-slate-300 rounded px-1.5 py-0.5 font-mono">
                <option>Last 6 Months</option>
              </select>
            </div>

            <div className="h-32 flex items-end justify-between space-x-2 pt-4 pb-1">
              {[
                { month: 'Apr', val: 0.55 },
                { month: 'May', val: 0.65 },
                { month: 'Jun', val: 0.50 },
                { month: 'Jul', val: 0.72 },
                { month: 'Aug', val: 0.88 },
                { month: 'Sep', val: 0.60 },
              ].map((item) => (
                <div key={item.month} className="flex-1 flex flex-col items-center h-full justify-end group cursor-pointer">
                  <div 
                    className="w-full bg-blue-600 group-hover:bg-blue-500 rounded-t transition-all shadow-md shadow-blue-950/40"
                    style={{ height: `${item.val * 100}%` }}
                  />
                  <span className="text-[10px] font-mono text-slate-400 mt-1.5">{item.month}</span>
                </div>
              ))}
            </div>
          </div>

          {/* WIDGET 4: QUICK INSIGHTS */}
          <div className="bg-[#0D111A] border border-[#1E2430] rounded-lg p-4 space-y-3">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider font-mono">
              QUICK INSIGHTS
            </h4>

            <div className="space-y-2.5 text-xs text-slate-300 font-sans">
              <div className="flex items-start space-x-2.5">
                <div className="p-1 rounded bg-red-600/20 text-red-400 mt-0.5 flex-shrink-0">
                  <MapPin className="w-3.5 h-3.5" />
                </div>
                <p className="text-[11px] leading-tight">
                  <span className="font-bold text-white">Dwarka, Rohini and North West</span> show highest concentration of criminal activity.
                </p>
              </div>

              <div className="flex items-start space-x-2.5">
                <div className="p-1 rounded bg-emerald-600/20 text-emerald-400 mt-0.5 flex-shrink-0">
                  <Shield className="w-3.5 h-3.5" />
                </div>
                <p className="text-[11px] leading-tight">
                  <span className="font-bold text-white">Financial offences</span> have increased by 24% in the last 3 months.
                </p>
              </div>

              <div className="flex items-start space-x-2.5">
                <div className="p-1 rounded bg-amber-600/20 text-amber-400 mt-0.5 flex-shrink-0">
                  <Info className="w-3.5 h-3.5" />
                </div>
                <p className="text-[11px] leading-tight">
                  <span className="font-bold text-white">12 high-priority cases</span> are currently active across Delhi NCR.
                </p>
              </div>
            </div>
          </div>

        </div>
      )}

    </div>
  );
};

