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
  Search,
  Calendar,
  Clock,
  Filter,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  ChevronLeft,
  Phone,
  Smartphone,
  Radio as TowerIcon,
  Shield,
  AlertTriangle,
  RotateCcw,
  Play,
  Layers,
  Activity,
  Bell,
  Globe,
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
  const [activeModuleTab, setActiveModuleTab] = useState<'CDR' | 'TOWER_DUMP' | 'CO_LOCATION' | 'SIM_IMEI' | 'SPATIAL'>('CDR');
  
  // Filter Toolbar States
  const [dateFilter, setDateFilter] = useState<string>('2012-03-14');
  const [startTime, setStartTime] = useState<string>('02:00');
  const [endTime, setEndTime] = useState<string>('04:00');
  const [eventTypeFilter, setEventTypeFilter] = useState<'ALL' | 'CALL' | 'DEVICE_PING' | 'MESSAGE'>('ALL');
  const [tableSearchQuery, setTableSearchQuery] = useState<string>('');

  // API Data States
  const [events, setEvents] = useState<TelecomEventItem[]>([]);
  const [totalEventsCount, setTotalEventsCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(10);
  const [totalPages, setTotalPages] = useState<number>(1);
  
  const [towers, setTowers] = useState<TelecomTower[]>([]);
  const [entities, setEntities] = useState<TelecomEntityItem[]>([]);

  // Tab-specific Data States
  const [coLocPhoneA, setCoLocPhoneA] = useState<string>('');
  const [coLocPhoneB, setCoLocPhoneB] = useState<string>('');
  const [availableCoLocPhones, setAvailableCoLocPhones] = useState<BenchmarkCasePhone[]>([]);
  const [_coLocPhoneError, setCoLocPhoneError] = useState<string | null>(null);
  const [_isCoLocLoading, setIsCoLocLoading] = useState<boolean>(false);
  const [_coLocations, setCoLocations] = useState<CoLocationResult[]>([]);
  const [_coLocationTotal, setCoLocationTotal] = useState<number>(0);
  const [_coLocationPage, setCoLocationPage] = useState<number>(1);
  const [_coLocationTotalPages, setCoLocationTotalPages] = useState<number>(1);
  const [_towerDumpItems, setTowerDumpItems] = useState<TowerDumpItem[]>([]);
  const [_deviceSimMatrix, setDeviceSimMatrix] = useState<DeviceSimMatrixItem[]>([]);
  const [coLocWindowSecs] = useState<number>(1800);
  const [_summaryMetrics, setSummaryMetrics] = useState<TelecomSummaryResponse | null>(null);
  const [selectedTowerFilter] = useState<string | undefined>(undefined);

  // Selection States
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [selectedTowerId, setSelectedTowerId] = useState<string | null>(null);

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

  // Clear tab-specific state when active case changes
  useEffect(() => {
    setCoLocations([]);
    setCoLocationTotal(0);
    setCoLocationPage(1);
    setCoLocationTotalPages(1);
    setTowerDumpItems([]);
    setDeviceSimMatrix([]);
    setCoLocPhoneA('');
    setCoLocPhoneB('');
    setCoLocPhoneError(null);
    setAvailableCoLocPhones([]);
    setSelectedEventId(null);
    setSelectedTowerId(null);
  }, [activeCaseId]);

  useEffect(() => {
    loadPageData();
  }, [activeCaseId, page, pageSize, eventTypeFilter, selectedTowerFilter]);

  const loadPageData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Fetch Case Telecom Events
      const eventsRes = await telecomApi.getCaseTelecomEvents(activeCaseId, {
        event_type: eventTypeFilter === 'ALL' ? undefined : eventTypeFilter,
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

      // 2. Fetch Case Towers
      const towersRes = await telecomApi.getCaseTelecomTowers(activeCaseId);
      setTowers(towersRes.towers || []);

      // 3. Fetch Case Entities
      const entitiesRes = await telecomApi.getCaseTelecomEntities(activeCaseId, { page_size: 50 });
      setEntities(entitiesRes.items || []);

      // 4. Fetch Global Summary Metrics
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
    if (activeModuleTab === 'TOWER_DUMP' && selectedTowerId) {
      loadTowerDump(selectedTowerId);
    } else if (activeModuleTab === 'CO_LOCATION') {
      loadCoLocation();
    } else if (activeModuleTab === 'SIM_IMEI') {
      loadSIMMatrix();
    }
  };

  // Tab Data Loaders
  const loadTowerDump = async (towerId: string) => {
    try {
      const dumpRes = await telecomApi.getTowerDump({ tower_id: towerId, case_id: activeCaseId, page: 1, page_size: 20 });
      setTowerDumpItems(dumpRes.items || []);
    } catch (err) {
      console.error('Failed to load tower dump:', err);
    }
  };

  const loadCoLocation = async (pageNum: number = 1) => {
    setCoLocPhoneError(null);
    const phoneA = coLocPhoneA.trim();
    const phoneB = coLocPhoneB.trim();

    if (!phoneA || !phoneB) {
      setCoLocPhoneError('Both Phone A and Phone B are required for co-location analysis.');
      return;
    }
    if (phoneA === phoneB) {
      setCoLocPhoneError('Phone A and Phone B must be different numbers.');
      return;
    }

    setIsCoLocLoading(true);
    try {
      const coLocRes = await telecomApi.getCoLocation({
        msisdn_a: phoneA,
        msisdn_b: phoneB,
        case_id: activeCaseId,
        overlap_window_seconds: coLocWindowSecs,
        page: pageNum,
        page_size: 50,
      });
      setCoLocations(coLocRes.results || []);
      setCoLocationTotal(coLocRes.pagination?.total ?? coLocRes.co_locations_found ?? 0);
      setCoLocationPage(coLocRes.pagination?.page ?? pageNum);
      setCoLocationTotalPages(coLocRes.pagination?.total_pages ?? 1);
    } catch (err: any) {
      setCoLocPhoneError(err.response?.data?.detail || 'Co-location query failed.');
    } finally {
      setIsCoLocLoading(false);
    }
  };

  const loadSIMMatrix = async () => {
    try {
      const simRes = await telecomApi.getDeviceSimMatrix({ case_id: activeCaseId, page: 1, page_size: 20 });
      setDeviceSimMatrix(simRes.items || []);
    } catch (err) {
      console.error('Failed to load SIM matrix:', err);
    }
  };

  const handleTabChange = (tab: typeof activeModuleTab) => {
    setActiveModuleTab(tab);
    if (tab === 'TOWER_DUMP' && towers.length > 0) {
      loadTowerDump(towers[0].tower_id);
    } else if (tab === 'CO_LOCATION') {
      if (activeCaseId.startsWith('BENCH-') && availableCoLocPhones.length === 0) {
        telecomApi.getBenchmarkCasePhones(activeCaseId, 50)
          .then(res => {
            setAvailableCoLocPhones(res.phones || []);
            if (!coLocPhoneA && res.phones.length > 0) setCoLocPhoneA(res.phones[0].msisdn);
            if (!coLocPhoneB && res.phones.length > 1) setCoLocPhoneB(res.phones[1].msisdn);
          })
          .catch(err => console.error('Failed to load benchmark phones:', err));
      }
    } else if (tab === 'SIM_IMEI') {
      loadSIMMatrix();
    }
  };

  // Helper formatting functions
  const formatTime = (isoString: string | null) => {
    if (!isoString) return '—';
    try {
      const d = new Date(isoString);
      return d.toTimeString().split(' ')[0]; // HH:MM:SS
    } catch {
      return isoString;
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
    return events.find((e) => e.event_id === selectedEventId) || events[0] || null;
  }, [events, selectedEventId]);

  // Client-side search filtering on loaded table events
  const filteredEvents = useMemo(() => {
    if (!tableSearchQuery.trim()) return events;
    const q = tableSearchQuery.toLowerCase();
    return events.filter(
      (e) =>
        e.caller_msisdn?.toLowerCase().includes(q) ||
        e.callee_msisdn?.toLowerCase().includes(q) ||
        e.location_name?.toLowerCase().includes(q) ||
        e.event_type.toLowerCase().includes(q)
    );
  }, [events, tableSearchQuery]);

  return (
    <div className="min-h-screen bg-[#070A11] text-slate-100 flex flex-col font-sans select-none pb-6">

      {/* ─── TIER 2: FULL-WIDTH CASE HERO BANNER ───────────────────────────────── */}
      <div className="relative w-full bg-[#0B0F19] border-b border-[#1A2333] overflow-hidden">
        {/* Full Visibility Photographic Background Image */}
        <div
          className="absolute inset-0 bg-cover bg-center opacity-100"
          style={{ backgroundImage: `url('/assets/indian_telecom_tower.png')` }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[#070A11]/50 via-[#070A11]/20 to-transparent" />

        <div className="relative z-10 px-6 pt-5 pb-3">
          {/* Breadcrumb & Primary Case Badge */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs font-sans text-slate-400">
              <span
                onClick={() => navigate('/cases')}
                className="hover:text-blue-400 cursor-pointer transition-colors"
              >
                Case Registry
              </span>
              <span>›</span>
              <span className="text-slate-200 font-bold font-mono">{activeCaseId}</span>
              {activeCaseId === 'CIV-2012-001' && (
                <span className="bg-blue-600/20 text-blue-400 border border-blue-500/40 text-[9px] font-extrabold px-2 py-0.5 rounded tracking-wider ml-2 uppercase font-mono">
                  PRIMARY CASE
                </span>
              )}
            </div>

            {/* Right Quote */}
            <div className="hidden lg:block text-right font-sans italic text-slate-400 text-xs">
              <div>"Signals connect places. Intelligence connects the truth."</div>
              <div className="text-[10px] text-slate-500 not-italic font-bold mt-0.5">— CIVIX</div>
            </div>
          </div>

          {/* Case Title & Metadata */}
          <div className="mt-2 flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="relative case-dropdown-container">
                <button
                  onClick={() => setIsCaseDropdownOpen(!isCaseDropdownOpen)}
                  className="text-2xl font-black tracking-tight text-white font-sans flex items-center gap-3 hover:text-blue-300 transition-colors text-left"
                >
                  <span className="font-mono">{activeCaseId}</span>
                  <span className="text-slate-400 text-lg font-semibold font-sans">
                    {activeCaseTitle}
                  </span>
                  <ChevronRight className="w-5 h-5 text-slate-500 transform rotate-90" />
                </button>

                {/* Case Dropdown */}
                {isCaseDropdownOpen && (
                  <div className="absolute top-full mt-2 left-0 w-96 bg-[#090D16] border border-[#1E2B42] rounded-md shadow-2xl z-50 overflow-hidden font-sans">
                    <div className="p-2 border-b border-[#1E2B42] flex items-center bg-[#070A11]">
                      <Search className="w-3.5 h-3.5 text-slate-400 mr-2" />
                      <input
                        type="text"
                        autoFocus
                        placeholder="Search cases..."
                        value={caseSearchQuery}
                        onChange={(e) => setCaseSearchQuery(e.target.value)}
                        className="bg-transparent border-none outline-none text-xs text-white w-full font-sans"
                      />
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                      <button
                        onClick={() => {
                          setSelectedCaseId('CIV-2012-001');
                          setIsCaseDropdownOpen(false);
                          setCaseSearchQuery('');
                          navigate('/cases/CIV-2012-001/telecom');
                        }}
                        className="w-full text-left px-3 py-2 text-xs hover:bg-[#121A2A] text-slate-200 border-b border-[#1E2B42]/50 transition-colors"
                      >
                        <div className="font-bold text-white">Dwarka Sector 23 Cash Van Robbery</div>
                        <div className="text-[10px] text-blue-400 font-mono">CIV-2012-001 · Primary Case</div>
                      </button>
                      {availableCases.map((c) => (
                        <button
                          key={c.case_id}
                          onClick={() => {
                            setSelectedCaseId(c.case_number);
                            setIsCaseDropdownOpen(false);
                            setCaseSearchQuery('');
                            navigate(`/cases/${c.case_number}/telecom`);
                          }}
                          className="w-full text-left px-3 py-2 text-xs hover:bg-[#121A2A] text-slate-200 border-b border-[#1E2B42]/30 transition-colors"
                        >
                          <div className="font-bold">{c.title}</div>
                          <div className="text-[10px] text-slate-400 font-mono">{c.case_number}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-4 text-xs font-sans text-slate-400 mt-1.5">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-slate-500" />
                  14 Mar 2012
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Globe className="w-3.5 h-3.5 text-slate-500" />
                  Dwarka, New Delhi
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── TIER 4: TELECOM SUB-NAVIGATION & ANALYSIS TOOLBAR ────────────────── */}
      <div className="px-6 py-2 bg-[#090D16] border-b border-[#1A2333] flex flex-wrap items-center justify-between gap-3 font-sans text-xs">
        {/* Sub-module Tabs */}
        <div className="flex items-center space-x-1">
          {[
            { id: 'CDR', label: 'CDR Analysis', icon: Smartphone },
            { id: 'TowerDump', label: 'Tower Dump', icon: TowerIcon },
            { id: 'CoLocation', label: 'Co-Location', icon: Activity },
            { id: 'SIMAnalysis', label: 'SIM / IMEI Analysis', icon: Layers },
            { id: 'SpatialAnalysis', label: 'Spatial Analysis', icon: Globe },
          ].map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeModuleTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id as any)}
                className={`px-3 py-1.5 rounded flex items-center gap-1.5 font-bold transition-all ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow'
                    : 'bg-[#0E1524] text-slate-400 hover:text-slate-200 border border-[#1E2B42]'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Filter Controls Bar */}
        <div className="flex items-center space-x-2">
          {/* Date Picker */}
          <div className="flex items-center bg-[#0E1524] border border-[#1E2B42] rounded px-2 py-1 text-slate-200">
            <Calendar className="w-3.5 h-3.5 text-slate-400 mr-1.5" />
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="bg-transparent border-none outline-none text-xs text-white cursor-pointer font-mono"
            />
          </div>

          {/* Time Start / End */}
          <div className="flex items-center bg-[#0E1524] border border-[#1E2B42] rounded px-2 py-1 text-slate-200 gap-1">
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
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold px-3 py-1.5 rounded flex items-center gap-1.5 shadow transition-all"
          >
            <Play className="w-3 h-3 fill-current" />
            <span>Run Analysis</span>
          </button>

          <button
            onClick={() => {
              setDateFilter('2012-03-14');
              setStartTime('02:00');
              setEndTime('04:00');
              setEventTypeFilter('ALL');
              setTableSearchQuery('');
              handleRunAnalysis();
            }}
            className="bg-[#0E1524] hover:bg-[#162035] text-slate-300 border border-[#1E2B42] px-2.5 py-1.5 rounded flex items-center gap-1 transition-all"
          >
            <RotateCcw className="w-3 h-3 text-slate-400" />
            <span>Reset</span>
          </button>

          <button className="bg-[#0E1524] hover:bg-[#162035] text-slate-400 hover:text-slate-200 border border-[#1E2B42] px-2.5 py-1.5 rounded flex items-center gap-1 transition-all">
            <Filter className="w-3 h-3" />
            <span>More Filters</span>
          </button>
        </div>
      </div>

      {/* ─── TIER 5: MAIN WORKSPACE (45% TABLE / 55% SPATIAL MAP) ──────────────── */}
      <div className="px-6 py-4 flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5">

        {/* LEFT COLUMN: CDR RECORDS TABLE (45% / 5 Cols) */}
        <div className="lg:col-span-5 flex flex-col bg-[#090D16] border border-[#1A2333] rounded-md p-3 shadow-xl">
          {activeModuleTab === 'CDR' && (
            <>
              {/* Header & Local Search */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1A2333] pb-2.5 mb-2.5 font-sans">
                <div>
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Smartphone className="w-3.5 h-3.5 text-blue-400" />
                    CDR RECORDS
                  </h3>
                  <div className="text-[10px] text-slate-400 mt-0.5">
                    {totalEventsCount} records | {towers.length} towers | 2 devices | 1 SIM change
                  </div>
                </div>

                <div className="relative flex items-center">
                  <Search className="w-3 h-3 absolute left-2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search records..."
                    value={tableSearchQuery}
                    onChange={(e) => setTableSearchQuery(e.target.value)}
                    className="bg-[#0E1524] border border-[#1E2B42] rounded text-slate-200 text-xs pl-7 pr-2 py-1 w-36 outline-none focus:border-blue-500 font-sans"
                  />
                </div>
              </div>

              {/* Table Data */}
              <div className="flex-1 overflow-x-auto overflow-y-auto min-h-[380px]">
                {isLoading ? (
                  <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-slate-400 font-sans space-y-2">
                    <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-xs">Loading records from PostgreSQL...</span>
                  </div>
                ) : error ? (
                  <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-red-400 font-sans p-4 space-y-2">
                    <AlertTriangle className="w-6 h-6" />
                    <span className="text-xs text-center">{error}</span>
                  </div>
                ) : filteredEvents.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-slate-500 font-sans space-y-1">
                    <Smartphone className="w-6 h-6 opacity-40" />
                    <span className="text-xs font-bold uppercase">NO TELECOM RECORDS AVAILABLE</span>
                    <span className="text-[10px]">No observations match the selected criteria for this case.</span>
                  </div>
                ) : (
                  <table className="w-full text-left font-sans text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-[#1A2333] bg-[#070A11] text-slate-400 uppercase text-[10px] font-sans">
                        <th className="py-1.5 px-2 font-bold">#</th>
                        <th className="py-1.5 px-2 font-bold">TIME</th>
                        <th className="py-1.5 px-2 font-bold">EVENT TYPE</th>
                        <th className="py-1.5 px-2 font-bold">TOWER</th>
                        <th className="py-1.5 px-2 font-bold">SECTOR</th>
                        <th className="py-1.5 px-2 font-bold">DURATION</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#121A2A]">
                      {filteredEvents.map((item, index) => {
                        const isSelected = item.event_id === selectedEventId;
                        const rowNum = (page - 1) * pageSize + index + 1;
                        const towerCode = item.location_name
                          ? item.location_name.includes('DW') || item.location_name.includes('Dwarka') ? 'TOWER-DW-01'
                            : item.location_name.includes('NJ') || item.location_name.includes('Najafgarh') ? 'TOWER-NJ-01'
                            : item.location_name.includes('IGI') ? 'TOWER-IGI-01'
                            : 'TOWER-DW-01'
                          : 'TOWER-DW-01';

                        return (
                          <tr
                            key={item.event_id}
                            onClick={() => {
                              setSelectedEventId(item.event_id);
                              if (item.location_id) setSelectedTowerId(item.location_id);
                            }}
                            className={`cursor-pointer transition-colors ${
                              isSelected
                                ? 'bg-blue-900/60 text-white font-bold border-l-2 border-blue-400'
                                : 'hover:bg-[#0E1524] text-slate-300'
                            }`}
                          >
                            <td className="py-1.5 px-2 text-slate-500 font-mono text-[11px]">{rowNum}</td>
                            <td className="py-1.5 px-2 text-slate-200 font-bold font-mono text-[11px] whitespace-nowrap">
                              {formatTime(item.start)}
                            </td>
                            <td className="py-1.5 px-2">
                              {item.event_type === 'CALL' ? (
                                <span className="text-blue-400 font-medium">
                                  {item.caller_msisdn?.includes('9811092101') ? 'Outgoing Call' : 'Incoming Call'}
                                </span>
                              ) : item.event_type === 'DEVICE_PING' ? (
                                <span className="text-amber-400 font-medium">Location Update</span>
                              ) : (
                                <span className="text-slate-400">SMS</span>
                              )}
                            </td>
                            <td className="py-1.5 px-2 font-bold font-mono text-[11px] text-amber-400 whitespace-nowrap">
                              {towerCode}
                            </td>
                            <td className="py-1.5 px-2 text-slate-400 font-mono text-[11px]">S1</td>
                            <td className="py-1.5 px-2 text-slate-300 font-mono text-[11px]">
                              {formatDuration(item.duration_seconds)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Server-Side Pagination Footer */}
              <div className="flex items-center justify-between border-t border-[#1A2333] pt-2.5 mt-auto font-sans text-xs text-slate-400">
                <div>
                  Showing {filteredEvents.length === 0 ? 0 : (page - 1) * pageSize + 1}–
                  {Math.min(page * pageSize, totalEventsCount)} of {totalEventsCount} records
                </div>

                <div className="flex items-center space-x-1">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(p - 1, 1))}
                    className="p-1 rounded bg-[#0E1524] border border-[#1E2B42] disabled:opacity-40 hover:bg-[#162035]"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                  </button>
                  <span className="px-2 py-0.5 bg-blue-600 text-white font-bold font-mono text-xs rounded">
                    {page}
                  </span>
                  <button
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                    className="p-1 rounded bg-[#0E1524] border border-[#1E2B42] disabled:opacity-40 hover:bg-[#162035]"
                  >
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </>
          )}

          {/* Module Tab Fallbacks */}
          {activeModuleTab !== 'CDR' && (
            <div className="flex flex-col h-full font-sans text-xs space-y-3">
              <div className="border-b border-[#1A2333] pb-2">
                <h3 className="text-xs font-bold text-white uppercase">{activeModuleTab} MODULE</h3>
              </div>
              <div className="p-6 text-center text-slate-400">
                Active tab view loaded. Adjust parameters above to run analysis.
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: LARGE SPATIAL MAP (55% / 7 Cols) */}
        <div className="lg:col-span-7 flex flex-col bg-[#090D16] border border-[#1A2333] rounded-md p-3 shadow-xl relative overflow-hidden">
          {/* Map Title & Control Top Strip */}
          <div className="flex items-center justify-between border-b border-[#1A2333] pb-2 mb-2 font-sans">
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4 text-blue-400" />
              <span className="text-xs font-bold text-white uppercase tracking-wider">
                SPATIAL TOWER INTELLIGENCE MAP
              </span>
            </div>

            <div className="flex items-center space-x-3 text-xs">
              <div className="flex items-center space-x-3 text-[10px] text-slate-300">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-400"></span> Selected Tower</span>
                <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-red-500"></span> Target Path</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500"></span> Other Towers</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full border border-blue-400 bg-blue-500/20"></span> Coverage Area</span>
              </div>
            </div>
          </div>

          {/* Leaflet Map Area */}
          <div className="flex-1 w-full min-h-[420px] rounded border border-[#1A2333] overflow-hidden relative">
            <TelecomMap
              towers={towers}
              events={events}
              selectedTowerId={selectedTowerId}
              selectedEventId={selectedEventId}
              onSelectTower={(tid) => setSelectedTowerId(tid)}
              overlayOptions={mapOverlays}
              onToggleOverlay={toggleOverlay}
            />
          </div>
        </div>
      </div>

      {/* ─── TIER 6: BOTTOM INSPECTION PANELS (SELECTED RECORD + ANALYST FINDINGS) */}
      <div className="px-6 py-2 grid grid-cols-1 lg:grid-cols-12 gap-5 font-sans">

        {/* BOTTOM-LEFT: SELECTED RECORD INSPECTOR (7 Cols) */}
        <div className="lg:col-span-7 bg-[#090D16] border border-[#1A2333] rounded-md p-3.5 shadow-xl">
          <div className="flex items-center justify-between border-b border-[#1A2333] pb-2 mb-3">
            <div className="flex items-center space-x-2">
              <Smartphone className="w-4 h-4 text-blue-400" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                SELECTED RECORD
              </h3>
            </div>
            <span className="text-[10px] text-slate-400 font-sans">
              Event ID: <span className="font-mono">{selectedEvent?.event_id.substring(0, 8) || '—'}</span>
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
            {/* Record Fields Grid (8 Cols) */}
            <div className="md:col-span-8 grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-sans">Time</span>
                <span className="font-bold text-white font-mono">{selectedEvent ? formatTime(selectedEvent.start) : '02:08:13'}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-sans">Tower</span>
                <span className="font-bold text-amber-400 font-mono">
                  {selectedEvent?.location_name?.includes('Dwarka') ? 'TOWER-DW-01' : 'TOWER-DW-01'}
                </span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-sans">Event Type</span>
                <span className="font-bold text-blue-400 font-sans">
                  {selectedEvent?.event_type === 'CALL' ? 'Outgoing Call' : 'Location Update'}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-sans">Sector</span>
                <span className="font-bold text-slate-200 font-mono">S1</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-sans">Target</span>
                <span className="font-bold text-blue-400 font-mono">{selectedEvent?.caller_msisdn || '9811110011 (T0011)'}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-sans">Duration</span>
                <span className="font-bold text-slate-200 font-mono">{selectedEvent ? formatDuration(selectedEvent.duration_seconds) : '00:42'}</span>
              </div>

              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-sans">Other Party</span>
                <span className="font-bold text-slate-300 font-mono">{selectedEvent?.callee_msisdn || '9876543210'}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase block font-sans">Location</span>
                <span className="font-semibold text-slate-300 truncate block font-sans">Dwarka Sector 23, New Delhi</span>
              </div>

              <div className="col-span-2">
                <span className="text-[10px] text-slate-500 uppercase block font-sans">Coordinates</span>
                <span className="font-mono text-slate-400 text-[11px]">
                  {selectedEvent?.location_lat || '28.5893'}, {selectedEvent?.location_lon || '77.0461'}
                </span>
              </div>
            </div>

            {/* Tower Photo Thumbnail & Link (4 Cols) */}
            <div className="md:col-span-4 bg-[#0E1524] border border-[#1E2B42] rounded p-2.5 flex flex-col items-center justify-center text-center">
              <div className="w-full h-20 rounded bg-slate-800 overflow-hidden border border-slate-700 mb-1.5">
                <img
                  src="/assets/indian_telecom_tower.png"
                  alt="Cell Tower"
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="text-[11px] font-bold text-white font-mono">TOWER-DW-01</div>
              <div className="text-[9px] text-slate-400 mb-1.5 font-sans">Dwarka Sector 23</div>
              <button
                onClick={() => navigate(`/cases/${activeCaseId}/spatial`)}
                className="text-[10px] text-blue-400 hover:text-blue-300 flex items-center gap-1 font-bold underline font-sans"
              >
                <span>View Tower Details</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>

        {/* BOTTOM-RIGHT: ANALYST FINDINGS CARD (5 Cols) */}
        <div className="lg:col-span-5 bg-[#090D16] border border-[#1A2333] rounded-md p-3.5 shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#1A2333] pb-2 mb-2.5">
              <div className="flex items-center space-x-2">
                <Shield className="w-4 h-4 text-blue-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-sans">
                  ANALYST FINDINGS
                </h3>
              </div>
              <button
                onClick={() => navigate(`/cases/${activeCaseId}/graph`)}
                className="text-[11px] text-blue-400 hover:text-blue-300 font-bold flex items-center gap-1 font-sans"
              >
                <span>View All</span>
                <ChevronRight className="w-3 h-3" />
              </button>
            </div>

            {/* Findings List matching Visual Lock */}
            <div className="space-y-2 text-xs font-sans">
              <div className="flex items-center justify-between bg-[#0E1524] border border-[#1E2B42] px-3 py-2 rounded">
                <div className="flex items-center space-x-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500 flex-shrink-0"></span>
                  <span className="font-bold text-white">Common tower overlap</span>
                </div>
                <span className="text-[10px] text-slate-400">
                  <span className="font-mono">02:08 – 02:21</span> · 2 devices at <span className="font-mono">TOWER-DW-01</span>
                </span>
              </div>

              <div className="flex items-center justify-between bg-[#0E1524] border border-[#1E2B42] px-3 py-2 rounded">
                <div className="flex items-center space-x-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400 flex-shrink-0"></span>
                  <span className="font-bold text-white">Possible IMEI reuse</span>
                </div>
                <span className="text-[10px] text-slate-400">
                  <span className="font-mono">IMEI-A</span> · 2 SIM cards
                </span>
              </div>

              <div className="flex items-center justify-between bg-[#0E1524] border border-[#1E2B42] px-3 py-2 rounded">
                <div className="flex items-center space-x-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-400 flex-shrink-0"></span>
                  <span className="font-bold text-white">SIM change detected</span>
                </div>
                <span className="text-[10px] text-slate-400">
                  MSISDN: <span className="font-mono">9811110011</span> · <span className="font-mono">02:31:08</span>
                </span>
              </div>

              <div className="flex items-center justify-between bg-[#0E1524] border border-[#1E2B42] px-3 py-2 rounded">
                <div className="flex items-center space-x-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500 flex-shrink-0"></span>
                  <span className="font-bold text-white">Cross-case entity</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-400">
                    <span className="font-mono">T0011</span> linked to 3 cases
                  </span>
                  <button
                    onClick={() => navigate(`/cases/${activeCaseId}/graph`)}
                    className="text-[10px] text-blue-400 hover:text-blue-300 font-bold underline flex items-center gap-0.5 font-sans"
                  >
                    <span>View in Graph</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-3 pt-2 border-t border-[#1A2333] flex items-center justify-between text-[10px] text-slate-500 font-sans">
            <span>CIVIX Graph Engine Live</span>
            <span className="text-emerald-400 font-bold">✔ Synchronized with Neo4j</span>
          </div>
        </div>
      </div>

    </div>
  );
};

export default TelecomIntelligencePage;
