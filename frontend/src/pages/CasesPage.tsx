import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { casesApi } from '../api/cases';
import { useCaseSelection } from '../context/CaseSelectionContext';
import type { CaseRegistryItem, CaseRegistryResponse, CaseCreateRequest } from '../types/api';
import { Panel } from '../components/ui/Panel';
import { Badge } from '../components/ui/Badge';
import {
  Search,
  Plus,
  Briefcase,
  AlertTriangle,
  RefreshCw,
  ChevronRight,
  X,
  Loader2,
  CheckCircle2,
  Users,
  FileText
} from 'lucide-react';

// ── Badge mappings ──────────────────────────────────────────────────────────

const STATUS_VARIANTS: Record<string, string> = {
  OPEN: 'active',
  ACTIVE: 'confirmed',
  CLOSED_SOLVED: 'closed',
  CLOSED_UNSOLVED: 'closed',
  CLOSED: 'closed',
  ARCHIVED: 'deferred',
  SUSPENDED: 'warning',
};

const PRIORITY_VARIANTS: Record<string, string> = {
  HIGH: 'critical',
  CRITICAL: 'critical',
  MEDIUM: 'warning',
  LOW: 'default',
};

// ── Time helper ──────────────────────────────────────────────────────────────

function formatRelativeTime(dateString: string): string {
  if (!dateString) return 'Unknown';
  const now = new Date();
  const past = new Date(dateString);
  const diffMs = Math.max(0, now.getTime() - past.getTime());
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 30) return `${diffDays} days ago`;
  return past.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatDateFormatted(dateString: string): string {
  if (!dateString) return '';
  const d = new Date(dateString);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) + 
    ', ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

// ── Types ─────────────────────────────────────────────────────────────────────

type TabCategory = 'ALL' | 'ACTIVE' | 'CRITICAL' | 'FINANCIAL' | 'PROPERTY' | 'INTELLIGENCE' | 'SURVEILLANCE' | 'UNRESOLVED';

// ── New Case Modal ────────────────────────────────────────────────────────────

interface NewCaseModalProps {
  onClose: () => void;
  onSuccess: (newCaseId: string) => void;
}

const CASE_TYPES = ['CRIMINAL', 'FINANCIAL', 'FORENSIC', 'INTELLIGENCE', 'MULTI_CASE', 'PROPERTY', 'SURVEILLANCE'];
const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

const NewCaseModal: React.FC<NewCaseModalProps> = ({ onClose, onSuccess }) => {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<CaseCreateRequest>({
    case_number: '',
    title: '',
    case_type: 'CRIMINAL',
    jurisdiction: '',
    priority: 'MEDIUM',
    investigating_unit: '',
  });
  const [formError, setFormError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (data: CaseCreateRequest) => casesApi.createCase(data),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['cases-registry'] });
      onSuccess(result.case_id);
    },
    onError: (err: Error) => {
      setFormError(err.message || 'Failed to create case. Please try again.');
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!form.case_number.trim()) return setFormError('Case number is required.');
    if (!form.title.trim()) return setFormError('Case title is required.');
    if (!form.jurisdiction.trim()) return setFormError('Jurisdiction is required.');
    mutation.mutate({
      ...form,
      investigating_unit: form.investigating_unit?.trim() || undefined,
    });
  }

  const inputCls = 'w-full bg-civix-bg border border-civix-border rounded-sm px-3 py-2 text-xs font-mono text-civix-text-primary placeholder-civix-text-muted focus:outline-none focus:border-civix-blue transition-colors disabled:opacity-50';
  const labelCls = 'block text-[10px] font-bold text-civix-text-muted uppercase tracking-widest mb-1 font-mono';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 bg-civix-surface border border-civix-border rounded-sm shadow-civix-lg w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-5 py-4 border-b border-civix-border bg-civix-surface-2">
          <div className="flex items-center space-x-2">
            <Briefcase className="w-4 h-4 text-civix-gold" />
            <h2 className="text-sm font-bold text-civix-text-primary uppercase tracking-wide font-mono">
              Open New Investigation
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-civix-text-muted hover:text-civix-text-primary hover:bg-civix-surface-3 rounded-sm transition-colors"
            disabled={mutation.isPending}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label htmlFor="nc-case-number" className={labelCls}>
              Case Number <span className="text-civix-red">*</span>
            </label>
            <input
              id="nc-case-number"
              type="text"
              placeholder="e.g. CASE-2026-0143"
              value={form.case_number}
              onChange={(e) => setForm((f) => ({ ...f, case_number: e.target.value }))}
              className={inputCls}
              required
              disabled={mutation.isPending}
            />
          </div>

          <div>
            <label htmlFor="nc-title" className={labelCls}>
              Investigation Title <span className="text-civix-red">*</span>
            </label>
            <input
              id="nc-title"
              type="text"
              placeholder="Brief operational case title"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              className={inputCls}
              required
              disabled={mutation.isPending}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="nc-case-type" className={labelCls}>Case Type</label>
              <select
                id="nc-case-type"
                value={form.case_type}
                onChange={(e) => setForm((f) => ({ ...f, case_type: e.target.value }))}
                className={inputCls}
                disabled={mutation.isPending}
              >
                {CASE_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="nc-priority" className={labelCls}>Priority</label>
              <select
                id="nc-priority"
                value={form.priority}
                onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
                className={inputCls}
                disabled={mutation.isPending}
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="nc-jurisdiction" className={labelCls}>
              Jurisdiction <span className="text-civix-red">*</span>
            </label>
            <input
              id="nc-jurisdiction"
              type="text"
              placeholder="e.g. North-West Delhi, Dwarka, National"
              value={form.jurisdiction}
              onChange={(e) => setForm((f) => ({ ...f, jurisdiction: e.target.value }))}
              className={inputCls}
              required
              disabled={mutation.isPending}
            />
          </div>

          <div>
            <label htmlFor="nc-unit" className={labelCls}>
              Investigating Unit <span className="text-civix-text-muted font-normal">(optional)</span>
            </label>
            <input
              id="nc-unit"
              type="text"
              placeholder="e.g. Delhi NCR Cyber Crime Cell"
              value={form.investigating_unit}
              onChange={(e) => setForm((f) => ({ ...f, investigating_unit: e.target.value }))}
              className={inputCls}
              disabled={mutation.isPending}
            />
          </div>

          {formError && (
            <div className="flex items-start space-x-2 bg-civix-red-subtle border border-civix-red-muted rounded-sm p-3">
              <AlertTriangle className="w-3.5 h-3.5 text-civix-red flex-shrink-0 mt-0.5" />
              <span className="text-xs text-civix-red-light">{formError}</span>
            </div>
          )}

          <div className="flex items-center justify-end space-x-3 pt-2 border-t border-civix-border">
            <button
              type="button"
              onClick={onClose}
              disabled={mutation.isPending}
              className="civix-btn-secondary disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="civix-btn-primary flex items-center space-x-2 disabled:opacity-50"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Opening...</span>
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5" />
                  <span>Open Investigation</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ── Main CasesPage ────────────────────────────────────────────────────────────

export const CasesPage: React.FC = () => {
  const navigate = useNavigate();
  const { selectedCaseId, setSelectedCaseId } = useCaseSelection();

  // Filter & Query parameters
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<TabCategory>('ALL');
  const [caseTypeFilter, setCaseTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [jurisdictionFilter, setJurisdictionFilter] = useState('');
  const [provenanceFilter, setProvenanceFilter] = useState('');
  const [sortBy, setSortBy] = useState('last_activity_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [showNewCaseModal, setShowNewCaseModal] = useState(false);
  const [newCaseSuccess, setNewCaseSuccess] = useState<string | null>(null);

  // Compute effective query parameters based on tab + selected filters
  const effectiveParams = React.useMemo(() => {
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
      search: search.trim() || undefined,
      case_type: type || undefined,
      status: stat || undefined,
      priority: prio || undefined,
      jurisdiction: jurisdictionFilter.trim() || undefined,
      provenance: provenanceFilter || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    };
  }, [page, pageSize, search, activeTab, caseTypeFilter, statusFilter, priorityFilter, jurisdictionFilter, provenanceFilter, sortBy, sortOrder]);

  const { data: registryResponse, isLoading, error, refetch, isFetching } = useQuery<CaseRegistryResponse>({
    queryKey: ['cases-registry', effectiveParams],
    queryFn: () => casesApi.getRegistry(effectiveParams),
    staleTime: 15_000,
  });

  const summary = registryResponse?.summary;
  const items = registryResponse?.items || [];
  const pagination = registryResponse?.pagination;

  const hasActiveFilters = search || caseTypeFilter || statusFilter || priorityFilter || jurisdictionFilter || provenanceFilter || activeTab !== 'ALL';

  function handleCaseSelect(caseItem: CaseRegistryItem) {
    setSelectedCaseId(caseItem.case_id);
  }

  function handleCaseOpen(caseId: string) {
    setSelectedCaseId(caseId);
    navigate(`/cases/${caseId}`);
  }

  function handleNewCaseSuccess(newCaseId: string) {
    setShowNewCaseModal(false);
    setNewCaseSuccess(newCaseId);
    setSelectedCaseId(newCaseId);
    setTimeout(() => setNewCaseSuccess(null), 4000);
  }

  function clearAllFilters() {
    setSearch('');
    setActiveTab('ALL');
    setCaseTypeFilter('');
    setStatusFilter('');
    setPriorityFilter('');
    setJurisdictionFilter('');
    setProvenanceFilter('');
    setPage(1);
  }

  const selectCls = 'bg-civix-bg border border-civix-border rounded-sm px-2.5 py-1.5 text-xs text-civix-text-primary font-mono focus:outline-none focus:border-civix-blue transition-colors';

  return (
    <div className="space-y-4">
      {/* ── Top Header & Summary Banner ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-civix-surface border border-civix-border p-4 rounded-sm">
        <div>
          <h1 className="text-xl font-extrabold text-civix-text-primary tracking-tight uppercase flex items-center space-x-2 font-mono">
            <span>CASES</span>
          </h1>
          <p className="text-xs text-civix-text-muted font-mono mt-0.5">
            Case Registry &amp; Investigation Management — Monitor. Investigate. Connect the Dots.
          </p>
        </div>

        {/* Summary Stats Cards */}
        <div className="flex items-center gap-4 border-l border-civix-border pl-4 overflow-x-auto py-1">
          <div className="text-center px-2">
            <p className="text-[10px] font-mono font-bold text-civix-text-muted uppercase tracking-wider">Total Cases</p>
            <p className="text-lg font-mono font-extrabold text-civix-text-primary">{summary?.total_cases ?? '...'}</p>
          </div>
          <div className="text-center px-2 border-l border-civix-border-subtle">
            <p className="text-[10px] font-mono font-bold text-civix-text-muted uppercase tracking-wider">Synthetic Benchmark</p>
            <p className="text-lg font-mono font-extrabold text-civix-blue-light">{summary?.synthetic_cases ?? '...'}</p>
          </div>
          <div className="text-center px-2 border-l border-civix-border-subtle">
            <p className="text-[10px] font-mono font-bold text-civix-gold uppercase tracking-wider">Golden Cases</p>
            <p className="text-lg font-mono font-extrabold text-civix-gold">{summary?.golden_cases ?? '...'}</p>
          </div>
          <div className="text-center px-2 border-l border-civix-border-subtle">
            <p className="text-[10px] font-mono font-bold text-civix-green uppercase tracking-wider">Active</p>
            <p className="text-lg font-mono font-extrabold text-civix-green">{summary?.active_cases ?? '...'}</p>
          </div>
          <div className="text-center px-2 border-l border-civix-border-subtle">
            <p className="text-[10px] font-mono font-bold text-civix-red uppercase tracking-wider">Critical Priority</p>
            <p className="text-lg font-mono font-extrabold text-civix-red">{summary?.critical_cases ?? '...'}</p>
          </div>
          <div className="text-center px-2 border-l border-civix-border-subtle">
            <p className="text-[10px] font-mono font-bold text-civix-text-secondary uppercase tracking-wider">Updated Today</p>
            <p className="text-lg font-mono font-extrabold text-civix-text-primary">{summary?.updated_today ?? '...'}</p>
          </div>
        </div>
      </div>

      {/* Success Banner */}
      {newCaseSuccess && (
        <div className="flex items-center space-x-2 bg-civix-green-subtle border border-civix-green-muted text-civix-green text-xs font-semibold px-4 py-2.5 rounded-sm">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>Investigation opened. Case ID: <span className="font-mono text-civix-text-mono">{newCaseSuccess}</span></span>
        </div>
      )}

      {/* ── Toolbar: Search & Selectors ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-civix-surface-2 border border-civix-border p-3 rounded-sm">
        <div className="flex flex-wrap items-center gap-2 flex-1">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[220px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-civix-text-muted" />
            <input
              id="cases-search"
              type="text"
              placeholder="Search cases, title, jurisdiction, entities, vehicles, IMEI..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-8 py-1.5 bg-civix-bg border border-civix-border rounded-sm text-xs text-civix-text-primary placeholder-civix-text-muted focus:outline-none focus:border-civix-blue transition-colors font-mono"
            />
            {search && (
              <button
                onClick={() => { setSearch(''); setPage(1); }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-civix-text-muted hover:text-civix-text-primary transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Quick Dropdown Filters */}
          <select
            value={caseTypeFilter}
            onChange={(e) => { setCaseTypeFilter(e.target.value); setPage(1); }}
            className={selectCls}
          >
            <option value="">All Types</option>
            {CASE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className={selectCls}
          >
            <option value="">All Status</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="OPEN">OPEN</option>
            <option value="CLOSED_SOLVED">CLOSED SOLVED</option>
            <option value="CLOSED_UNSOLVED">CLOSED UNSOLVED</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
            className={selectCls}
          >
            <option value="">All Priority</option>
            {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>

          <select
            value={provenanceFilter}
            onChange={(e) => { setProvenanceFilter(e.target.value); setPage(1); }}
            className={selectCls}
          >
            <option value="">All Provenance</option>
            <option value="GOLDEN">Golden Cases</option>
            <option value="SYNTHETIC">Synthetic Cases</option>
          </select>

          {hasActiveFilters && (
            <button
              onClick={clearAllFilters}
              className="flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold text-civix-text-muted bg-civix-surface-3 border border-civix-border rounded-sm hover:text-civix-text-primary transition-colors font-mono"
            >
              <X className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>

        {/* Right side actions */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center space-x-1.5 civix-btn-secondary py-1.5 text-xs font-mono disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            id="new-case-btn"
            onClick={() => setShowNewCaseModal(true)}
            className="flex items-center space-x-2 civix-btn-primary py-1.5 text-xs font-mono font-bold"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>+ New Case</span>
          </button>
        </div>
      </div>

      {/* ── Category Filter Tabs + Sorting ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between border-b border-civix-border gap-2 pb-1">
        {/* Filter Pills */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1">
          {[
            { id: 'ALL', label: 'All Cases', count: summary?.total_cases },
            { id: 'ACTIVE', label: 'Active', count: summary?.active_cases },
            { id: 'CRITICAL', label: 'Critical', count: summary?.critical_cases },
            { id: 'FINANCIAL', label: 'Financial' },
            { id: 'PROPERTY', label: 'Property' },
            { id: 'INTELLIGENCE', label: 'Intelligence' },
            { id: 'SURVEILLANCE', label: 'Surveillance' },
            { id: 'UNRESOLVED', label: 'Unresolved' },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => { setActiveTab(tab.id as TabCategory); setPage(1); }}
                className={`px-3 py-1.5 rounded-t-sm text-xs font-mono font-semibold flex items-center space-x-1.5 transition-colors border-b-2 whitespace-nowrap ${
                  isActive
                    ? 'border-civix-blue text-civix-blue-light bg-civix-blue-subtle/30 font-bold'
                    : 'border-transparent text-civix-text-secondary hover:text-civix-text-primary hover:bg-civix-surface-2'
                }`}
              >
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${isActive ? 'bg-civix-blue text-white' : 'bg-civix-surface-3 text-civix-text-muted'}`}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Sorting Dropdown */}
        <div className="flex items-center space-x-2 text-xs font-mono text-civix-text-muted py-1">
          <span>Sort by:</span>
          <select
            value={`${sortBy}:${sortOrder}`}
            onChange={(e) => {
              const [sb, so] = e.target.value.split(':');
              setSortBy(sb);
              setSortOrder(so);
              setPage(1);
            }}
            className="bg-civix-bg border border-civix-border rounded-sm px-2 py-1 text-xs text-civix-text-primary font-mono focus:outline-none focus:border-civix-blue"
          >
            <option value="last_activity_at:desc">Last Updated (Newest)</option>
            <option value="last_activity_at:asc">Last Updated (Oldest)</option>
            <option value="priority:desc">Priority (Highest)</option>
            <option value="case_number:asc">Case Number (A-Z)</option>
            <option value="title:asc font-mono">Title (A-Z)</option>
          </select>
        </div>
      </div>

      {/* ── Main Case Registry Table Panel ────────────────────────────────────────── */}
      <Panel
        title="INVESTIGATIVE CASE REGISTRY"
        subtitle="Authoritative cases derived dynamically from PostgreSQL"
        headerAction={
          <span className="text-[10px] font-mono font-bold text-civix-text-muted uppercase tracking-widest">
            {isLoading ? '...' : `Showing ${items.length} of ${pagination?.total ?? 0} cases`}
          </span>
        }
      >
        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-20 space-x-3 text-civix-text-muted">
            <Loader2 className="w-6 h-6 animate-spin text-civix-blue-light" />
            <span className="text-xs font-mono">Querying PostgreSQL Case Registry...</span>
          </div>
        )}

        {/* Error State */}
        {!isLoading && error && (
          <div className="py-16 text-center space-y-3">
            <AlertTriangle className="w-8 h-8 text-civix-red mx-auto" />
            <div>
              <p className="text-sm font-bold text-civix-text-primary uppercase tracking-wide font-mono">Unable to Load Case Registry</p>
              <p className="text-xs text-civix-text-muted mt-1 font-mono">Database query failed. Please verify API server state.</p>
            </div>
            <button onClick={() => refetch()} className="inline-flex items-center space-x-2 civix-btn-primary py-1.5 text-xs font-mono font-bold">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && items.length === 0 && (
          <div className="py-16 text-center space-y-3">
            <Briefcase className="w-8 h-8 text-civix-text-muted mx-auto" />
            <p className="text-sm font-semibold text-civix-text-secondary font-mono">No investigations match the current filter criteria.</p>
            <button
              onClick={clearAllFilters}
              className="text-xs text-civix-blue-light hover:text-civix-text-primary transition-colors font-mono underline"
            >
              Clear all filters
            </button>
          </div>
        )}

        {/* Table View */}
        {!isLoading && !error && items.length > 0 && (
          <div className="overflow-x-auto -m-4">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-civix-surface-2 border-b border-civix-border text-[9px] font-bold text-civix-text-muted uppercase tracking-widest font-mono">
                  <th className="text-left px-4 py-3">CASE ID</th>
                  <th className="text-left px-4 py-3">TITLE / SUBJECT</th>
                  <th className="text-left px-4 py-3">TYPE</th>
                  <th className="text-left px-4 py-3">STATUS</th>
                  <th className="text-left px-4 py-3">PRIORITY</th>
                  <th className="text-left px-4 py-3">JURISDICTION</th>
                  <th className="text-left px-4 py-3">LAST ACTIVITY</th>
                  <th className="text-center px-4 py-3">ENTITIES</th>
                  <th className="text-center px-4 py-3">EVIDENCE</th>
                  <th className="text-right px-4 py-3">ACTIONS</th>
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
                      id={`case-row-${caseItem.case_id}`}
                      onClick={() => handleCaseSelect(caseItem)}
                      className={`transition-colors cursor-pointer ${
                        isSelected
                          ? 'bg-civix-blue-subtle/40 border-l-2 border-l-civix-blue'
                          : 'hover:bg-civix-surface-3'
                      }`}
                    >
                      {/* Case ID + Provenance Badge */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex flex-col space-y-1">
                          <span className={`font-mono font-extrabold text-xs ${isSelected ? 'text-civix-blue-light' : 'text-civix-text-mono'}`}>
                            {caseItem.case_number}
                          </span>
                          <span className={`inline-block text-[8px] font-mono font-bold px-1.5 py-0.2 rounded-xs tracking-wider w-max ${
                            caseItem.provenance === 'GOLDEN' 
                              ? 'bg-civix-gold/20 text-civix-gold border border-civix-gold/40' 
                              : 'bg-civix-blue/15 text-civix-blue-light border border-civix-blue/30'
                          }`}>
                            {caseItem.provenance}
                          </span>
                        </div>
                      </td>

                      {/* Title / Subject & Description */}
                      <td className="px-4 py-3 max-w-[280px]">
                        <div className="flex flex-col">
                          <span className="font-bold text-xs leading-snug text-civix-text-primary hover:text-civix-blue-light transition-colors font-sans">
                            {caseItem.title}
                          </span>
                          {caseItem.description && (
                            <span className="text-[10px] text-civix-text-muted truncate mt-0.5 font-sans">
                              {caseItem.description}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Case Type */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-xs bg-civix-surface-3 border border-civix-border text-civix-text-secondary">
                          {caseItem.case_type}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <Badge variant={statusVar as any}>{caseItem.status}</Badge>
                      </td>

                      {/* Priority */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <Badge variant={priorityVar as any}>{caseItem.priority}</Badge>
                      </td>

                      {/* Jurisdiction & Police Station */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-civix-text-primary font-sans">
                            {caseItem.police_station}
                          </span>
                          <span className="text-[10px] text-civix-text-muted font-sans">
                            {caseItem.jurisdiction}
                          </span>
                        </div>
                      </td>

                      {/* Last Activity */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-civix-text-primary font-mono">
                            {formatRelativeTime(caseItem.last_activity_at)}
                          </span>
                          <span className="text-[9px] text-civix-text-muted font-mono">
                            {formatDateFormatted(caseItem.last_activity_at)}
                          </span>
                        </div>
                      </td>

                      {/* Entities Count */}
                      <td className="px-4 py-3 text-center whitespace-nowrap">
                        <div className="inline-flex items-center space-x-1.5 bg-civix-surface-3 px-2 py-1 rounded-sm border border-civix-border">
                          <Users className="w-3 h-3 text-civix-blue-light" />
                          <span className="font-mono font-bold text-xs text-civix-text-primary">{caseItem.entity_count}</span>
                        </div>
                      </td>

                      {/* Evidence Count */}
                      <td className="px-4 py-3 text-center whitespace-nowrap">
                        <div className="inline-flex items-center space-x-1.5 bg-civix-surface-3 px-2 py-1 rounded-sm border border-civix-border">
                          <FileText className="w-3 h-3 text-civix-gold" />
                          <span className="font-mono font-bold text-xs text-civix-text-primary">{caseItem.evidence_count}</span>
                        </div>
                      </td>

                      {/* Action / Open Button */}
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <button
                          id={`open-case-${caseItem.case_id}`}
                          onClick={(e) => { e.stopPropagation(); handleCaseOpen(caseItem.case_id); }}
                          className="inline-flex items-center space-x-1 px-2.5 py-1 text-[10px] font-bold text-civix-text-secondary bg-civix-surface-3 border border-civix-border rounded-sm hover:bg-civix-blue hover:text-white hover:border-civix-blue-dark transition-colors font-mono"
                        >
                          <span>Open</span>
                          <ChevronRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Pagination Controls */}
            {pagination && pagination.total > 0 && (
              <div className="px-4 py-3 border-t border-civix-border flex flex-col sm:flex-row items-center justify-between bg-civix-surface-2 gap-3 font-mono text-xs">
                <span className="text-civix-text-muted text-[11px]">
                  Showing {Math.min((pagination.page - 1) * pagination.page_size + 1, pagination.total)}–{Math.min(pagination.page * pagination.page_size, pagination.total)} of {pagination.total} cases
                </span>

                <div className="flex items-center space-x-1">
                  <button
                    disabled={pagination.page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="px-2.5 py-1 bg-civix-surface border border-civix-border rounded-sm disabled:opacity-40 hover:bg-civix-surface-3 transition-colors"
                  >
                    &lt;
                  </button>

                  {Array.from({ length: Math.min(6, pagination.total_pages) }, (_, i) => i + 1).map((pNum) => (
                    <button
                      key={pNum}
                      onClick={() => setPage(pNum)}
                      className={`px-2.5 py-1 rounded-sm border font-bold transition-colors ${
                        pagination.page === pNum
                          ? 'bg-civix-blue text-white border-civix-blue'
                          : 'bg-civix-surface border-civix-border text-civix-text-secondary hover:bg-civix-surface-3'
                      }`}
                    >
                      {pNum}
                    </button>
                  ))}

                  {pagination.total_pages > 6 && (
                    <span className="px-1 text-civix-text-muted">...</span>
                  )}

                  {pagination.total_pages > 6 && (
                    <button
                      onClick={() => setPage(pagination.total_pages)}
                      className={`px-2.5 py-1 rounded-sm border font-bold transition-colors ${
                        pagination.page === pagination.total_pages
                          ? 'bg-civix-blue text-white border-civix-blue'
                          : 'bg-civix-surface border-civix-border text-civix-text-secondary hover:bg-civix-surface-3'
                      }`}
                    >
                      {pagination.total_pages}
                    </button>
                  )}

                  <button
                    disabled={pagination.page >= pagination.total_pages}
                    onClick={() => setPage((p) => Math.min(pagination.total_pages, p + 1))}
                    className="px-2.5 py-1 bg-civix-surface border border-civix-border rounded-sm disabled:opacity-40 hover:bg-civix-surface-3 transition-colors"
                  >
                    &gt;
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </Panel>

      {/* New Case Modal */}
      {showNewCaseModal && (
        <NewCaseModal
          onClose={() => setShowNewCaseModal(false)}
          onSuccess={handleNewCaseSuccess}
        />
      )}
    </div>
  );
};
