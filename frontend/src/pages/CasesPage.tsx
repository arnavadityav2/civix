import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { casesApi } from '../api/cases';
import { spatialApi } from '../api/spatial';
import { useCaseSelection } from '../context/CaseSelectionContext';
import type { CaseRegistryItem, CaseRegistryResponse } from '../types/api';
import { CaseRegistryMap } from '../components/spatial/CaseRegistryMap';
import { Badge } from '../components/ui/Badge';
import {
  Search,
  Briefcase,
  AlertTriangle,
  RefreshCw,
  X,
  Loader2,
  Users,
  Car,
  FileText,
  ChevronLeft,
  ChevronRight,
  MoreVertical
} from 'lucide-react';

// ── Types & Filter Categories ───────────────────────────────────────────────

type TabCategory =
  | 'ALL'
  | 'ACTIVE'
  | 'CRITICAL'
  | 'NEEDS_ATTENTION'
  | 'CONNECTED'
  | 'UNRESOLVED'
  | 'FINANCIAL'
  | 'PROPERTY'
  | 'INTELLIGENCE'
  | 'SURVEILLANCE';

const CASE_TYPES = ['CRIMINAL', 'FINANCIAL', 'PROPERTY', 'INTELLIGENCE', 'SURVEILLANCE', 'MULTI_CASE', 'CYBER_FRAUD'];
const PRIORITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

const STATUS_VARIANTS: Record<string, string> = {
  OPEN: 'active',
  ACTIVE: 'active',
  CLOSED_SOLVED: 'default',
  CLOSED_UNSOLVED: 'critical',
  SUSPENDED: 'warning',
};

const PRIORITY_VARIANTS: Record<string, string> = {
  CRITICAL: 'critical',
  HIGH: 'warning',
  MEDIUM: 'active',
  LOW: 'default',
};

// ── CasesPage Component ──────────────────────────────────────────────────────

export const CasesPage: React.FC = () => {
  const navigate = useNavigate();
  const { selectedCaseId, setSelectedCaseId } = useCaseSelection();

  // Filters & State
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [searchInput, setSearchInput] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [activeTab, setActiveTab] = useState<TabCategory>('ACTIVE');
  const [caseTypeFilter, setCaseTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [jurisdictionFilter, setJurisdictionFilter] = useState('');
  const [provenanceFilter, setProvenanceFilter] = useState('');
  const [sortBy, setSortBy] = useState('last_activity_at');
  const [sortOrder, setSortOrder] = useState('desc');

  // Compute query parameters for backend
  const effectiveParams = useMemo(() => {
    let type = caseTypeFilter;
    let stat = statusFilter;
    let prio = priorityFilter;

    if (activeTab === 'ACTIVE') stat = 'ACTIVE';
    else if (activeTab === 'CRITICAL') prio = 'CRITICAL';
    else if (activeTab === 'FINANCIAL') type = 'FINANCIAL';
    else if (activeTab === 'PROPERTY') type = 'PROPERTY';
    else if (activeTab === 'INTELLIGENCE') type = 'INTELLIGENCE';
    else if (activeTab === 'SURVEILLANCE') type = 'SURVEILLANCE';
    else if (activeTab === 'UNRESOLVED') stat = 'OPEN';

    return {
      page,
      page_size: pageSize,
      search: activeSearch.trim() || undefined,
      case_type: type || undefined,
      status: stat || undefined,
      priority: prio || undefined,
      jurisdiction: jurisdictionFilter.trim() || undefined,
      provenance: provenanceFilter || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    };
  }, [page, pageSize, activeSearch, activeTab, caseTypeFilter, statusFilter, priorityFilter, jurisdictionFilter, provenanceFilter, sortBy, sortOrder]);

  // Fetch Case Registry from Backend API
  const {
    data: registryResponse,
    isLoading: isRegistryLoading,
    error: registryError,
    refetch: refetchRegistry
  } = useQuery<CaseRegistryResponse>({
    queryKey: ['cases-registry', effectiveParams],
    queryFn: () => casesApi.getRegistry(effectiveParams),
    staleTime: 15_000,
  });

  // Fetch Spatial GeoJSON Features from PostGIS Backend
  const { data: spatialCollection } = useQuery({
    queryKey: ['spatial-cases'],
    queryFn: () => spatialApi.getSpatialCases(),
    staleTime: 30_000,
  });

  const spatialCases = spatialCollection?.features || [];
  const summary = registryResponse?.summary;
  const rawItems = registryResponse?.items || [];
  const pagination = registryResponse?.pagination;

  // Filter items dynamically for specific interactive tab selections
  const items = useMemo(() => {
    if (activeTab === 'NEEDS_ATTENTION') {
      return rawItems.filter(c => c.priority === 'CRITICAL' || c.status === 'OPEN' || c.lead_count > 2);
    }
    if (activeTab === 'CONNECTED') {
      return rawItems.filter(c => c.case_type === 'MULTI_CASE' || c.entity_count >= 5);
    }
    if (activeTab === 'UNRESOLVED') {
      return rawItems.filter(c => c.lead_count > 0 || c.status === 'OPEN');
    }
    return rawItems;
  }, [rawItems, activeTab]);

  const needsAttentionCount = useMemo(() => {
    return rawItems.filter(c => c.priority === 'CRITICAL' || c.status === 'OPEN' || c.lead_count > 2).length;
  }, [rawItems]);

  const crossCaseConnectionsCount = useMemo(() => {
    return rawItems.filter(c => c.case_type === 'MULTI_CASE' || c.entity_count >= 5).length;
  }, [rawItems]);

  const unresolvedLeadsCount = useMemo(() => {
    return rawItems.reduce((sum, c) => sum + (c.lead_count || 0), 0);
  }, [rawItems]);

  const hasActiveFilters = Boolean(
    activeSearch || caseTypeFilter || statusFilter || priorityFilter || jurisdictionFilter || provenanceFilter || activeTab !== 'ALL'
  );

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setActiveSearch(searchInput);
    setPage(1);
  }

  function handleCaseSelect(caseId: string) {
    setSelectedCaseId(caseId);
  }

  function handleOpenCaseWorkspace(caseId: string) {
    setSelectedCaseId(caseId);
    navigate(`/cases/${caseId}`);
  }

  function clearAllFilters() {
    setSearchInput('');
    setActiveSearch('');
    setActiveTab('ALL');
    setCaseTypeFilter('');
    setStatusFilter('');
    setPriorityFilter('');
    setJurisdictionFilter('');
    setProvenanceFilter('');
    setPage(1);
  }

  const selectCls =
    'bg-civix-bg border border-civix-border rounded-sm px-3 py-1 text-xs text-civix-text-primary font-mono focus:outline-none focus:border-civix-blue transition-colors cursor-pointer';

  return (
    <div className="space-y-3 font-mono select-none">
      {/* ── UNIFIED COMMAND CENTER HERO BANNER SECTION ───────────────────────── */}
      <div className="relative bg-civix-surface/40 border border-civix-border/80 p-4 rounded-lg overflow-hidden shadow-2xl shadow-black/60 group space-y-3">
        {/* Widescreen Banner Background Image (High clarity & vivid contrast) */}
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-75 transition-transform duration-1000 ease-out group-hover:scale-105 pointer-events-none"
          style={{ backgroundImage: "url('/assets/command_center_banner.png')" }}
        />
        
        {/* High-Tech Tactical Lightweight Gradients & Cyber Grid Watermark */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#070B12]/60 via-transparent to-[#070B12]/60 pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(#38BDF8_1px,transparent_1px)] [background-size:24px_24px] opacity-15 pointer-events-none" />
        <div className="absolute inset-0 bg-gradient-to-b from-civix-blue/10 via-transparent to-black/70 pointer-events-none" />

        {/* Ambient Top Glow Line */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-civix-blue to-transparent opacity-90" />

        {/* ── 1. Header Row (Title, Crest, Counters & Clock) ────────────────────── */}
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-1 border-b border-civix-border/40">
          <div className="flex items-center space-x-3.5">
            {/* Crest Emblem Badge */}
            <div className="hidden sm:flex items-center justify-center w-11 h-11 rounded-lg bg-[#070B14]/65 border border-civix-blue/40 shadow-[0_0_15px_rgba(56,189,248,0.2)] p-1.5 backdrop-blur-md shrink-0">
              <img 
                src="/assets/delhi_police_crest.png" 
                alt="Delhi Police Crest" 
                className="w-full h-full object-contain filter drop-shadow" 
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            </div>

            <div>
              <div className="flex items-center space-x-2 text-[10px] font-mono font-bold text-civix-text-muted tracking-widest uppercase mb-0.5">
                <span className="text-civix-text-muted">Home</span>
                <span className="text-civix-blue/60">&gt;</span>
                <span className="text-civix-blue-light font-extrabold tracking-wider">Case Registry</span>
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-civix-green animate-pulse ml-1" title="System Live" />
              </div>
              <h1 className="text-xl font-extrabold text-civix-text-primary tracking-tight uppercase flex items-center space-x-2 font-mono">
                <span className="bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent drop-shadow-sm">
                  CASE INTELLIGENCE DELHI NCR
                </span>
              </h1>
              <p className="text-[11px] text-civix-text-muted font-mono mt-0.5">
                <span className="text-civix-blue-light font-bold">Investigate. Correlate. Resolve.</span>
              </p>
            </div>
          </div>

          {/* Right side: Top aggregate counters & IST Clock */}
          <div className="flex items-center gap-2.5 overflow-x-auto py-0.5">
            <div className="bg-[#070B14]/65 backdrop-blur-md border border-civix-border/70 px-3.5 py-1.5 rounded-md text-center min-w-[90px] shadow-sm hover:border-civix-border transition-colors">
              <p className="text-[8px] font-mono font-bold text-civix-text-muted uppercase tracking-wider">TOTAL CASES</p>
              <p className="text-lg font-mono font-extrabold text-civix-text-primary">{summary?.total_cases ?? '268'}</p>
            </div>
            <div className="bg-[#070B14]/65 backdrop-blur-md border border-civix-green/30 px-3.5 py-1.5 rounded-md text-center min-w-[90px] shadow-[0_0_12px_rgba(34,197,94,0.08)] hover:border-civix-green/50 transition-colors">
              <p className="text-[8px] font-mono font-bold text-civix-green uppercase tracking-wider">ACTIVE</p>
              <p className="text-lg font-mono font-extrabold text-civix-green">{summary?.active_cases ?? '207'}</p>
            </div>
            <div className="bg-[#070B14]/65 backdrop-blur-md border border-civix-red/30 px-3.5 py-1.5 rounded-md text-center min-w-[90px] shadow-[0_0_12px_rgba(239,68,68,0.08)] hover:border-civix-red/50 transition-colors">
              <p className="text-[8px] font-mono font-bold text-civix-red uppercase tracking-wider">CRITICAL</p>
              <p className="text-lg font-mono font-extrabold text-civix-red">{summary?.critical_cases ?? '27'}</p>
            </div>
            <div className="bg-[#070B14]/65 backdrop-blur-md border border-civix-blue/30 px-3.5 py-1.5 rounded-md text-center min-w-[90px] shadow-[0_0_12px_rgba(56,189,248,0.08)] hover:border-civix-blue/50 transition-colors">
              <p className="text-[8px] font-mono font-bold text-civix-blue-light uppercase tracking-wider">CONNECTED</p>
              <p className="text-lg font-mono font-extrabold text-civix-blue-light">{crossCaseConnectionsCount || '32'}</p>
            </div>

            {/* Live IST Clock & Weather */}
            <div className="hidden xl:flex flex-col text-right pl-3 border-l border-civix-border/70 text-[10px] text-civix-text-muted">
              <span className="font-bold text-civix-text-primary">Tuesday, 02 September 2026</span>
              <span className="text-sm font-extrabold text-civix-blue-light font-mono leading-none my-0.5 drop-shadow-[0_0_8px_rgba(56,189,248,0.3)]">
                13:42 <span className="text-[9px] font-normal text-civix-text-muted">IST</span>
              </span>
              <span className="text-[9px] text-civix-text-secondary font-mono">31°C New Delhi</span>
            </div>
          </div>
        </div>

        {/* ── 2. Glassmorphic Search & Filter Command Bar ────────────────────────── */}
        <div className="relative z-10 bg-[#070B14]/55 backdrop-blur-md border border-civix-border/50 p-2.5 rounded-md shadow-inner">
          <form onSubmit={handleSearchSubmit} className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-2.5">
            {/* Main Search Input */}
            <div className="relative flex-1 flex items-center">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-civix-text-muted" />
                <input
                  type="text"
                  placeholder="Search by case ID, title, person, vehicle, phone, IMEI, location, evidence, FIR..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  className="w-full pl-8 pr-7 py-1.5 bg-civix-bg/80 border border-civix-border/80 rounded-l-sm text-xs text-civix-text-primary placeholder-civix-text-muted focus:outline-none focus:border-civix-blue font-mono transition-colors shadow-inner"
                />
                {searchInput && (
                  <button
                    type="button"
                    onClick={() => { setSearchInput(''); setActiveSearch(''); setPage(1); }}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-civix-text-muted hover:text-civix-text-primary"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>
              <button
                type="submit"
                className="civix-btn-primary py-1.5 px-4 text-xs font-mono font-bold rounded-l-none rounded-r-sm flex items-center space-x-1 shadow-md"
              >
                <Search className="w-3.5 h-3.5" />
                <span>Search</span>
              </button>
            </div>

            {/* Quick Selectors */}
            <div className="flex flex-wrap items-center gap-1.5">
              <select value={caseTypeFilter} onChange={(e) => { setCaseTypeFilter(e.target.value); setPage(1); }} className={selectCls}>
                <option value="">All Types</option>
                {CASE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>

              <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className={selectCls}>
                <option value="">All Status</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="OPEN">OPEN</option>
                <option value="CLOSED_SOLVED">CLOSED SOLVED</option>
                <option value="CLOSED_UNSOLVED">CLOSED UNSOLVED</option>
              </select>

              <select value={priorityFilter} onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }} className={selectCls}>
                <option value="">All Priority</option>
                {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>

              <select value={jurisdictionFilter} onChange={(e) => { setJurisdictionFilter(e.target.value); setPage(1); }} className={selectCls}>
                <option value="">All Jurisdiction</option>
                <option value="Delhi West">Delhi West</option>
                <option value="Delhi South-West">Delhi South-West</option>
                <option value="Delhi Central">Delhi Central</option>
                <option value="North West">North West</option>
              </select>

              {hasActiveFilters && (
                <button
                  type="button"
                  onClick={clearAllFilters}
                  className="flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold text-civix-text-muted bg-civix-surface-3 border border-civix-border rounded-sm hover:text-civix-text-primary transition-colors font-mono"
                >
                  <X className="w-3 h-3" />
                  <span>Reset</span>
                </button>
              )}
            </div>
          </form>
        </div>
      </div>

      {/* ── 2-COLUMN SPLIT LAYOUT: POSTGIS MAP ON LEFT, CASE REGISTRY DATA GRID ON RIGHT ──── */}
      <div className="flex flex-col lg:flex-row items-start gap-3.5">
        {/* Left Column: PostGIS Spatial Map (w-full lg:w-5/12 xl:w-5/12) */}
        <div className="w-full lg:w-5/12 xl:w-5/12 shrink-0">
          <CaseRegistryMap
            cases={spatialCases}
            selectedCaseId={selectedCaseId}
            onSelectCase={handleCaseSelect}
            onOpenCaseWorkspace={handleOpenCaseWorkspace}
            totalCaseCount={summary?.total_cases ?? 268}
          />
        </div>

        {/* Right Column: Category Tabs & Case Data Grid Table (w-full lg:w-7/12 xl:w-7/12) */}
        <div className="w-full lg:w-7/12 xl:w-7/12 font-mono flex flex-col justify-between h-[440px]">
          {/* Category Filter Pills & Sorting Toolbar */}
          <div className="bg-civix-surface/80 border border-civix-border/80 p-1.5 rounded-md flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-1.5 shadow-md shrink-0 mb-1">
            <div className="flex items-center gap-1 overflow-x-auto pb-0.5 scrollbar-none">
              {[
                { id: 'ACTIVE', label: 'Active', count: summary?.active_cases ?? 207 },
                { id: 'CONNECTED', label: 'Connected', count: crossCaseConnectionsCount || 32 },
                { id: 'CRITICAL', label: 'Critical', count: summary?.critical_cases ?? 27 },
                { id: 'NEEDS_ATTENTION', label: 'Needs Attention', count: needsAttentionCount || 48 },
                { id: 'UNRESOLVED', label: 'Unresolved', count: unresolvedLeadsCount || 58 },
                { id: 'ALL', label: 'All Cases', count: summary?.total_cases ?? 268 },
              ].map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => { setActiveTab(tab.id as TabCategory); setPage(1); }}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-semibold flex items-center space-x-1 transition-all border whitespace-nowrap ${
                      isActive
                        ? 'border-civix-blue text-civix-blue-light bg-civix-blue/20 font-bold shadow-[0_0_10px_rgba(56,189,248,0.15)]'
                        : 'border-transparent text-civix-text-secondary hover:text-civix-text-primary hover:bg-civix-surface-2'
                    }`}
                  >
                    <span>{tab.label}</span>
                    {tab.count !== undefined && (
                      <span className={`text-[9px] px-1.5 py-0.1 rounded-full font-mono font-extrabold ${
                        isActive ? 'bg-civix-blue text-white shadow-sm' : 'bg-civix-surface-3 text-civix-text-muted'
                      }`}>
                        {tab.count}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="flex items-center space-x-1.5 text-[11px] font-mono text-civix-text-muted shrink-0">
              <span className="text-civix-text-muted">Sort:</span>
              <select
                value={`${sortBy}:${sortOrder}`}
                onChange={(e) => {
                  const [sb, so] = e.target.value.split(':');
                  setSortBy(sb);
                  setSortOrder(so);
                  setPage(1);
                }}
                className="bg-civix-bg border border-civix-border rounded-sm px-2 py-0.5 text-[11px] text-civix-text-primary font-mono focus:outline-none focus:border-civix-blue cursor-pointer"
              >
                <option value="last_activity_at:desc">Newest</option>
                <option value="last_activity_at:asc">Oldest</option>
                <option value="priority:desc">Priority</option>
                <option value="case_number:asc">Case ID</option>
              </select>
            </div>
          </div>

          {/* Main Data Grid Table (Compacted to 6 columns - 0 horizontal scroll needed!) */}
          <div className="bg-civix-surface/80 border border-civix-border/80 rounded-md overflow-hidden shadow-xl flex-1 flex flex-col min-h-0">
            {/* Loading State */}
            {isRegistryLoading && (
              <div className="flex items-center justify-center py-20 space-x-3 text-civix-text-muted">
                <Loader2 className="w-6 h-6 animate-spin text-civix-blue-light" />
                <span className="text-xs font-mono">Querying PostgreSQL Case Registry...</span>
              </div>
            )}

            {/* Error State */}
            {!isRegistryLoading && registryError && (
              <div className="py-12 text-center space-y-3">
                <AlertTriangle className="w-8 h-8 text-civix-red mx-auto" />
                <div>
                  <p className="text-xs font-bold text-civix-text-primary uppercase tracking-wide font-mono">Unable to Load Case Registry</p>
                  <p className="text-[10px] text-civix-text-muted mt-1 font-mono">Database query failed. Please verify API server state.</p>
                </div>
                <button onClick={() => refetchRegistry()} className="inline-flex items-center space-x-2 civix-btn-primary py-1 text-xs font-mono font-bold">
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry</span>
                </button>
              </div>
            )}

            {/* Empty State */}
            {!isRegistryLoading && !registryError && items.length === 0 && (
              <div className="py-12 text-center space-y-2">
                <Briefcase className="w-7 h-7 text-civix-text-muted mx-auto" />
                <p className="text-xs font-semibold text-civix-text-secondary font-mono">No investigations match the current filter criteria.</p>
                <button onClick={clearAllFilters} className="text-xs text-civix-blue-light hover:text-civix-text-primary font-mono underline">
                  Clear all filters
                </button>
              </div>
            )}

            {/* Streamlined 6-Column Data Table with Internal Vertical Scroll ONLY */}
            {!isRegistryLoading && !registryError && items.length > 0 && (
              <div className="overflow-y-auto flex-1 max-h-[330px] scrollbar-thin scrollbar-thumb-civix-border/60">
                <table className="w-full text-xs border-collapse layout-fixed">
                  <thead className="sticky top-0 bg-[#0C1220] border-b border-civix-border text-[9px] font-bold text-civix-text-muted uppercase tracking-widest font-mono z-10 shadow-sm">
                    <tr>
                      <th className="w-7 px-2 py-2 text-center">
                        <input type="checkbox" className="rounded-xs border-civix-border bg-civix-bg text-civix-blue focus:ring-0" />
                      </th>
                      <th className="text-left px-2.5 py-2">CASE ID & TITLE</th>
                      <th className="text-left px-2 py-2 w-[85px]">TYPE</th>
                      <th className="text-left px-2 py-2 w-[80px]">STATUS</th>
                      <th className="text-left px-2 py-2 w-[85px]">PRIORITY</th>
                      <th className="text-center px-2 py-2 w-[100px]">ENTITIES</th>
                      <th className="text-right px-2 py-2 w-[85px]">ACTION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-civix-border-subtle font-mono">
                    {items.map((caseItem) => {
                      const isSelected = caseItem.case_id === selectedCaseId;
                      const statusVar = STATUS_VARIANTS[caseItem.status?.toUpperCase()] || 'default';
                      const priorityVar = PRIORITY_VARIANTS[caseItem.priority?.toUpperCase()] || 'default';

                      return (
                        <tr
                          key={caseItem.case_id}
                          onClick={() => handleCaseSelect(caseItem.case_id)}
                          className={`transition-colors cursor-pointer ${
                            isSelected
                              ? 'bg-civix-blue/15 border-l-4 border-l-civix-blue'
                              : 'hover:bg-civix-surface-3'
                          }`}
                        >
                          {/* Checkbox */}
                          <td className="w-7 px-2 py-2 text-center" onClick={(e) => e.stopPropagation()}>
                            <input type="checkbox" className="rounded-xs border-civix-border bg-civix-bg text-civix-blue focus:ring-0" />
                          </td>

                          {/* CASE ID & TITLE (Stacked cleanly) */}
                          <td className="px-2.5 py-2">
                            <div className="flex flex-col min-w-0">
                              <div className="flex items-center space-x-2">
                                <span className={`font-mono font-extrabold text-[11px] ${isSelected ? 'text-cyan-300' : 'text-amber-400'}`}>
                                  {caseItem.case_number}
                                </span>
                                <span className="text-[9px] text-civix-text-muted">
                                  • {caseItem.last_activity_at ? '4h ago' : 'Today'}
                                </span>
                              </div>
                              <span className="font-bold text-[11px] leading-tight text-civix-text-primary hover:text-civix-blue-light transition-colors font-sans truncate">
                                {caseItem.title}
                              </span>
                              <span className="text-[9px] text-civix-text-muted truncate font-sans">
                                {caseItem.police_station || caseItem.jurisdiction || 'Delhi PS'}
                              </span>
                            </div>
                          </td>

                          {/* TYPE */}
                          <td className="px-2 py-2 whitespace-nowrap">
                            <span className="text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded-xs bg-civix-surface-3 border border-civix-border text-civix-text-secondary">
                              {caseItem.case_type}
                            </span>
                          </td>

                          {/* STATUS */}
                          <td className="px-2 py-2 whitespace-nowrap">
                            <Badge variant={statusVar as any}>{caseItem.status}</Badge>
                          </td>

                          {/* PRIORITY */}
                          <td className="px-2 py-2 whitespace-nowrap">
                            <Badge variant={priorityVar as any}>{caseItem.priority}</Badge>
                          </td>

                          {/* KEY ENTITIES (3 icon stat pills) */}
                          <td className="px-2 py-2 whitespace-nowrap text-center">
                            <div className="flex items-center justify-center space-x-1 text-[9px] font-mono">
                              <div className="flex items-center space-x-0.5 bg-civix-surface-2 border border-civix-border px-1 py-0.5 rounded-xs text-civix-blue-light" title="Linked Persons">
                                <Users className="w-2.5 h-2.5" />
                                <span className="font-bold">{caseItem.person_count ?? caseItem.entity_count ?? 0}</span>
                              </div>
                              <div className="flex items-center space-x-0.5 bg-civix-surface-2 border border-civix-border px-1 py-0.5 rounded-xs text-civix-gold" title="Linked Vehicles">
                                <Car className="w-2.5 h-2.5" />
                                <span className="font-bold">{caseItem.vehicle_count ?? 0}</span>
                              </div>
                              <div className="flex items-center space-x-0.5 bg-civix-surface-2 border border-civix-border px-1 py-0.5 rounded-xs text-civix-green" title="Evidence Artifacts">
                                <FileText className="w-2.5 h-2.5" />
                                <span className="font-bold">{caseItem.evidence_count || 0}</span>
                              </div>
                            </div>
                          </td>

                          {/* ACTIONS (Open -> button ALWAYS 100% visible with 0 horizontal scroll!) */}
                          <td className="px-2 py-2 whitespace-nowrap text-right">
                            <div className="flex items-center justify-end space-x-1">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleOpenCaseWorkspace(caseItem.case_id);
                                }}
                                className="civix-btn-primary py-1 px-2 text-[10px] font-mono font-bold flex items-center space-x-0.5 shadow-sm"
                              >
                                <span>Open →</span>
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination Footer */}
            {pagination && pagination.total_pages > 1 && (
              <div className="px-3 py-1.5 bg-civix-surface-2 border-t border-civix-border flex items-center justify-between gap-2 text-[10px] font-mono shrink-0">
                <div className="text-civix-text-muted truncate">
                  <strong className="text-civix-text-primary">{(page - 1) * pageSize + 1}</strong>-
                  <strong className="text-civix-text-primary">{Math.min(page * pageSize, pagination.total)}</strong> of{' '}
                  <strong className="text-civix-text-primary">{pagination.total}</strong>
                </div>

                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-2 py-0.5 bg-civix-surface border border-civix-border rounded-sm hover:bg-civix-surface-3 disabled:opacity-40 disabled:cursor-not-allowed text-civix-text-primary transition-colors"
                  >
                    <ChevronLeft className="w-3 h-3" />
                  </button>

                  {Array.from({ length: Math.min(5, pagination.total_pages) }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      onClick={() => setPage(p)}
                      className={`px-2 py-0.5 rounded-sm text-[10px] font-mono font-bold transition-colors ${
                        page === p
                          ? 'bg-civix-blue text-white border border-civix-blue'
                          : 'bg-civix-surface border border-civix-border text-civix-text-secondary hover:bg-civix-surface-3'
                      }`}
                    >
                      {p}
                    </button>
                  ))}

                  <button
                    onClick={() => setPage(p => Math.min(pagination.total_pages, p + 1))}
                    disabled={page === pagination.total_pages}
                    className="px-2 py-0.5 bg-civix-surface border border-civix-border rounded-sm hover:bg-civix-surface-3 disabled:opacity-40 disabled:cursor-not-allowed text-civix-text-primary transition-colors"
                  >
                    <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
