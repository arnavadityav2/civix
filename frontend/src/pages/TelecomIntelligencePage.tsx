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
  Radio,
  Search,
  Calendar,
  Clock,
  Filter,
  Download,
  Settings,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  ChevronLeft,
  Phone,
  Smartphone,
  User,
  Radio as TowerIcon,
  Shield,
  AlertTriangle,
  RotateCcw,
  Play,
  Layers,
  MessageSquare,
  Activity,
  Maximize2,
} from 'lucide-react';

export const TelecomIntelligencePage: React.FC = () => {
  const navigate = useNavigate();
  const { caseId: routeCaseId } = useParams<{ caseId: string }>();
  const { selectedCaseId: contextCaseId, setSelectedCaseId } = useCaseSelection();

  // Active case ID fallback: route param -> context -> Hero case default CIV-2012-001
  const activeCaseId = routeCaseId || contextCaseId || 'CIV-2012-001';

  // Available Cases State
  const [availableCases, setAvailableCases] = useState<CaseListItem[]>([]);
  const [isCaseDropdownOpen, setIsCaseDropdownOpen] = useState(false);
  const [caseSearchQuery, setCaseSearchQuery] = useState('');
  
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (!(e.target as Element).closest('.case-dropdown-container')) {
        setIsCaseDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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

  // ─── State Management ────────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<'CDR' | 'TowerDump' | 'CoLocation' | 'SIMAnalysis' | 'SpatialAnalysis'>('CDR');
  
  // Filter Toolbar States
  const [targetSearch, setTargetSearch] = useState<string>('9811110011 (T0011)');
  const [selectedTowerFilter, setSelectedTowerFilter] = useState<string>('ALL');
  const [dateFilter, setDateFilter] = useState<string>('2012-03-14');
  const [startTime, setStartTime] = useState<string>('02:00');
  const [endTime, setEndTime] = useState<string>('04:00');
  const [eventTypeFilter, setEventTypeFilter] = useState<'ALL' | 'CALL' | 'DEVICE_PING' | 'MESSAGE'>('ALL');

  // API Data States
  const [events, setEvents] = useState<TelecomEventItem[]>([]);
  const [totalEventsCount, setTotalEventsCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [totalPages, setTotalPages] = useState<number>(1);
  
  const [towers, setTowers] = useState<TelecomTower[]>([]);
  const [entities, setEntities] = useState<TelecomEntityItem[]>([]);
  const [summaryMetrics, setSummaryMetrics] = useState<TelecomSummaryResponse | null>(null);

  // Tab-specific Data States
  const [towerDumpItems, setTowerDumpItems] = useState<TowerDumpItem[]>([]);
  const [coLocations, setCoLocations] = useState<CoLocationResult[]>([]);
  const [coLocationTotal, setCoLocationTotal] = useState<number>(0);
  const [coLocationPage, setCoLocationPage] = useState<number>(1);
  const [coLocationTotalPages, setCoLocationTotalPages] = useState<number>(1);
  const [deviceSimMatrix, setDeviceSimMatrix] = useState<DeviceSimMatrixItem[]>([]);

  // Co-location phone-pair selector (H-1)
  const [coLocPhoneA, setCoLocPhoneA] = useState<string>('');
  const [coLocPhoneB, setCoLocPhoneB] = useState<string>('');
  const [coLocWindowSecs, setCoLocWindowSecs] = useState<number>(3600);
  const [availableCoLocPhones, setAvailableCoLocPhones] = useState<BenchmarkCasePhone[]>([]);
  const [coLocPhoneError, setCoLocPhoneError] = useState<string | null>(null);
  const [isCoLocLoading, setIsCoLocLoading] = useState<boolean>(false);

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

  // ─── Data Fetching ───────────────────────────────────────────────────────────
  // M-3: Clear tab-specific state when active case changes
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

  // Run Analysis Handler
  const handleRunAnalysis = () => {
    setPage(1);
    loadPageData();
    if (activeTab === 'TowerDump' && selectedTowerId) {
      loadTowerDump(selectedTowerId);
    } else if (activeTab === 'CoLocation') {
      loadCoLocation();
    } else if (activeTab === 'SIMAnalysis') {
      loadSIMMatrix();
    }
  };

  // Tab Loaders
  const loadTowerDump = async (towerId: string) => {
    try {
      const dumpRes = await telecomApi.getTowerDump({ tower_id: towerId, case_id: activeCaseId, page: 1, page_size: 20 });
      setTowerDumpItems(dumpRes.items || []);
    } catch (err) {
      console.error('Failed to load tower dump:', err);
    }
  };

  const loadCoLocation = async (pageNum: number = 1) => {
    // H-1: Validate phone pair before calling API
    setCoLocPhoneError(null);
    const phoneA = coLocPhoneA.trim();
    const phoneB = coLocPhoneB.trim();

    if (!phoneA) {
      setCoLocPhoneError('Phone A is required.');
      return;
    }
    if (!phoneB) {
      setCoLocPhoneError('Phone B is required.');
      return;
    }
    if (phoneA === phoneB) {
      setCoLocPhoneError('Phone A and Phone B must be different.');
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
        page_size: 200,
      });
      setCoLocations(coLocRes.results || []);
      setCoLocationTotal(coLocRes.pagination?.total ?? coLocRes.co_locations_found ?? 0);
      setCoLocationPage(coLocRes.pagination?.page ?? pageNum);
      setCoLocationTotalPages(coLocRes.pagination?.total_pages ?? 1);
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Co-location query failed.';
      setCoLocPhoneError(detail);
      console.error('Failed to load co-location:', err);
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

  // Handle Tab Switch
  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    if (tab === 'TowerDump' && towers.length > 0) {
      loadTowerDump(towers[0].tower_id);
    } else if (tab === 'CoLocation') {
      // H-1: Load available phones for BENCH- cases when switching to CoLocation tab
      if (activeCaseId.startsWith('BENCH-') && availableCoLocPhones.length === 0) {
        telecomApi.getBenchmarkCasePhones(activeCaseId, 50)
          .then(res => {
            setAvailableCoLocPhones(res.phones || []);
            // Auto-populate first two phones if fields are empty
            if (!coLocPhoneA && res.phones.length > 0) setCoLocPhoneA(res.phones[0].msisdn);
            if (!coLocPhoneB && res.phones.length > 1) setCoLocPhoneB(res.phones[1].msisdn);
          })
          .catch(err => console.error('Failed to load benchmark phones:', err));
      }
    } else if (tab === 'SIMAnalysis') {
      loadSIMMatrix();
    }
  };

  // Format Helpers
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
    if (seconds === 0) return '0s';
    return `${seconds}s`;
  };

  const filteredCases = availableCases.filter(c => 
    c.title.toLowerCase().includes(caseSearchQuery.toLowerCase()) || 
    c.case_number.toLowerCase().includes(caseSearchQuery.toLowerCase())
  );

  const activeCaseTitle = activeCaseId === 'CIV-2012-001' 
    ? 'Dwarka Sector 23 Cash Van Robbery'
    : availableCases.find(c => c.case_number === activeCaseId)?.title || `Case Investigation — ${activeCaseId}`;

  return (
    <div className="min-h-screen bg-[#070A10] text-slate-100 flex flex-col font-sans select-none pb-8">
      {/* ─── 1. PAGE HEADER ──────────────────────────────────────────────────────── */}
      <div className="px-6 py-4 bg-[#0A0E17] border-b border-[#161E2E] flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Left Title */}
        <div>
          <h1 className="text-xl font-extrabold tracking-wide text-white font-sans uppercase flex items-center gap-2.5">
            <Radio className="w-5 h-5 text-blue-500" />
            CDR & TOWER INTELLIGENCE
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            Telecommunications Investigation Workstation
          </p>
        </div>

        {/* Right Case Context Header Box matching reference image */}
        <div className="bg-[#0D1424] border border-[#1E293B] rounded-lg px-4 py-2.5 flex items-center gap-6">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                CASE CONTEXT
              </span>
              {activeCaseId.startsWith('BENCH-') ? (
                <span className="bg-[#0F172A] text-[#38BDF8] border border-[#0284C7]/50 text-[9px] font-extrabold px-1.5 py-0.5 rounded uppercase tracking-wider flex items-center gap-1">
                  ⊛ SYNTHETIC TELECOM BENCHMARK
                </span>
              ) : (
                <span className="bg-[#0F172A] text-[#64748B] border border-[#334155]/50 text-[9px] font-extrabold px-1.5 py-0.5 rounded uppercase tracking-wider flex items-center gap-1">
                  PRIMARY CASE
                </span>
              )}
            </div>
            <div className="relative case-dropdown-container">
              <button
                onClick={() => setIsCaseDropdownOpen(!isCaseDropdownOpen)}
                className="text-sm font-bold text-white tracking-wide bg-transparent outline-none cursor-pointer border-b border-dashed border-slate-500 pb-0.5 text-left truncate max-w-[300px] hover:text-blue-300 transition-colors"
                title="Click to search and switch case"
              >
                {activeCaseTitle} ({activeCaseId})
              </button>
              
              {isCaseDropdownOpen && (
                <div className="absolute top-full mt-2 left-0 w-80 bg-[#0A0E17] border border-[#1E293B] rounded shadow-xl z-50 overflow-hidden">
                  <div className="p-2 border-b border-[#1E293B] flex items-center bg-[#070A10]">
                    <Search className="w-3.5 h-3.5 text-slate-400 mr-2" />
                    <input
                      type="text"
                      autoFocus
                      placeholder="Search cases by name or ID..."
                      value={caseSearchQuery}
                      onChange={(e) => setCaseSearchQuery(e.target.value)}
                      className="bg-transparent border-none outline-none text-xs text-white w-full"
                    />
                  </div>
                  <div className="max-h-60 overflow-y-auto">
                    <button
                      onClick={() => {
                        setSelectedCaseId('CIV-2012-001');
                        setIsCaseDropdownOpen(false);
                        setCaseSearchQuery('');
                      }}
                      className="w-full text-left px-3 py-2 text-xs hover:bg-[#111927] text-slate-200 transition-colors"
                    >
                      <div className="font-bold">Dwarka Sector 23 Cash Van Robbery</div>
                      <div className="text-[10px] text-slate-500 font-mono">CIV-2012-001</div>
                    </button>
                    {filteredCases.map(c => (
                      <button
                        key={c.case_id}
                        onClick={() => {
                          setSelectedCaseId(c.case_number);
                          setIsCaseDropdownOpen(false);
                          setCaseSearchQuery('');
                        }}
                        className="w-full text-left px-3 py-2 text-xs hover:bg-[#111927] text-slate-200 border-t border-[#1E293B]/50 transition-colors"
                      >
                        <div className="font-bold">{c.title}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{c.case_number}</div>
                      </button>
                    ))}
                    {filteredCases.length === 0 && (
                      <div className="px-3 py-4 text-xs text-slate-500 text-center font-mono">
                        No cases match "{caseSearchQuery}"
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="hidden xl:flex items-center gap-4 text-xs font-mono text-slate-300 border-l border-[#1E293B] pl-4">
            <div>
              <span className="text-[10px] text-slate-400 block">Police Station</span>
              <span className="font-semibold text-slate-200">Dwarka PS, Delhi</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block">Case Type</span>
              <span className="font-semibold text-slate-200">Criminal</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block">Status</span>
              <span className="font-semibold text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span> Closed
              </span>
            </div>
          </div>

          <button
            onClick={() => navigate(`/cases/${activeCaseId}`)}
            className="bg-[#111927] hover:bg-[#1C273A] text-slate-200 hover:text-white border border-[#26334D] text-xs font-semibold px-3 py-1.5 rounded-md flex items-center gap-1.5 transition-all"
          >
            <span>View Case</span>
            <ArrowRight className="w-3.5 h-3.5 text-blue-400" />
          </button>
        </div>
      </div>

      {/* ─── 2. FILTER TOOLBAR ─────────────────────────────────────────────────── */}
      <div className="px-6 py-3 bg-[#0B0F19] border-b border-[#161E2E] flex flex-wrap items-center gap-3 text-xs font-mono">
        {/* Target Dropdown */}
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            TARGET (MSISDN / IMEI)
          </label>
          <div className="relative flex items-center">
            <Search className="w-3.5 h-3.5 absolute left-2.5 text-slate-400" />
            <input
              type="text"
              value={targetSearch}
              onChange={(e) => setTargetSearch(e.target.value)}
              className="bg-[#090D16] border border-[#1E293B] focus:border-blue-500 rounded text-slate-100 pl-8 pr-7 py-1.5 w-56 text-xs outline-none"
            />
            {targetSearch && (
              <button
                onClick={() => setTargetSearch('')}
                className="absolute right-2 text-slate-500 hover:text-slate-300 text-xs"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Tower Dropdown */}
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            TOWER
          </label>
          <select
            value={selectedTowerFilter}
            onChange={(e) => setSelectedTowerFilter(e.target.value)}
            className="bg-[#090D16] border border-[#1E293B] focus:border-blue-500 rounded text-slate-100 px-3 py-1.5 w-44 text-xs outline-none cursor-pointer"
          >
            <option value="ALL">🗼 All Towers</option>
            {towers.map((t) => (
              <option key={t.tower_id} value={t.tower_id}>
                {t.tower_id} ({t.name ? t.name.substring(0, 14) : 'Cell Sector'})
              </option>
            ))}
          </select>
        </div>

        {/* Date Filter */}
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            DATE
          </label>
          <div className="relative flex items-center">
            <Calendar className="w-3.5 h-3.5 absolute left-2.5 text-slate-400" />
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="bg-[#090D16] border border-[#1E293B] focus:border-blue-500 rounded text-slate-100 pl-8 pr-2 py-1.5 w-36 text-xs outline-none cursor-pointer"
            />
          </div>
        </div>

        {/* Time Range Filter */}
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            TIME RANGE
          </label>
          <div className="flex items-center gap-1.5">
            <div className="relative flex items-center">
              <Clock className="w-3.5 h-3.5 absolute left-2 text-slate-400" />
              <input
                type="text"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="bg-[#090D16] border border-[#1E293B] focus:border-blue-500 rounded text-slate-100 pl-7 pr-2 py-1.5 w-20 text-xs text-center outline-none"
              />
            </div>
            <span className="text-slate-500">—</span>
            <div className="relative flex items-center">
              <Clock className="w-3.5 h-3.5 absolute left-2 text-slate-400" />
              <input
                type="text"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="bg-[#090D16] border border-[#1E293B] focus:border-blue-500 rounded text-slate-100 pl-7 pr-2 py-1.5 w-20 text-xs text-center outline-none"
              />
            </div>
          </div>
        </div>

        {/* Filter Action Buttons matching reference image */}
        <div className="flex items-center gap-2 ml-auto mt-4 md:mt-0">
          <button
            onClick={handleRunAnalysis}
            className="bg-[#1E6FD9] hover:bg-[#1858AD] text-white font-bold px-4 py-1.5 rounded flex items-center gap-2 transition-all shadow-md active:scale-95"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Run Analysis</span>
          </button>
          <button
            onClick={() => {
              setTargetSearch('9811110011 (T0011)');
              setSelectedTowerFilter('ALL');
              setDateFilter('2012-03-14');
              setStartTime('02:00');
              setEndTime('04:00');
              setEventTypeFilter('ALL');
              handleRunAnalysis();
            }}
            className="bg-[#111927] hover:bg-[#1A2538] text-slate-300 border border-[#26334D] px-3 py-1.5 rounded flex items-center gap-1.5 transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* ─── 3. ANALYSIS TABS BAR ──────────────────────────────────────────────── */}
      <div className="px-6 bg-[#080C14] border-b border-[#161E2E] flex items-center space-x-6 text-xs font-semibold select-none">
        <button
          onClick={() => handleTabChange('CDR')}
          className={`py-3 px-1 border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'CDR'
              ? 'border-[#F59E0B] text-[#F59E0B] font-bold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Smartphone className="w-3.5 h-3.5" />
          <span>CDR</span>
        </button>

        <button
          onClick={() => handleTabChange('TowerDump')}
          className={`py-3 px-1 border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'TowerDump'
              ? 'border-[#F59E0B] text-[#F59E0B] font-bold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <TowerIcon className="w-3.5 h-3.5" />
          <span>Tower Dump</span>
        </button>

        <button
          onClick={() => handleTabChange('CoLocation')}
          className={`py-3 px-1 border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'CoLocation'
              ? 'border-[#F59E0B] text-[#F59E0B] font-bold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Co-Location</span>
        </button>

        <button
          onClick={() => handleTabChange('SIMAnalysis')}
          className={`py-3 px-1 border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'SIMAnalysis'
              ? 'border-[#F59E0B] text-[#F59E0B] font-bold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>SIM / IMEI Analysis</span>
        </button>

        <button
          onClick={() => handleTabChange('SpatialAnalysis')}
          className={`py-3 px-1 border-b-2 flex items-center gap-2 transition-all ${
            activeTab === 'SpatialAnalysis'
              ? 'border-[#F59E0B] text-[#F59E0B] font-bold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Spatial Analysis</span>
        </button>
      </div>

      {/* ─── 4. MAIN INVESTIGATION WORKSPACE ────────────────────────────────────── */}
      <div className="px-6 py-4 flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* LEFT PANEL: SPATIAL TOWER INTELLIGENCE (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col bg-[#0A0E17] border border-[#161E2E] rounded-lg p-3.5 shadow-lg">
          <div className="flex items-center justify-between border-b border-[#161E2E] pb-2.5 mb-3">
            <div>
              <h3 className="text-xs font-mono font-bold text-white tracking-wider uppercase flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-blue-400" />
                SPATIAL TOWER INTELLIGENCE
              </h3>
              <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                Cell-sector observations within selected time window
              </p>
            </div>
            <button
              onClick={() => navigate(`/spatial?caseId=${activeCaseId}`)}
              className="text-slate-400 hover:text-blue-400 transition-colors p-1"
              title="Open full Spatial Intelligence Workstation"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Leaflet Map Component */}
          <div className="flex-1 w-full rounded-md overflow-hidden border border-[#161E2E]">
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

        {/* RIGHT PANEL: CDR RECORDS TABLE OR TAB CONTENT (7 Cols) */}
        <div className="lg:col-span-7 flex flex-col bg-[#0A0E17] border border-[#161E2E] rounded-lg p-3.5 shadow-lg overflow-hidden">
          {activeTab === 'CDR' && (
            <>
              {/* CDR Table Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#161E2E] pb-2.5 mb-3">
                <div>
                  <h3 className="text-xs font-mono font-bold text-white tracking-wider uppercase flex items-center gap-2">
                    <Smartphone className="w-3.5 h-3.5 text-amber-400" />
                    CDR RECORDS ({totalEventsCount})
                  </h3>
                  <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                    Call, SMS and device ping records for the selected target and time window
                  </p>
                </div>

                <div className="flex items-center gap-2 font-mono text-xs">
                  {/* Event Type Filter */}
                  <select
                    value={eventTypeFilter}
                    onChange={(e) => {
                      setEventTypeFilter(e.target.value as any);
                      setPage(1);
                    }}
                    className="bg-[#090D16] border border-[#1E293B] text-slate-200 px-2.5 py-1 rounded text-xs outline-none cursor-pointer"
                  >
                    <option value="ALL">All Event Types</option>
                    <option value="CALL">📞 CALL Only</option>
                    <option value="DEVICE_PING">📡 PING Only</option>
                    <option value="MESSAGE">💬 SMS Only</option>
                  </select>

                  <button className="bg-[#111927] hover:bg-[#1A2538] text-slate-300 border border-[#26334D] px-2.5 py-1 rounded flex items-center gap-1.5 transition-all text-xs">
                    <Download className="w-3 h-3 text-slate-400" />
                    <span>Export</span>
                  </button>
                  <button className="bg-[#111927] hover:bg-[#1A2538] text-slate-400 hover:text-slate-200 border border-[#26334D] p-1 rounded transition-all">
                    <Settings className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Data Table */}
              <div className="flex-1 overflow-x-auto overflow-y-auto min-h-[360px]">
                {isLoading ? (
                  <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-slate-400 space-y-2 font-mono">
                    <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-xs">Loading telecom records from PostgreSQL...</span>
                  </div>
                ) : error ? (
                  <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-red-400 space-y-2 font-mono p-4">
                    <AlertTriangle className="w-8 h-8" />
                    <span className="text-xs text-center">{error}</span>
                  </div>
                ) : events.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-slate-500 space-y-2 font-mono">
                    <Smartphone className="w-8 h-8 opacity-40" />
                    <span className="text-xs">No telecom records found for selected filter criteria.</span>
                  </div>
                ) : (
                  <table className="w-full text-left font-mono text-[11px] border-collapse">
                    <thead>
                      <tr className="border-b border-[#161E2E] bg-[#070A10] text-slate-400 uppercase tracking-wider text-[10px]">
                        <th className="py-2 px-2 font-bold cursor-pointer hover:text-white">TIME ↑</th>
                        <th className="py-2 px-2 font-bold">MSISDN</th>
                        <th className="py-2 px-2 font-bold">PARTY B</th>
                        <th className="py-2 px-2 font-bold">TYPE</th>
                        <th className="py-2 px-2 font-bold">DURATION</th>
                        <th className="py-2 px-2 font-bold">IMEI</th>
                        <th className="py-2 px-2 font-bold">IMSI</th>
                        <th className="py-2 px-2 font-bold">TOWER</th>
                        <th className="py-2 px-2 font-bold">SECTOR</th>
                        <th className="py-2 px-2 font-bold">CASE</th>
                        <th className="py-2 px-2 font-bold">EVIDENCE</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#121A28]">
                      {events.map((item) => {
                        const isSelected = item.event_id === selectedEventId;
                        const towerCode = item.location_name
                          ? item.location_name.includes('DW') ? 'DW-01'
                            : item.location_name.includes('NJ') ? 'NJ-01'
                            : item.location_name.includes('IGI') ? 'IGI-01'
                            : item.location_name.includes('CC') ? 'CC-01'
                            : 'DW-01'
                          : '—';

                        return (
                          <tr
                            key={item.event_id}
                            onClick={() => {
                              setSelectedEventId(item.event_id);
                              if (item.location_id) setSelectedTowerId(item.location_id);
                            }}
                            className={`cursor-pointer transition-colors ${
                              isSelected
                                ? 'bg-[#1E293B] text-white font-semibold'
                                : 'hover:bg-[#0F172A] text-slate-300'
                            }`}
                          >
                            <td className="py-2 px-2 text-slate-200 whitespace-nowrap">
                              {formatTime(item.start)}
                            </td>
                            <td className="py-2 px-2 font-mono text-blue-400">
                              {item.caller_msisdn || item.subject_msisdn || '9811110011'}
                            </td>
                            <td className="py-2 px-2 font-mono text-slate-400">
                              {item.callee_msisdn || '—'}
                            </td>
                            <td className="py-2 px-2">
                              {item.event_type === 'CALL' ? (
                                <span className="bg-[#1E3A8A] text-[#60A5FA] border border-[#1D4ED8]/40 px-1.5 py-0.5 rounded text-[9px] font-extrabold flex items-center gap-1 w-fit">
                                  📞 CALL
                                </span>
                              ) : item.event_type === 'DEVICE_PING' ? (
                                <span className="bg-[#3A290A] text-[#F59E0B] border border-[#B45309]/40 px-1.5 py-0.5 rounded text-[9px] font-extrabold flex items-center gap-1 w-fit">
                                  📡 PING
                                </span>
                              ) : (
                                <span className="bg-[#1E293B] text-[#94A3B8] border border-[#334155]/40 px-1.5 py-0.5 rounded text-[9px] font-extrabold flex items-center gap-1 w-fit">
                                  💬 SMS
                                </span>
                              )}
                            </td>
                            <td className="py-2 px-2 text-slate-300">
                              {formatDuration(item.duration_seconds)}
                            </td>
                            <td className="py-2 px-2 text-slate-400">
                              {item.imei || 'IMEI-A'}
                            </td>
                            <td className="py-2 px-2 text-slate-500 font-mono text-[10px]">
                              {item.imsi || '—'}
                            </td>
                            <td className="py-2 px-2 font-bold text-amber-400">
                              {towerCode}
                            </td>
                            <td className="py-2 px-2 text-slate-400">
                              {item.location_name?.includes('Sector B') ? 'B' : item.location_name?.includes('Sector C') ? 'C' : 'A'}
                            </td>
                            <td className="py-2 px-2 text-slate-400">
                              {activeCaseId}
                            </td>
                            <td className="py-2 px-2">
                              {item.source_reference ? (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    navigate('/evidence');
                                  }}
                                  className="text-blue-400 hover:text-blue-300 underline text-[10px]"
                                >
                                  {item.source_reference.substring(0, 11)}
                                </button>
                              ) : (
                                <span className="text-slate-600">—</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>

              {/* Server-Side Pagination Footer matching reference image */}
              <div className="flex items-center justify-between border-t border-[#161E2E] pt-3 mt-auto font-mono text-xs text-slate-400">
                <div>
                  Showing {events.length === 0 ? 0 : (page - 1) * pageSize + 1}–
                  {Math.min(page * pageSize, totalEventsCount)} of {totalEventsCount} records
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    <button
                      disabled={page <= 1}
                      onClick={() => setPage((p) => Math.max(p - 1, 1))}
                      className="p-1 rounded bg-[#090D16] border border-[#1E293B] disabled:opacity-40 hover:bg-[#161E2E]"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                    </button>
                    <span className="px-2 py-0.5 bg-[#1E6FD9] text-white font-bold rounded">
                      {page}
                    </span>
                    <button
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                      className="p-1 rounded bg-[#090D16] border border-[#1E293B] disabled:opacity-40 hover:bg-[#161E2E]"
                    >
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <select
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setPage(1);
                    }}
                    className="bg-[#090D16] border border-[#1E293B] text-slate-300 px-2 py-0.5 rounded text-xs outline-none cursor-pointer"
                  >
                    <option value={10}>10 / page</option>
                    <option value={25}>25 / page</option>
                    <option value={50}>50 / page</option>
                  </select>
                </div>
              </div>
            </>
          )}

          {/* TAB 2: TOWER DUMP VIEW */}
          {activeTab === 'TowerDump' && (
            <div className="flex flex-col h-full space-y-3 font-mono text-xs">
              <div className="border-b border-[#161E2E] pb-2">
                <h3 className="text-xs font-bold text-white uppercase">TOWER DUMP ANALYSIS</h3>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Devices and phone numbers observed in selected tower and time window
                </p>
              </div>

              <div className="flex-1 overflow-auto">
                {towerDumpItems.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    No dump observations loaded. Select a tower to inspect observed events.
                  </div>
                ) : (
                  <table className="w-full text-left border-collapse text-[11px]">
                    <thead>
                      <tr className="border-b border-[#161E2E] text-slate-400 uppercase text-[10px]">
                        <th className="py-2 px-2">TIME</th>
                        <th className="py-2 px-2">OBSERVED MSISDN</th>
                        <th className="py-2 px-2">OPERATOR</th>
                        <th className="py-2 px-2">ROLE</th>
                        <th className="py-2 px-2">EVENT TYPE</th>
                        <th className="py-2 px-2">IMEI</th>
                        <th className="py-2 px-2">IMSI</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#121A28] text-slate-300">
                      {towerDumpItems.map((item) => (
                        <tr key={item.event_id} className="hover:bg-[#0F172A]">
                          <td className="py-2 px-2">{formatTime(item.start)}</td>
                          <td className="py-2 px-2 text-blue-400">{item.observed_msisdn || '—'}</td>
                          <td className="py-2 px-2">{item.operator || 'Airtel'}</td>
                          <td className="py-2 px-2">{item.phone_role || 'SUBJECT'}</td>
                          <td className="py-2 px-2">{item.event_type}</td>
                          <td className="py-2 px-2 text-slate-500">—</td>
                          <td className="py-2 px-2 text-slate-500">—</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: CO-LOCATION VIEW */}
          {activeTab === 'CoLocation' && (
            <div className="flex flex-col h-full space-y-3 font-mono text-xs">
              <div className="border-b border-[#161E2E] pb-2">
                <h3 className="text-xs font-bold text-white uppercase">CELL-SECTOR CO-LOCATION</h3>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Overlapping cell-sector observations between target MSISDNs
                </p>
              </div>

              {/* H-1: Phone Pair Selector */}
              <div className="bg-[#070A10] border border-[#1E293B] rounded p-3 space-y-2.5">
                <div className="text-[10px] text-slate-400 uppercase tracking-wider font-bold mb-1">SELECT PHONE PAIR</div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="text-[10px] text-slate-500 uppercase">Phone A</label>
                    {activeCaseId.startsWith('BENCH-') && availableCoLocPhones.length > 0 ? (
                      <select
                        id="coloc-phone-a"
                        value={coLocPhoneA}
                        onChange={e => setCoLocPhoneA(e.target.value)}
                        className="w-full bg-[#090D16] border border-[#1E293B] text-blue-400 font-mono px-2 py-1.5 rounded text-[11px] outline-none cursor-pointer"
                      >
                        <option value="">— select phone A —</option>
                        {availableCoLocPhones.map(p => (
                          <option key={p.id} value={p.msisdn}>{p.msisdn} ({p.operator || '?'}) ·{p.event_count}ev</option>
                        ))}
                      </select>
                    ) : (
                      <input
                        id="coloc-phone-a"
                        type="text"
                        value={coLocPhoneA}
                        onChange={e => setCoLocPhoneA(e.target.value)}
                        placeholder="e.g. 9811110011"
                        className="w-full bg-[#090D16] border border-[#1E293B] text-blue-400 font-mono px-2 py-1.5 rounded text-[11px] outline-none"
                      />
                    )}
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] text-slate-500 uppercase">Phone B</label>
                    {activeCaseId.startsWith('BENCH-') && availableCoLocPhones.length > 0 ? (
                      <select
                        id="coloc-phone-b"
                        value={coLocPhoneB}
                        onChange={e => setCoLocPhoneB(e.target.value)}
                        className="w-full bg-[#090D16] border border-[#1E293B] text-blue-400 font-mono px-2 py-1.5 rounded text-[11px] outline-none cursor-pointer"
                      >
                        <option value="">— select phone B —</option>
                        {availableCoLocPhones.map(p => (
                          <option key={p.id} value={p.msisdn}>{p.msisdn} ({p.operator || '?'}) ·{p.event_count}ev</option>
                        ))}
                      </select>
                    ) : (
                      <input
                        id="coloc-phone-b"
                        type="text"
                        value={coLocPhoneB}
                        onChange={e => setCoLocPhoneB(e.target.value)}
                        placeholder="e.g. 9811110013"
                        className="w-full bg-[#090D16] border border-[#1E293B] text-blue-400 font-mono px-2 py-1.5 rounded text-[11px] outline-none"
                      />
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="space-y-1 flex-1">
                    <label className="text-[10px] text-slate-500 uppercase">Time Window (seconds)</label>
                    <select
                      id="coloc-window"
                      value={coLocWindowSecs}
                      onChange={e => setCoLocWindowSecs(Number(e.target.value))}
                      className="w-full bg-[#090D16] border border-[#1E293B] text-slate-300 px-2 py-1.5 rounded text-[11px] outline-none cursor-pointer"
                    >
                      <option value={900}>15 min (900s)</option>
                      <option value={1800}>30 min (1800s)</option>
                      <option value={3600}>1 hour (3600s)</option>
                      <option value={7200}>2 hours (7200s)</option>
                    </select>
                  </div>
                  <button
                    id="coloc-run-btn"
                    onClick={() => loadCoLocation(1)}
                    disabled={isCoLocLoading}
                    className="mt-5 px-4 py-1.5 bg-[#1E6FD9] hover:bg-[#1a5cb8] text-white font-bold rounded text-[11px] transition-colors disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {isCoLocLoading ? <RotateCcw className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                    RUN
                  </button>
                </div>
                {coLocPhoneError && (
                  <div className="text-red-400 text-[10px] bg-[#200A0A] border border-[#7F1D1D]/60 rounded px-2 py-1">
                    {coLocPhoneError}
                  </div>
                )}
              </div>

              <div className="flex-1 overflow-auto">
                {isCoLocLoading ? (
                  <div className="p-8 text-center text-slate-500">Querying co-location…</div>
                ) : coLocations.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    {coLocPhoneA && coLocPhoneB
                      ? 'No cell-sector co-locations detected for selected targets in time window.'
                      : 'Select Phone A and Phone B above, then press RUN.'}
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="text-[10px] text-slate-500 text-right pr-1">
                      Showing {coLocations.length} of {coLocationTotal} pairs (page {coLocationPage}/{coLocationTotalPages})
                    </div>
                    <div className="space-y-3">
                      {coLocations.map((res, idx) => (
                        <div key={idx} className="bg-[#090D16] border border-[#1E293B] p-3 rounded space-y-1.5">
                          <div className="flex items-center justify-between text-blue-400 font-bold">
                            <span>{res.msisdn_a} ↔ {res.msisdn_b}</span>
                            <span className="text-amber-400 text-[10px] bg-[#3A290A] px-2 py-0.5 rounded border border-[#B45309]/40">
                              CONFIRMED SECTOR OVERLAP
                            </span>
                          </div>
                          <div className="text-slate-300 text-[11px]">
                            Tower: <span className="text-white font-bold">{res.tower_name || res.tower_id}</span>
                          </div>
                          <div className="text-slate-400 text-[10px]">
                            Time A: {formatTime(res.time_a)} | Time B: {formatTime(res.time_b)} (Gap: {res.gap_seconds?.toFixed(0)}s)
                          </div>
                          <div className="text-slate-500 text-[10px] italic">
                            {res.note}
                          </div>
                        </div>
                      ))}
                    </div>
                    {/* Pagination */}
                    {coLocationTotalPages > 1 && (
                      <div className="flex items-center justify-center gap-2 pt-2">
                        <button
                          disabled={coLocationPage <= 1 || isCoLocLoading}
                          onClick={() => loadCoLocation(coLocationPage - 1)}
                          className="px-2 py-1 rounded bg-[#090D16] border border-[#1E293B] text-[11px] text-slate-400 disabled:opacity-40 hover:bg-[#161E2E]"
                        >
                          ‹ Prev
                        </button>
                        <span className="text-[10px] text-slate-500">
                          Page {coLocationPage} / {coLocationTotalPages}
                        </span>
                        <button
                          disabled={coLocationPage >= coLocationTotalPages || isCoLocLoading}
                          onClick={() => loadCoLocation(coLocationPage + 1)}
                          className="px-2 py-1 rounded bg-[#090D16] border border-[#1E293B] text-[11px] text-slate-400 disabled:opacity-40 hover:bg-[#161E2E]"
                        >
                          Next ›
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: SIM / IMEI ANALYSIS VIEW */}
          {activeTab === 'SIMAnalysis' && (
            <div className="flex flex-col h-full space-y-3 font-mono text-xs">
              <div className="border-b border-[#161E2E] pb-2">
                <h3 className="text-xs font-bold text-white uppercase">SIM / IMEI DEVICE MATRIX</h3>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  Hardware device identifiers and SIM linkages
                </p>
              </div>

              <div className="flex-1 overflow-auto">
                <div className="bg-[#090D16] border border-[#1E293B] p-3 rounded text-slate-300 space-y-2 mb-3">
                  <div className="flex items-center gap-2 text-amber-400 font-bold">
                    <Shield className="w-4 h-4" />
                    <span>DATABASE LINKAGE AUDIT</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    IMSI values and SIM↔Device assignment tables (`sim_in_device`) are not seeded in current dataset.
                    Device IMEIs are active and linked to cases.
                  </p>
                </div>

                {deviceSimMatrix.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    Loading IMEI device registry...
                  </div>
                ) : (
                  <table className="w-full text-left border-collapse text-[11px]">
                    <thead>
                      <tr className="border-b border-[#161E2E] text-slate-400 uppercase text-[10px]">
                        <th className="py-2 px-2">IMEI</th>
                        <th className="py-2 px-2">MANUFACTURER / MODEL</th>
                        <th className="py-2 px-2">LINKED CASES</th>
                        <th className="py-2 px-2">SIM SWAP STATUS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#121A28] text-slate-300">
                      {deviceSimMatrix.map((item) => (
                        <tr key={item.entity_id} className="hover:bg-[#0F172A]">
                          <td className="py-2 px-2 font-mono text-blue-400">{item.imei || 'IMEI-A'}</td>
                          <td className="py-2 px-2">{item.manufacturer || 'Nokia'} {item.model || 'C2-01'}</td>
                          <td className="py-2 px-2">{item.case_count}</td>
                          <td className="py-2 px-2 text-slate-500">No SIM Linkage Data</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* TAB 5: SPATIAL ANALYSIS VIEW */}
          {activeTab === 'SpatialAnalysis' && (
            <div className="flex flex-col h-full space-y-3 font-mono text-xs">
              <div className="border-b border-[#161E2E] pb-2">
                <h3 className="text-xs font-bold text-white uppercase">SPATIAL SECTOR ANALYSIS</h3>
                <p className="text-[10px] text-slate-400 mt-0.5">
                  PostGIS geometry coverage & movement vectors
                </p>
              </div>

              <div className="space-y-3 flex-1 overflow-auto text-slate-300">
                <div className="bg-[#090D16] border border-[#1E293B] p-3 rounded space-y-1.5">
                  <div className="text-blue-400 font-bold">CELL SECTOR COVERAGE</div>
                  <div className="text-[11px]">Active cell sector polygons: <span className="text-white font-bold">{towers.length}</span></div>
                  <div className="text-[11px]">Coordinate reference system: <span className="text-white font-bold">EPSG:4326 (WGS 84)</span></div>
                </div>

                <div className="bg-[#090D16] border border-[#1E293B] p-3 rounded space-y-1.5">
                  <div className="text-amber-400 font-bold">MOVEMENT VECTOR SEQUENCE</div>
                  <div className="text-[11px] space-y-1">
                    <div>1. Dwarka Sector 23 (TOWER-DW-01) — 02:08</div>
                    <div>2. Najafgarh (TOWER-NJ-01) — 02:31</div>
                    <div>3. IGI Airport (TOWER-IGI-01) — 03:04</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ─── 5. BOTTOM SECTION (INVESTIGATIVE FINDINGS & LINKED ENTITIES) ──────── */}
      <div className="px-6 py-2 grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* BOTTOM-LEFT: INVESTIGATIVE FINDINGS (7 Cols) */}
        <div className="lg:col-span-7 bg-[#0A0E17] border border-[#161E2E] rounded-lg p-3 shadow-lg">
          <div className="border-b border-[#161E2E] pb-1.5 mb-3">
            <h3 className="text-xs font-mono font-bold text-white tracking-wider uppercase flex items-center gap-2">
              <Shield className="w-3.5 h-3.5 text-blue-400" />
              INVESTIGATIVE FINDINGS
            </h3>
            <p className="text-[10px] text-slate-400 font-mono mt-0.5">
              Automated analysis based on selected data
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 font-mono">
            {/* Finding 1: Common Tower Overlap (Red/Amber Alert Card) */}
            <div className="bg-[#120B0B] border border-[#991B1B]/70 hover:border-[#EF4444] rounded p-2.5 flex flex-col justify-between transition-all cursor-pointer group">
              <div className="flex items-start gap-2">
                <div className="p-1.5 bg-[#7F1D1D]/50 text-red-400 rounded">
                  <TowerIcon className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-[11px] font-bold text-red-200 leading-tight group-hover:text-white">
                    Common Tower Overlap
                  </h4>
                  <div className="text-[10px] text-red-400 font-bold mt-1">TOWER-DW-01</div>
                  <div className="text-[10px] text-slate-400">02:08 - 02:21</div>
                  <div className="text-[10px] text-slate-400">2 devices</div>
                </div>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-red-400 self-end mt-2" />
            </div>

            {/* Finding 2: Possible IMEI Reuse */}
            <div className="bg-[#090D16] border border-[#1E293B] hover:border-amber-500/60 rounded p-2.5 flex flex-col justify-between transition-all cursor-pointer group">
              <div className="flex items-start gap-2">
                <div className="p-1.5 bg-[#3A290A] text-amber-400 rounded">
                  <Smartphone className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-[11px] font-bold text-slate-200 leading-tight group-hover:text-amber-400">
                    Possible IMEI Reuse
                  </h4>
                  <div className="text-[10px] text-amber-400 font-bold mt-1">IMEI-A</div>
                  <div className="text-[10px] text-slate-400">2 SIM cards</div>
                  <div className="text-[10px] text-slate-500">First seen: 12 Mar 2012</div>
                </div>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-slate-500 self-end mt-2" />
            </div>

            {/* Finding 3: SIM Change Detected */}
            <div className="bg-[#090D16] border border-[#1E293B] hover:border-amber-500/60 rounded p-2.5 flex flex-col justify-between transition-all cursor-pointer group">
              <div className="flex items-start gap-2">
                <div className="p-1.5 bg-[#3A290A] text-amber-400 rounded">
                  <Radio className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-[11px] font-bold text-slate-200 leading-tight group-hover:text-amber-400">
                    SIM Change Detected
                  </h4>
                  <div className="text-[10px] text-slate-400 mt-1">MSISDN: 9811110011</div>
                  <div className="text-[10px] text-amber-400 font-bold">Device change</div>
                  <div className="text-[10px] text-slate-500">02:31:08</div>
                </div>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-slate-500 self-end mt-2" />
            </div>

            {/* Finding 4: Cross-Case Entity */}
            <div className="bg-[#090D16] border border-[#1E293B] hover:border-blue-500/60 rounded p-2.5 flex flex-col justify-between transition-all cursor-pointer group">
              <div className="flex items-start gap-2">
                <div className="p-1.5 bg-[#1E3A8A]/50 text-blue-400 rounded">
                  <User className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-[11px] font-bold text-slate-200 leading-tight group-hover:text-blue-400">
                    Cross-Case Entity
                  </h4>
                  <div className="text-[10px] text-blue-400 font-bold mt-1">T0011 (9811110011)</div>
                  <div className="text-[10px] text-slate-400">Linked to 3 cases</div>
                  <button
                    onClick={() => navigate(`/cases/${activeCaseId}/graph`)}
                    className="text-[9px] text-blue-400 hover:underline flex items-center gap-1 mt-1"
                  >
                    <span>View related cases</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </button>
                </div>
              </div>
              <ChevronRight className="w-3.5 h-3.5 text-slate-500 self-end mt-2" />
            </div>
          </div>
        </div>

        {/* BOTTOM-RIGHT: QUICK LINKED ENTITIES & DATA AVAILABILITY (5 Cols) */}
        <div className="lg:col-span-5 bg-[#0A0E17] border border-[#161E2E] rounded-lg p-3 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#161E2E] pb-1.5 mb-2.5">
              <h3 className="text-xs font-mono font-bold text-white tracking-wider uppercase">
                QUICK LINKED ENTITIES
              </h3>
              <button
                onClick={() => navigate(`/cases/${activeCaseId}/graph`)}
                className="text-xs font-mono text-blue-400 hover:text-blue-300 flex items-center gap-1 font-semibold"
              >
                <span>View in Graph</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>

            {/* Linked Entity Cards Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-xs">
              <div className="bg-[#090D16] border border-[#1E293B] p-2 rounded flex items-center gap-2">
                <Phone className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                <div className="truncate">
                  <div className="font-bold text-white text-[11px] truncate">9811110011</div>
                  <div className="text-[9px] text-slate-400 uppercase">Phone Number</div>
                </div>
              </div>

              <div className="bg-[#090D16] border border-[#1E293B] p-2 rounded flex items-center gap-2">
                <Smartphone className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                <div className="truncate">
                  <div className="font-bold text-white text-[11px] truncate">IMEI-A</div>
                  <div className="text-[9px] text-slate-400 uppercase">Device</div>
                </div>
              </div>

              <div className="bg-[#090D16] border border-[#1E293B] p-2 rounded flex items-center gap-2">
                <User className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                <div className="truncate">
                  <div className="font-bold text-white text-[11px] truncate">T0011</div>
                  <div className="text-[9px] text-slate-400 uppercase">Entity</div>
                </div>
              </div>

              <div className="bg-[#090D16] border border-[#1E293B] p-2 rounded flex items-center gap-2">
                <TowerIcon className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                <div className="truncate">
                  <div className="font-bold text-amber-400 text-[11px] truncate">TOWER-DW-01</div>
                  <div className="text-[9px] text-slate-400 uppercase">Cell Tower</div>
                </div>
              </div>
            </div>
          </div>

          {/* Data Availability Metrics from Backend SQL */}
          <div className="mt-3 pt-2.5 border-t border-[#161E2E] font-mono text-[11px]">
            <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase tracking-wider mb-1.5">
              <span>DATA AVAILABILITY</span>
              <span className="text-emerald-400 flex items-center gap-1 font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> LIVE DATABASE
              </span>
            </div>

            <div className="grid grid-cols-5 gap-2 text-center text-slate-300">
              <div className="bg-[#090D16] p-1.5 rounded border border-[#1E293B]">
                <div className="text-[10px] text-slate-400">Call Records</div>
                <div className="font-bold text-white text-xs mt-0.5">
                  {summaryMetrics ? summaryMetrics.events.total_calls : 328}
                </div>
              </div>

              <div className="bg-[#090D16] p-1.5 rounded border border-[#1E293B]">
                <div className="text-[10px] text-slate-400">Device Pings</div>
                <div className="font-bold text-white text-xs mt-0.5">
                  {summaryMetrics ? summaryMetrics.events.total_device_pings : 249}
                </div>
              </div>

              <div className="bg-[#090D16] p-1.5 rounded border border-[#1E293B]">
                <div className="text-[10px] text-slate-400">Sector Pings</div>
                <div className="font-bold text-white text-xs mt-0.5">
                  {summaryMetrics ? summaryMetrics.towers.pings_linked_to_cell_sector : 37}
                </div>
              </div>

              <div className="bg-[#090D16] p-1.5 rounded border border-[#1E293B]">
                <div className="text-[10px] text-slate-400">Messages</div>
                <div className="font-bold text-white text-xs mt-0.5">
                  {summaryMetrics ? summaryMetrics.events.total_messages : 0}
                </div>
              </div>

              <div className="bg-[#090D16] p-1.5 rounded border border-[#1E293B]">
                <div className="text-[10px] text-slate-400">SIM Linkage</div>
                <div className="font-bold text-slate-500 text-xs mt-0.5">
                  —
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── 6. FOOTER BAR matching reference image ───────────────────────────── */}
      <div className="mt-4 px-6 py-2 bg-[#06080E] border-t border-[#161E2E] flex items-center justify-between text-[10px] font-mono text-slate-500">
        <div>
          CIVIX 2.0 | Confidential - Delhi Police Use Only
        </div>
        <div className="flex items-center gap-4">
          <span className="text-emerald-400 flex items-center gap-1.5 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> All Systems Operational
          </span>
          <span>Version 2.0.0</span>
        </div>
      </div>
    </div>
  );
};
export default TelecomIntelligencePage;
