import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useCaseSelection } from '../context/CaseSelectionContext';
import { casesApi } from '../api/cases';
import type { CaseListItem } from '../types/api';
import { telecomApi } from '../api/telecom';
import type {
  TelecomEventItem,
  TelecomEntityItem,
  TelecomTower,
  TelecomSummaryResponse,
  TowerDumpItem,
  CoLocationResult,
  DeviceSimMatrixItem,
  BenchmarkCasePhone,
} from '../api/telecom';
import { TelecomMap } from '../components/telecom/TelecomMap';
import {
  DWARKA_SECTOR_23_TOWERS,
  DWARKA_SECTOR_23_EVENTS,
  DWARKA_SECTOR_23_ENTITIES,
  DWARKA_SECTOR_23_FINDINGS,
  DWARKA_SECTOR_23_SUSPECTS,
  getNetworkNodesForSuspect,
} from '../data/mockTelecomDataset';
import type { CaseSuspectProfile } from '../data/mockTelecomDataset';
import {
  Search,
  Calendar,
  Clock,
  Filter,
  ArrowRight,
  Smartphone,
  Radio as TowerIcon,
  Shield,
  Play,
  Layers,
  Activity,
  Globe,
  Phone,
  PhoneCall,
  PhoneOutgoing,
  Cpu,
  User,
  Car,
  CheckCircle2,
  MapPin,
  Maximize2,
  ChevronDown,
  Users,
  Zap,
} from 'lucide-react';

export const TelecomIntelligencePage: React.FC = () => {
  const navigate = useNavigate();
  const { caseId: routeCaseId } = useParams<{ caseId: string }>();
  const { selectedCaseId: contextCaseId, setSelectedCaseId } = useCaseSelection();

  // Active case ID fallback: route param -> context -> Flagship Case default CIV-2012-001
  const activeCaseId = routeCaseId || contextCaseId || 'CIV-2012-001';

  // Available Cases State
  const [availableCases, setAvailableCases] = useState<CaseListItem[]>([]);
  const [isCaseDropdownOpen, setIsCaseDropdownOpen] = useState(false);
  const [caseSearchQuery, setCaseSearchQuery] = useState('');

  // Suspect Selector State (Default: 'ALL_ACCUSED' or 'suresh')
  const [selectedSuspectId, setSelectedSuspectId] = useState<string>('suresh');

  // Handle click outside case dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (!(e.target as Element).closest('.case-dropdown-container')) {
        setIsCaseDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch available cases for dynamic switching
  useEffect(() => {
    const fetchCases = async () => {
      try {
        const [primaryCases, benchRes] = await Promise.all([
          casesApi.listCases(),
          telecomApi.getBenchmarkCases().catch(() => ({ cases: [] }))
        ]);

        const benchCases: CaseListItem[] = benchRes.cases.map(c => ({
          case_id: c.id,
          case_number: c.case_number,
          title: c.title,
          case_type: c.scenario_type,
          status: 'BENCHMARK',
          priority: c.severity,
          jurisdiction: 'SYNTHETIC'
        }));

        setAvailableCases([...primaryCases, ...benchCases]);
      } catch (err) {
        console.error('Failed to load cases', err);
      }
    };
    fetchCases();
  }, []);

  // ─── Module Navigation & Filters ──────────────────────────────────────────────
  const [activeModuleTab, setActiveModuleTab] = useState<'Communication' | 'Movement' | 'Co-location' | 'SIM_IMEI' | 'Spatial'>('Communication');

  // Filter Toolbar States
  const [dateFilter, setDateFilter] = useState<string>('2012-03-14');
  const [startTime, setStartTime] = useState<string>('02:00');
  const [endTime, setEndTime] = useState<string>('04:00');
  const [cdrFilter, setCdrFilter] = useState<'ALL' | 'INCOMING' | 'OUTGOING' | 'SMS' | 'DATA'>('ALL');
  const [tableSearchQuery, setTableSearchQuery] = useState<string>('');

  // Bottom Panel Tab State (Findings vs Connected Entities)
  const [bottomTab, setBottomTab] = useState<'FINDINGS' | 'ENTITIES'>('FINDINGS');

  // API Data States
  const [events, setEvents] = useState<TelecomEventItem[]>([]);
  const [totalEventsCount, setTotalEventsCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [_totalPages, setTotalPages] = useState<number>(1);

  const [towers, setTowers] = useState<TelecomTower[]>([]);
  const [_entities, setEntities] = useState<TelecomEntityItem[]>([]);

  // Tab-specific Data States
  const [_coLocPhoneA, setCoLocPhoneA] = useState<string>('');
  const [_coLocPhoneB, setCoLocPhoneB] = useState<string>('');
  const [_availableCoLocPhones, setAvailableCoLocPhones] = useState<BenchmarkCasePhone[]>([]);
  const [_coLocPhoneError, setCoLocPhoneError] = useState<string | null>(null);
  const [_isCoLocLoading, setIsCoLocLoading] = useState<boolean>(false);
  const [_coLocations, setCoLocations] = useState<CoLocationResult[]>([]);
  const [_coLocationTotal, setCoLocationTotal] = useState<number>(0);
  const [_towerDumpItems, setTowerDumpItems] = useState<TowerDumpItem[]>([]);
  const [_deviceSimMatrix, setDeviceSimMatrix] = useState<DeviceSimMatrixItem[]>([]);
  const [_coLocWindowSecs] = useState<number>(1800);
  const [_summaryMetrics, setSummaryMetrics] = useState<TelecomSummaryResponse | null>(null);

  // Selection States
  const [selectedEventId, setSelectedEventId] = useState<string | null>('f1353f6d-001');
  const [selectedTowerId, setSelectedTowerId] = useState<string | null>('TOWER-DW-01');

  // Loading & Error States
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Map Overlay Toggles
  const [mapOverlays, setMapOverlays] = useState({
    cellTowers: true,
    coverageArea: true,
    devicePings: true,
    movementPath: true,
    selectedTower: true,
    mapLabels: true,
  });

  const toggleOverlay = (key: keyof typeof mapOverlays) => {
    setMapOverlays((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Currently Selected Suspect Profile
  const activeSuspect: CaseSuspectProfile = useMemo(() => {
    return DWARKA_SECTOR_23_SUSPECTS.find((s) => s.id === selectedSuspectId) || DWARKA_SECTOR_23_SUSPECTS[1];
  }, [selectedSuspectId]);

  // Dynamic Network Nodes based on selected suspect
  const networkNodes = useMemo(() => {
    return getNetworkNodesForSuspect(selectedSuspectId);
  }, [selectedSuspectId]);

  // Clear tab-specific state when active case changes
  useEffect(() => {
    setCoLocations([]);
    setCoLocationTotal(0);
    setTowerDumpItems([]);
    setDeviceSimMatrix([]);
    setCoLocPhoneA('');
    setCoLocPhoneB('');
    setCoLocPhoneError(null);
    setAvailableCoLocPhones([]);
    setSelectedEventId('f1353f6d-001');
    setSelectedTowerId('TOWER-DW-01');
  }, [activeCaseId]);

  useEffect(() => {
    loadPageData();
  }, [activeCaseId, page, pageSize, cdrFilter, selectedSuspectId]);

  const loadPageData = async () => {
    setIsLoading(true);
    setError(null);

    // Front-end Demo Dataset for Dwarka Sector 23 Robbery (CIV-2012-001)
    if (activeCaseId === 'CIV-2012-001') {
      let baseEvents = DWARKA_SECTOR_23_EVENTS;

      // Filter events by selected suspect if a specific suspect is selected
      if (selectedSuspectId !== 'ALL_ACCUSED' && activeSuspect.phone) {
        const p = activeSuspect.phone;
        baseEvents = DWARKA_SECTOR_23_EVENTS.filter(
          (e) => e.caller_msisdn?.includes(p) || e.callee_msisdn?.includes(p) || e.subject_msisdn?.includes(p)
        );
      }

      // Apply CDR category filter (Incoming / Outgoing / SMS / Data)
      let filtered = baseEvents;
      if (cdrFilter === 'INCOMING') {
        filtered = baseEvents.filter(e => e.event_type === 'CALL' && !e.caller_msisdn?.includes(activeSuspect.phone || '9811092101'));
      } else if (cdrFilter === 'OUTGOING') {
        filtered = baseEvents.filter(e => e.event_type === 'CALL' && e.caller_msisdn?.includes(activeSuspect.phone || '9811092101'));
      } else if (cdrFilter === 'SMS') {
        filtered = baseEvents.filter(e => e.event_type === 'MESSAGE');
      } else if (cdrFilter === 'DATA') {
        filtered = baseEvents.filter(e => e.event_type === 'DEVICE_PING');
      }

      setEvents(filtered);
      setTotalEventsCount(baseEvents.length);
      setTotalPages(Math.ceil(filtered.length / pageSize) || 1);
      setTowers(DWARKA_SECTOR_23_TOWERS);
      setEntities(DWARKA_SECTOR_23_ENTITIES);

      if (filtered.length > 0 && !selectedEventId) {
        setSelectedEventId(filtered[0].event_id);
        setSelectedTowerId(filtered[0].location_id);
      }
      setIsLoading(false);
      return;
    }

    try {
      const eventsRes = await telecomApi.getCaseTelecomEvents(activeCaseId, {
        event_type: cdrFilter === 'ALL' ? undefined : (cdrFilter === 'SMS' ? 'MESSAGE' : (cdrFilter === 'DATA' ? 'DEVICE_PING' : 'CALL')),
        page,
        page_size: pageSize,
      });

      setEvents(eventsRes.items || []);
      setTotalEventsCount(eventsRes.pagination?.total || 0);
      setTotalPages(eventsRes.pagination?.total_pages || 1);

      if (eventsRes.items && eventsRes.items.length > 0 && !selectedEventId) {
        setSelectedEventId(eventsRes.items[0].event_id);
        if (eventsRes.items[0].location_id) {
          setSelectedTowerId(eventsRes.items[0].location_id);
        }
      }

      const towersRes = await telecomApi.getCaseTelecomTowers(activeCaseId);
      setTowers(towersRes.towers || []);

      const entitiesRes = await telecomApi.getCaseTelecomEntities(activeCaseId, { page_size: 50 });
      setEntities(entitiesRes.items || []);

      const summaryRes = await telecomApi.getTelecomSummary();
      setSummaryMetrics(summaryRes);

    } catch (err: any) {
      console.error('Failed to load telecom data:', err);
      setError(err.response?.data?.detail || 'Unable to connect to telecom intelligence backend service.');
    } finally {
      setIsLoading(false);
    }
  };

  // Run Analysis Button Handler
  const handleRunAnalysis = () => {
    setPage(1);
    loadPageData();
  };

  const handleTabChange = (tab: typeof activeModuleTab) => {
    setActiveModuleTab(tab);
  };

  // Helper formatting functions
  const formatTime = (isoString: string | null | undefined) => {
    if (!isoString) return '15:45:00';
    try {
      if (isoString.includes('T')) {
        return isoString.split('T')[1].slice(0, 8);
      }
      return isoString;
    } catch {
      return '15:45:00';
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (seconds === null || seconds === undefined) return '—';
    if (seconds === 0) return '00:00';
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const activeCaseTitle = activeCaseId === 'CIV-2012-001'
    ? 'Dwarka Sector 23 Cash Van Robbery'
    : availableCases.find(c => c.case_number === activeCaseId)?.title || `Case Investigation — ${activeCaseId}`;

  // Currently selected CDR event for bottom inspector card
  const selectedEvent = useMemo(() => {
    return DWARKA_SECTOR_23_EVENTS.find((e) => e.event_id === selectedEventId) || events[0] || DWARKA_SECTOR_23_EVENTS[0];
  }, [events, selectedEventId]);

  // Client-side search & category filtering on table events
  const filteredEvents = useMemo(() => {
    let list = events;
    if (!tableSearchQuery.trim()) return list;
    const q = tableSearchQuery.toLowerCase();
    return list.filter(
      (e) =>
        e.caller_msisdn?.toLowerCase().includes(q) ||
        e.callee_msisdn?.toLowerCase().includes(q) ||
        e.location_name?.toLowerCase().includes(q) ||
        e.event_type.toLowerCase().includes(q)
    );
  }, [events, tableSearchQuery]);

  // Category counts for CDR Records filter pills
  const counts = useMemo(() => {
    const all = events.length;
    const incoming = events.filter(e => e.event_type === 'CALL' && !e.caller_msisdn?.includes(activeSuspect.phone || '9811092101')).length;
    const outgoing = events.filter(e => e.event_type === 'CALL' && e.caller_msisdn?.includes(activeSuspect.phone || '9811092101')).length;
    const sms = events.filter(e => e.event_type === 'MESSAGE').length;
    const data = events.filter(e => e.event_type === 'DEVICE_PING').length;
    return { all, incoming, outgoing, sms, data };
  }, [events, activeSuspect]);

  return (
    <div className="min-h-screen bg-[#070A11] text-slate-100 flex flex-col font-sans select-none pb-6">

      {/* ─── TIER 1: CASE & TARGET CONTEXT HEADER ────────────────────────────────────────── */}
      <div className="w-full bg-[#090D16] border-b border-[#1A2333] px-6 py-3 shadow-md">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          
          {/* Left Context: Case Title & Target Person */}
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 rounded-lg bg-cyan-950/60 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-inner">
              <TowerIcon className="w-5 h-5" />
            </div>
            
            <div>
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-slate-400 font-mono">CASE: {activeCaseId}</span>
                <span className="bg-red-500/20 text-red-400 border border-red-500/40 text-[9px] font-black px-1.5 py-0.5 rounded tracking-wider uppercase font-mono">
                  CRITICAL
                </span>
                <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[9px] font-black px-1.5 py-0.5 rounded tracking-wider uppercase font-mono">
                  ACTIVE
                </span>
              </div>
              
              <h1 className="text-lg font-extrabold text-white tracking-tight flex items-center gap-2">
                <span>{activeCaseTitle}</span>
              </h1>
              
              <div className="flex items-center space-x-3 text-xs text-slate-400 mt-0.5">
                <span className="text-cyan-400 font-semibold">TELECOM INTELLIGENCE WORKSTATION</span>
                <span>•</span>
                <span className="text-slate-300">Target: <strong className="text-white font-mono">{activeSuspect.name} ({activeSuspect.phone})</strong></span>
                <span>•</span>
                <span>Dwarka PS, Delhi</span>
              </div>
            </div>
          </div>

          {/* Right Operational Metrics (4 Stats Cards) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-[#0D1322] border border-[#1E2B42] rounded-md px-3 py-2 flex items-center space-x-3">
              <div className="p-2 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Smartphone className="w-4 h-4" />
              </div>
              <div>
                <div className="text-base font-black text-white font-mono leading-none">{activeSuspect.callCount24h}</div>
                <div className="text-[10px] text-slate-400 uppercase font-semibold mt-0.5">CDR Events</div>
              </div>
            </div>

            <div className="bg-[#0D1322] border border-[#1E2B42] rounded-md px-3 py-2 flex items-center space-x-3">
              <div className="p-2 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <TowerIcon className="w-4 h-4" />
              </div>
              <div>
                <div className="text-base font-black text-white font-mono leading-none">1,037</div>
                <div className="text-[10px] text-slate-400 uppercase font-semibold mt-0.5">Towers Seen</div>
              </div>
            </div>

            <div className="bg-[#0D1322] border border-[#1E2B42] rounded-md px-3 py-2 flex items-center space-x-3">
              <div className="p-2 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20">
                <Phone className="w-4 h-4" />
              </div>
              <div>
                <div className="text-base font-black text-white font-mono leading-none">4</div>
                <div className="text-[10px] text-slate-400 uppercase font-semibold mt-0.5">Accused Devices</div>
              </div>
            </div>

            <div className="bg-[#0D1322] border border-[#1E2B42] rounded-md px-3 py-2 flex items-center space-x-3">
              <div className="p-2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Zap className="w-4 h-4" />
              </div>
              <div>
                <div className="text-base font-black text-white font-mono leading-none">{activeSuspect.interSuspectCallCount}</div>
                <div className="text-[10px] text-slate-400 uppercase font-semibold mt-0.5">Inter-Calls</div>
              </div>
            </div>
          </div>

        </div>
      </div>

      {/* ─── TIER 2: FIVE INVESTIGATIVE MODES TOOLBAR ───────────────────────────────────── */}
      <div className="px-6 py-2 bg-[#090D16] border-b border-[#1A2333] flex flex-wrap items-center justify-between gap-3 text-xs">
        
        {/* 5 Mode Buttons */}
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          {[
            { id: 'Communication', title: 'Communication', subtitle: 'Who talked to whom?', icon: PhoneCall },
            { id: 'Movement', title: 'Movement', subtitle: 'Where was the device?', icon: MapPin },
            { id: 'Co-location', title: 'Co-location', subtitle: 'Who was nearby?', icon: Activity },
            { id: 'SIM_IMEI', title: 'SIM / IMEI', subtitle: 'Device & SIM changes', icon: Cpu },
            { id: 'Spatial', title: 'Spatial Analysis', subtitle: 'Telecom + case geography', icon: Globe },
          ].map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeModuleTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id as any)}
                className={`px-3 py-2 rounded-md border flex items-center space-x-2.5 transition-all ${
                  isSelected
                    ? 'bg-cyan-950/70 border-cyan-500 text-cyan-300 shadow-md shadow-cyan-950/40'
                    : 'bg-[#0E1524] border-[#1E2B42] text-slate-400 hover:text-slate-200 hover:border-slate-600'
                }`}
              >
                <Icon className={`w-4 h-4 ${isSelected ? 'text-cyan-400' : 'text-slate-500'}`} />
                <div className="text-left">
                  <div className="font-bold text-xs leading-none">{tab.title}</div>
                  <div className="text-[9px] text-slate-400 mt-0.5 font-sans leading-none">{tab.subtitle}</div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Filter Controls Bar */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center bg-[#0E1524] border border-[#1E2B42] rounded px-2 py-1.5 text-slate-200">
            <Calendar className="w-3.5 h-3.5 text-slate-400 mr-1.5" />
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="bg-transparent border-none outline-none text-xs text-white cursor-pointer font-mono"
            />
          </div>

          <div className="flex items-center bg-[#0E1524] border border-[#1E2B42] rounded px-2 py-1.5 text-slate-200 gap-1">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="bg-transparent border-none outline-none text-xs text-white w-12 text-center font-mono"
            />
            <span className="text-slate-500">to</span>
            <input
              type="text"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="bg-transparent border-none outline-none text-xs text-white w-12 text-center font-mono"
            />
          </div>

          <button
            onClick={handleRunAnalysis}
            className="bg-cyan-600 hover:bg-cyan-500 text-white font-bold px-3 py-1.5 rounded flex items-center gap-1.5 shadow transition-all"
          >
            <Play className="w-3 h-3 fill-current" />
            <span>Run Analysis</span>
          </button>

          <button className="bg-[#0E1524] hover:bg-[#162035] text-slate-400 hover:text-slate-200 border border-[#1E2B42] px-2.5 py-1.5 rounded flex items-center gap-1 transition-all">
            <Filter className="w-3.5 h-3.5" />
            <span>More Filters</span>
          </button>
        </div>
      </div>

      {/* ─── TIER 3: MAIN UPPER WORKSPACE (2 COLUMNS: COMMUNICATION GRAPH + EXPANDED MAP) ──── */}
      <div className="px-6 py-4 grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* COLUMN 1: COMMUNICATION NETWORK & ACCUSED SELECTOR (~5.0 Cols) */}
        <div className="lg:col-span-5 bg-[#090D16] border border-[#1A2333] rounded-md p-3.5 shadow-xl flex flex-col justify-between">
          <div>
            {/* Header & Suspect Selector Dropdown */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1A2333] pb-2.5 mb-3 font-sans">
              <div className="flex items-center space-x-2">
                <PhoneCall className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  COMMUNICATION NETWORK
                </h3>
              </div>

              {/* ACCUSED / SUSPECT SELECTOR DROPDOWN */}
              <div className="relative">
                <select
                  value={selectedSuspectId}
                  onChange={(e) => setSelectedSuspectId(e.target.value)}
                  className="bg-[#0D1322] border border-cyan-500/50 text-cyan-300 font-bold text-xs px-2.5 py-1.5 rounded outline-none cursor-pointer focus:border-cyan-400 font-sans shadow"
                >
                  {DWARKA_SECTOR_23_SUSPECTS.map((s) => (
                    <option key={s.id} value={s.id} className="bg-[#090D16] text-white">
                      {s.name} ({s.phone})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Suspect Active Badge Info */}
            <div className="mb-2 px-3 py-2 rounded bg-[#0D1322] border border-[#1E2B42] flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-white font-sans">{activeSuspect.name}</span>
                <span className="text-[10px] text-slate-400 font-mono ml-2">{activeSuspect.phone}</span>
              </div>
              <span className={`text-[9px] font-black px-2 py-0.5 rounded tracking-wider ${activeSuspect.roleBadgeColor}`}>
                {activeSuspect.role}
              </span>
            </div>

            {/* SVG Radial Graph Visual Representation */}
            <div className="relative w-full h-[360px] bg-[#070A11] border border-[#141C2E] rounded-md overflow-hidden flex items-center justify-center">
              
              {/* Dynamic SVG Connecting Lines */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none">
                <line x1="50%" y1="50%" x2="22%" y2="20%" stroke="#EF4444" strokeWidth="2" strokeDasharray="3 3" opacity="0.85" />
                <line x1="50%" y1="50%" x2="78%" y2="20%" stroke="#EF4444" strokeWidth="2" strokeDasharray="3 3" opacity="0.85" />
                <line x1="50%" y1="50%" x2="82%" y2="55%" stroke="#3B82F6" strokeWidth="1.5" opacity="0.75" />
                <line x1="50%" y1="50%" x2="72%" y2="82%" stroke="#3B82F6" strokeWidth="1.5" opacity="0.75" />
                <line x1="50%" y1="50%" x2="28%" y2="80%" stroke="#3B82F6" strokeWidth="1.5" opacity="0.75" />
                <line x1="50%" y1="50%" x2="16%" y2="48%" stroke="#10B981" strokeWidth="2" opacity="0.9" />
              </svg>

              {/* Central Target Node (Selected Suspect) */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 flex flex-col items-center">
                <div className="relative w-16 h-16 rounded-full bg-gradient-to-br from-cyan-600 via-blue-700 to-indigo-900 border-2 border-cyan-400 shadow-xl shadow-cyan-950/80 flex items-center justify-center animate-pulse">
                  <User className="w-8 h-8 text-white" />
                </div>
                <div className="mt-1 bg-cyan-950/90 border border-cyan-500/60 rounded px-2.5 py-0.5 text-center shadow-md">
                  <div className="text-[11px] font-black text-white font-mono">{activeSuspect.name}</div>
                  <div className="text-[9px] text-cyan-300 font-mono">{activeSuspect.phone}</div>
                </div>
              </div>

              {/* Dynamic Surrounding Radial Nodes */}
              {networkNodes.map((node, idx) => {
                // Layout positions in ellipse
                const positions = [
                  { top: '18%', left: '22%' },
                  { top: '18%', left: '78%' },
                  { top: '55%', left: '84%' },
                  { top: '82%', left: '72%' },
                  { top: '80%', left: '28%' },
                  { top: '48%', left: '16%' },
                ];
                const pos = positions[idx % positions.length];

                return (
                  <div key={node.id} className="absolute z-10 flex flex-col items-center group cursor-pointer" style={{ top: pos.top, left: pos.left, transform: 'translate(-50%, -50%)' }}>
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center shadow transition-transform group-hover:scale-110 ${
                      node.type === 'PERSON'
                        ? 'bg-red-950 border border-red-400 text-red-300'
                        : node.type === 'VEHICLE'
                        ? 'bg-emerald-950 border border-emerald-400 text-emerald-300'
                        : node.type === 'DEVICE'
                        ? 'bg-purple-950 border border-purple-400 text-purple-300'
                        : 'bg-blue-950 border border-blue-400 text-blue-300'
                    }`}>
                      {node.type === 'VEHICLE' ? <Car className="w-4 h-4" /> : node.type === 'DEVICE' ? <Cpu className="w-4 h-4" /> : <User className="w-4 h-4" />}
                    </div>
                    <div className="text-center mt-1 bg-[#090D16]/95 px-2 py-0.5 rounded border border-[#1E2B42] max-w-[130px]">
                      <div className="text-[10px] font-bold text-white font-mono truncate">{node.label}</div>
                      {node.sublabel && <div className="text-[8px] text-cyan-400 font-mono truncate">{node.sublabel}</div>}
                    </div>
                  </div>
                );
              })}

            </div>
          </div>

          {/* Graph Legend Footer */}
          <div className="mt-2.5 pt-2 border-t border-[#1A2333] flex flex-wrap items-center justify-between text-[9px] text-slate-400 font-sans gap-x-2 gap-y-1">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"></span> Accused Person</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400"></span> Vehicle</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-purple-400"></span> Device</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400"></span> Number</span>
            <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-red-500"></span> High Call Surge</span>
            <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-blue-500"></span> Inter-Link</span>
          </div>

        </div>

        {/* COLUMN 2: CENTERED EXPANDED MOVEMENT MAP (~7.0 Cols) */}
        <div className="lg:col-span-7 bg-[#090D16] border border-[#1A2333] rounded-md p-3.5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1A2333] pb-2 mb-2 font-sans">
              <div className="flex items-center space-x-2">
                <MapPin className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  TOWER MOVEMENT MAP — {activeSuspect.name}
                </h3>
              </div>

              <div className="flex items-center space-x-2">
                <span className="text-[10px] text-cyan-400 bg-[#0E1524] border border-cyan-500/40 px-2 py-0.5 rounded font-mono font-bold">
                  5 Tower Handoffs Active
                </span>
                <button className="text-slate-400 hover:text-white">
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Leaflet Tower Map Container (Centered, Large Height) */}
            <div className="relative w-full h-[400px] rounded-md border border-[#1A2333] overflow-hidden">
              <TelecomMap
                towers={towers}
                events={events}
                selectedTowerId={selectedTowerId}
                selectedEventId={selectedEventId}
                onSelectTower={(tid) => setSelectedTowerId(tid)}
                overlayOptions={mapOverlays}
                onToggleOverlay={toggleOverlay}
              />

              {/* Map Overlay Controls Box Top Right */}
              <div className="absolute top-2 right-2 z-[400] bg-[#090D16]/90 backdrop-blur border border-[#1E2B42] rounded p-2 text-[10px] space-y-1">
                <label className="flex items-center gap-1.5 text-slate-300 cursor-pointer">
                  <input type="checkbox" checked={mapOverlays.cellTowers} onChange={() => toggleOverlay('cellTowers')} className="rounded accent-cyan-500" />
                  <span>Towers</span>
                </label>
                <label className="flex items-center gap-1.5 text-slate-300 cursor-pointer">
                  <input type="checkbox" checked={mapOverlays.devicePings} onChange={() => toggleOverlay('devicePings')} className="rounded accent-cyan-500" />
                  <span>Heatmap</span>
                </label>
                <label className="flex items-center gap-1.5 text-slate-300 cursor-pointer">
                  <input type="checkbox" checked={mapOverlays.coverageArea} onChange={() => toggleOverlay('coverageArea')} className="rounded accent-cyan-500" />
                  <span>Case Area</span>
                </label>
                <label className="flex items-center gap-1.5 text-slate-300 cursor-pointer">
                  <input type="checkbox" checked={mapOverlays.selectedTower} onChange={() => toggleOverlay('selectedTower')} className="rounded accent-cyan-500" />
                  <span>Satellite</span>
                </label>
              </div>

              {/* Scale Bar Bottom Left */}
              <div className="absolute bottom-2 left-2 z-[400] bg-[#090D16]/80 px-2 py-0.5 rounded border border-[#1E2B42] text-[9px] text-slate-400 font-mono">
                2 km
              </div>
            </div>
          </div>

          <div className="mt-2 text-[10px] text-slate-400 flex items-center justify-between border-t border-[#1A2333] pt-2 font-sans">
            <span className="font-mono text-cyan-300">
              Crime Path: TOWER-DW-01 (Vault) → DW-02 (Market) → DW-03 (Metro) → DW-04 (Safehouse) → DW-05 (Ring Road)
            </span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> Spatial Route Lock
            </span>
          </div>
        </div>

      </div>

      {/* ─── TIER 4: MIDDLE FULL-WIDTH TELECOM TIMELINE STRIP ────────────────────────────── */}
      <div className="px-6 py-2">
        <div className="bg-[#090D16] border border-[#1A2333] rounded-md p-3 shadow-xl">
          <div className="flex items-center justify-between border-b border-[#1A2333] pb-2 mb-2 font-sans">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                TELECOM TIMELINE · {events.length} EVENTS ({activeSuspect.name})
              </h3>
            </div>

            {/* Timeline Legend */}
            <div className="flex items-center space-x-4 text-[10px] text-slate-300">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500"></span> Incoming Call</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"></span> Outgoing Call</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-purple-400"></span> SMS</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400"></span> Data</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400"></span> SIM Change</span>
            </div>
          </div>

          {/* Scrubber Strip */}
          <div className="relative py-4 flex items-center px-4">
            <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-0.5 bg-[#1E2B42]" />
            
            <div className="w-full flex items-center justify-between relative z-10 font-mono text-[10px] text-slate-400">
              {['15:30', '15:45', '16:00', '16:15', '16:30', '16:48', '17:00', '17:15', '17:30'].map((tick, idx) => (
                <div key={idx} className="flex flex-col items-center">
                  <div className="w-1 h-2 bg-slate-600 mb-1" />
                  <span>{tick}</span>
                </div>
              ))}
            </div>

            {/* Interactive Event Dots Overlaid along timeline */}
            <div className="absolute inset-x-8 top-1/2 -translate-y-1/2 z-20 flex justify-between items-center pointer-events-none">
              {events.map((evt) => {
                const isSelected = evt.event_id === selectedEventId;
                const dotColor = evt.event_type === 'MESSAGE' 
                  ? 'bg-purple-400' 
                  : evt.event_type === 'DEVICE_PING' 
                  ? 'bg-emerald-400' 
                  : evt.caller_msisdn?.includes(activeSuspect.phone || '9811092101') 
                  ? 'bg-red-500' 
                  : 'bg-blue-500';

                return (
                  <button
                    key={evt.event_id}
                    onClick={() => {
                      setSelectedEventId(evt.event_id);
                      if (evt.location_id) setSelectedTowerId(evt.location_id);
                    }}
                    className={`pointer-events-auto w-3.5 h-3.5 rounded-full ${dotColor} transition-transform hover:scale-150 ${
                      isSelected ? 'ring-4 ring-cyan-400 scale-125' : 'opacity-80 hover:opacity-100'
                    }`}
                    title={`${formatTime(evt.start)} - ${evt.description}`}
                  />
                );
              })}
            </div>

          </div>
        </div>
      </div>

      {/* ─── TIER 5: BOTTOM WORKSPACE (CDR TABLE, EVENT DETAILS, FINDINGS & ENTITIES) ──── */}
      <div className="px-6 py-2 grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* BOTTOM LEFT: CDR RECORDS TABLE WITH QUICK FILTERS (~4.5 Cols) */}
        <div className="lg:col-span-5 bg-[#090D16] border border-[#1A2333] rounded-md p-3 shadow-xl flex flex-col justify-between">
          <div>
            {/* Header & Category Pills */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1A2333] pb-2 mb-2 font-sans">
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Smartphone className="w-3.5 h-3.5 text-cyan-400" />
                  CDR RECORDS ({events.length})
                </h3>
              </div>

              <div className="relative flex items-center">
                <Search className="w-3 h-3 absolute left-2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search records..."
                  value={tableSearchQuery}
                  onChange={(e) => setTableSearchQuery(e.target.value)}
                  className="bg-[#0E1524] border border-[#1E2B42] rounded text-slate-200 text-xs pl-7 pr-2 py-1 w-32 outline-none focus:border-cyan-500 font-sans"
                />
              </div>
            </div>

            {/* Quick Filter Category Pills */}
            <div className="flex items-center space-x-1 mb-2">
              <button
                onClick={() => setCdrFilter('ALL')}
                className={`px-2.5 py-1 rounded text-xs font-bold font-mono transition-colors ${
                  cdrFilter === 'ALL' ? 'bg-cyan-600 text-white' : 'bg-[#0E1524] text-slate-400 hover:text-white border border-[#1E2B42]'
                }`}
              >
                All {counts.all}
              </button>
              <button
                onClick={() => setCdrFilter('INCOMING')}
                className={`px-2 py-1 rounded text-xs font-bold font-mono transition-colors ${
                  cdrFilter === 'INCOMING' ? 'bg-blue-600 text-white' : 'bg-[#0E1524] text-slate-400 hover:text-white border border-[#1E2B42]'
                }`}
              >
                Incoming {counts.incoming}
              </button>
              <button
                onClick={() => setCdrFilter('OUTGOING')}
                className={`px-2 py-1 rounded text-xs font-bold font-mono transition-colors ${
                  cdrFilter === 'OUTGOING' ? 'bg-red-600 text-white' : 'bg-[#0E1524] text-slate-400 hover:text-white border border-[#1E2B42]'
                }`}
              >
                Outgoing {counts.outgoing}
              </button>
              <button
                onClick={() => setCdrFilter('SMS')}
                className={`px-2 py-1 rounded text-xs font-bold font-mono transition-colors ${
                  cdrFilter === 'SMS' ? 'bg-purple-600 text-white' : 'bg-[#0E1524] text-slate-400 hover:text-white border border-[#1E2B42]'
                }`}
              >
                SMS {counts.sms}
              </button>
              <button
                onClick={() => setCdrFilter('DATA')}
                className={`px-2 py-1 rounded text-xs font-bold font-mono transition-colors ${
                  cdrFilter === 'DATA' ? 'bg-emerald-600 text-white' : 'bg-[#0E1524] text-slate-400 hover:text-white border border-[#1E2B42]'
                }`}
              >
                Data {counts.data}
              </button>
            </div>

            {/* CDR Records Table */}
            <div className="overflow-x-auto overflow-y-auto max-h-[260px]">
              <table className="w-full text-left font-sans text-xs border-collapse">
                <thead>
                  <tr className="border-b border-[#1A2333] bg-[#070A11] text-slate-400 uppercase text-[9px] font-sans">
                    <th className="py-1.5 px-2 font-bold">#</th>
                    <th className="py-1.5 px-2 font-bold">TIME</th>
                    <th className="py-1.5 px-2 font-bold">TYPE</th>
                    <th className="py-1.5 px-2 font-bold">TOWER</th>
                    <th className="py-1.5 px-2 font-bold">SECTOR</th>
                    <th className="py-1.5 px-2 font-bold">DURATION</th>
                    <th className="py-1.5 px-2 font-bold">OTHER PARTY</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#121A2A]">
                  {filteredEvents.map((item, index) => {
                    const isSelected = item.event_id === selectedEventId;
                    const rowNum = index + 1;
                    const isOutgoing = item.caller_msisdn?.includes(activeSuspect.phone || '9811092101');
                    const otherParty = isOutgoing ? item.callee_msisdn : item.caller_msisdn;

                    return (
                      <tr
                        key={item.event_id}
                        onClick={() => {
                          setSelectedEventId(item.event_id);
                          if (item.location_id) setSelectedTowerId(item.location_id);
                        }}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-cyan-950/80 text-white font-bold border-l-2 border-cyan-400'
                            : 'hover:bg-[#0E1524] text-slate-300'
                        }`}
                      >
                        <td className="py-1.5 px-2 text-slate-500 font-mono text-[10px]">{rowNum}</td>
                        <td className="py-1.5 px-2 text-slate-200 font-bold font-mono text-[10px] whitespace-nowrap">
                          {formatTime(item.start)}
                        </td>
                        <td className="py-1.5 px-2 text-[10px]">
                          {item.event_type === 'MESSAGE' ? (
                            <span className="text-purple-400 font-medium">SMS</span>
                          ) : item.event_type === 'DEVICE_PING' ? (
                            <span className="text-emerald-400 font-medium">Data Ping</span>
                          ) : isOutgoing ? (
                            <span className="text-red-400 font-medium">Outgoing</span>
                          ) : (
                            <span className="text-blue-400 font-medium">Incoming</span>
                          )}
                        </td>
                        <td className="py-1.5 px-2 font-bold font-mono text-[10px] text-amber-400 whitespace-nowrap">
                          {item.location_id || 'TOWER-DW-01'}
                        </td>
                        <td className="py-1.5 px-2 text-slate-400 font-mono text-[10px]">S1</td>
                        <td className="py-1.5 px-2 text-slate-300 font-mono text-[10px]">
                          {formatDuration(item.duration_seconds)}
                        </td>
                        <td className="py-1.5 px-2 text-slate-300 font-mono text-[10px] whitespace-nowrap">
                          {otherParty || '—'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-[#1A2333] pt-2 mt-2 font-sans text-[10px] text-slate-400">
            <div>Showing 1–{filteredEvents.length} of {events.length} records</div>
            <div className="flex items-center space-x-1 font-mono">
              <button disabled className="px-1.5 py-0.5 rounded bg-[#0E1524] border border-[#1E2B42] opacity-40">&lt;</button>
              <span className="px-2 py-0.5 bg-cyan-600 text-white font-bold rounded">1</span>
              <button disabled className="px-1.5 py-0.5 rounded bg-[#0E1524] border border-[#1E2B42] opacity-40">&gt;</button>
            </div>
          </div>
        </div>

        {/* BOTTOM MIDDLE: EVENT DETAILS INSPECTOR (~4.0 Cols) */}
        <div className="lg:col-span-4 bg-[#090D16] border border-[#1A2333] rounded-md p-3 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1A2333] pb-2 mb-2 font-sans">
              <div className="flex items-center space-x-2">
                <Smartphone className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  EVENT DETAILS
                </h3>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">
                Event ID: <span className="text-slate-200 font-bold">{selectedEvent?.event_id ? selectedEvent.event_id.slice(0, 8) : 'f1353f6d'}</span>
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">
              {/* Event Inspector Fields */}
              <div className="md:col-span-7 space-y-2 text-xs">
                <div className="flex items-center space-x-2">
                  <div className="p-2 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-400">
                    <PhoneOutgoing className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-black text-white font-mono">
                      {formatTime(selectedEvent?.start)}
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-cyan-400 text-xs">
                        {selectedEvent?.caller_msisdn?.includes(activeSuspect.phone || '9811092101') ? 'Outgoing Call' : 'Incoming Call'}
                      </span>
                      <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[8px] font-bold px-1.5 py-0.2 rounded flex items-center gap-0.5">
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        Verified
                      </span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[11px] pt-1 border-t border-[#1A2333]">
                  <div>
                    <span className="text-[9px] text-slate-500 uppercase block font-sans">Target Number</span>
                    <span className="font-bold text-cyan-400 font-mono">{activeSuspect.phone}</span>
                  </div>
                  <div>
                    <span className="text-[9px] text-slate-500 uppercase block font-sans">Other Party</span>
                    <span className="font-bold text-white font-mono">{selectedEvent?.callee_msisdn || selectedEvent?.caller_msisdn || '+91 98710 23455'}</span>
                  </div>

                  <div>
                    <span className="text-[9px] text-slate-500 uppercase block font-sans">Tower</span>
                    <span className="font-bold text-amber-400 font-mono">{selectedEvent?.location_id || 'TOWER-DW-01'}</span>
                  </div>
                  <div>
                    <span className="text-[9px] text-slate-500 uppercase block font-sans">Sector</span>
                    <span className="font-bold text-slate-200 font-mono">S1</span>
                  </div>

                  <div>
                    <span className="text-[9px] text-slate-500 uppercase block font-sans">Duration</span>
                    <span className="font-bold text-slate-200 font-mono">{formatDuration(selectedEvent?.duration_seconds)}</span>
                  </div>
                  <div>
                    <span className="text-[9px] text-slate-500 uppercase block font-sans">Device</span>
                    <span className="font-mono text-purple-300 text-[10px] truncate block font-bold">IMEI: {activeSuspect.imei}</span>
                  </div>
                </div>
              </div>

              {/* Tower Image Thumbnail Right */}
              <div className="md:col-span-5 bg-[#0E1524] border border-[#1E2B42] rounded p-2 flex flex-col items-center justify-center text-center">
                <div className="w-full h-20 rounded bg-slate-800 overflow-hidden border border-slate-700 mb-1.5 relative">
                  <img
                    src="/assets/indian_telecom_tower.png"
                    alt="Cell Tower"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                  <div className="absolute bottom-1 left-1.5 text-[9px] font-bold text-white font-mono">
                    {selectedEvent?.location_id || 'TOWER-DW-01'}
                  </div>
                </div>
                <div className="text-[10px] font-bold text-slate-300 font-sans truncate w-full">Dwarka Sector 23</div>
                <button
                  onClick={() => navigate(`/cases/${activeCaseId}/spatial`)}
                  className="mt-1 text-[10px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-bold underline font-sans"
                >
                  <span>View Tower</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>

            </div>
          </div>
        </div>

        {/* BOTTOM RIGHT: CIVIX FINDINGS & CONNECTED ENTITIES (~3.5 Cols) */}
        <div className="lg:col-span-3 bg-[#090D16] border border-[#1A2333] rounded-md p-3 shadow-xl flex flex-col justify-between font-sans">
          <div>
            {/* Tab Header: Switch between Findings and Connected Entities */}
            <div className="flex items-center justify-between border-b border-[#1A2333] pb-2 mb-2">
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => setBottomTab('FINDINGS')}
                  className={`px-2 py-1 rounded text-xs font-bold transition-colors ${
                    bottomTab === 'FINDINGS' ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/50' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Findings ({DWARKA_SECTOR_23_FINDINGS.length})
                </button>
                <button
                  onClick={() => setBottomTab('ENTITIES')}
                  className={`px-2 py-1 rounded text-xs font-bold transition-colors ${
                    bottomTab === 'ENTITIES' ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/50' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Entities (5)
                </button>
              </div>

              <button
                onClick={() => navigate(`/cases/${activeCaseId}/graph`)}
                className="text-[10px] text-cyan-400 hover:underline font-bold"
              >
                Graph ↗
              </button>
            </div>

            {/* TAB CONTENT: FINDINGS */}
            {bottomTab === 'FINDINGS' && (
              <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1">
                {DWARKA_SECTOR_23_FINDINGS.map((finding) => (
                  <div key={finding.id} className="bg-[#0D1322] border border-[#1E2B42] rounded p-2 flex items-start justify-between gap-1.5 hover:border-cyan-500/40 transition-colors">
                    <div className="flex-1 space-y-0.5">
                      <div className="flex items-center space-x-1.5">
                        <span className={`text-[8px] font-black px-1 py-0.2 rounded tracking-wider ${finding.severityColor}`}>
                          {finding.severity}
                        </span>
                        <span className="text-[8px] text-cyan-400 font-mono font-bold">{finding.signalStrengthPct}% SIGNAL</span>
                      </div>

                      <h4 className="text-[11px] font-bold text-white font-sans">{finding.title}</h4>
                      <p className="text-[9px] text-slate-300 leading-tight font-sans">{finding.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* TAB CONTENT: CONNECTED ENTITIES */}
            {bottomTab === 'ENTITIES' && (
              <div className="space-y-1.5 max-h-[260px] overflow-y-auto pr-1">
                <div className="bg-[#0D1322] border border-[#1E2B42] rounded p-2 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-red-950 border border-red-500/40 flex items-center justify-center text-red-300">
                      <User className="w-3 h-3" />
                    </div>
                    <div>
                      <div className="text-[11px] font-bold text-white font-sans">{activeSuspect.name}</div>
                      <div className="text-[8px] text-slate-400">{activeSuspect.role}</div>
                    </div>
                  </div>
                  <button className="text-[9px] text-cyan-400 hover:underline font-bold font-mono">View →</button>
                </div>

                <div className="bg-[#0D1322] border border-[#1E2B42] rounded p-2 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-blue-950 border border-blue-500/40 flex items-center justify-center text-blue-300">
                      <Phone className="w-3 h-3" />
                    </div>
                    <div>
                      <div className="text-[11px] font-bold text-white font-mono">{activeSuspect.phone}</div>
                      <div className="text-[8px] text-slate-400">Suspect Number</div>
                    </div>
                  </div>
                  <button className="text-[9px] text-cyan-400 hover:underline font-bold font-mono">View →</button>
                </div>

                <div className="bg-[#0D1322] border border-[#1E2B42] rounded p-2 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-purple-950 border border-purple-500/40 flex items-center justify-center text-purple-300">
                      <Cpu className="w-3 h-3" />
                    </div>
                    <div>
                      <div className="text-[11px] font-bold text-purple-300 font-mono truncate w-24">IMEI: {activeSuspect?.imei ? activeSuspect.imei.slice(0, 8) : '35209900'}...</div>
                      <div className="text-[8px] text-slate-400">Device IMEI</div>
                    </div>
                  </div>
                  <button className="text-[9px] text-cyan-400 hover:underline font-bold font-mono">View →</button>
                </div>

                <div className="bg-[#0D1322] border border-[#1E2B42] rounded p-2 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-amber-950 border border-amber-500/40 flex items-center justify-center text-amber-300">
                      <TowerIcon className="w-3 h-3" />
                    </div>
                    <div>
                      <div className="text-[11px] font-bold text-amber-400 font-mono">TOWER-DW-01</div>
                      <div className="text-[8px] text-slate-400">Primary Scene Tower</div>
                    </div>
                  </div>
                  <button className="text-[9px] text-cyan-400 hover:underline font-bold font-mono">View Map →</button>
                </div>

                <div className="bg-[#0D1322] border border-[#1E2B42] rounded p-2 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-6 h-6 rounded-full bg-slate-800 border border-slate-600 flex items-center justify-center text-slate-300">
                      <Shield className="w-3 h-3" />
                    </div>
                    <div>
                      <div className="text-[11px] font-bold text-white font-mono">CIV-2012-001</div>
                      <div className="text-[8px] text-slate-400">Active Case</div>
                    </div>
                  </div>
                  <button className="text-[9px] text-cyan-400 hover:underline font-bold font-mono">View Case →</button>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>

    </div>
  );
};

export default TelecomIntelligencePage;
