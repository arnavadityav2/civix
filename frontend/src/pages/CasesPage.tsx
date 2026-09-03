import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { casesApi } from '../api/cases';
import { useCaseSelection } from '../context/CaseSelectionContext';
import type { CaseListItem, CaseCreateRequest } from '../types/api';
import { Panel } from '../components/ui/Panel';
import { Badge } from '../components/ui/Badge';
import {
  Search,
  Plus,
  Briefcase,
  AlertTriangle,
  RefreshCw,
  ChevronRight,
  Filter,
  X,
  Loader2,
  ArrowUpDown,
  CheckCircle2,
} from 'lucide-react';

// ── Status & Priority badge mapping ──────────────────────────────────────────

const STATUS_VARIANTS: Record<string, string> = {
  OPEN: 'active',
  ACTIVE: 'confirmed',
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

const PRIORITY_ORDER: Record<string, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function normalizeFilterValue(v: string) {
  return v.toUpperCase().trim();
}

function matchesFilter(item: CaseListItem, filters: FilterState, search: string) {
  if (search) {
    const q = search.toLowerCase();
    if (
      !item.title.toLowerCase().includes(q) &&
      !item.case_number.toLowerCase().includes(q) &&
      !item.jurisdiction.toLowerCase().includes(q)
    ) {
      return false;
    }
  }
  if (filters.status && normalizeFilterValue(item.status) !== normalizeFilterValue(filters.status)) return false;
  if (filters.priority && normalizeFilterValue(item.priority) !== normalizeFilterValue(filters.priority)) return false;
  if (filters.jurisdiction && normalizeFilterValue(item.jurisdiction) !== normalizeFilterValue(filters.jurisdiction)) return false;
  return true;
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface FilterState {
  status: string;
  priority: string;
  jurisdiction: string;
}

type SortField = 'case_number' | 'title' | 'status' | 'priority' | 'jurisdiction';

const INITIAL_FILTERS: FilterState = { status: '', priority: '', jurisdiction: '' };

// ── New Case Modal ────────────────────────────────────────────────────────────

interface NewCaseModalProps {
  onClose: () => void;
  onSuccess: (newCaseId: string) => void;
}

const CASE_TYPES = ['FINANCIAL', 'INTELLIGENCE', 'CRIMINAL', 'COUNTERTERRORISM', 'CYBER', 'NARCOTICS', 'OTHER'];
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
      queryClient.invalidateQueries({ queryKey: ['cases'] });
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div className="absolute inset-0 bg-slate-900/40" onClick={onClose} />

      {/* Dialog */}
      <div className="relative z-10 bg-white border border-slate-300 rounded shadow-lg w-full max-w-md mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center space-x-2">
            <Briefcase className="w-4 h-4 text-amber-600" />
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">Open New Investigation</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded transition-colors"
            disabled={mutation.isPending}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Case Number */}
          <div>
            <label htmlFor="nc-case-number" className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wide">
              Case Number <span className="text-red-600">*</span>
            </label>
            <input
              id="nc-case-number"
              type="text"
              placeholder="e.g. CASE-2026-0143"
              value={form.case_number}
              onChange={(e) => setForm((f) => ({ ...f, case_number: e.target.value }))}
              className="w-full border border-slate-300 rounded px-3 py-2 text-xs font-mono text-slate-900 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900 focus:border-slate-900 placeholder-slate-400"
              required
              disabled={mutation.isPending}
            />
          </div>

          {/* Title */}
          <div>
            <label htmlFor="nc-title" className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wide">
              Investigation Title <span className="text-red-600">*</span>
            </label>
            <input
              id="nc-title"
              type="text"
              placeholder="Brief operational case title"
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              className="w-full border border-slate-300 rounded px-3 py-2 text-xs text-slate-900 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900 focus:border-slate-900 placeholder-slate-400"
              required
              disabled={mutation.isPending}
            />
          </div>

          {/* Case Type + Priority */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="nc-case-type" className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wide">
                Case Type
              </label>
              <select
                id="nc-case-type"
                value={form.case_type}
                onChange={(e) => setForm((f) => ({ ...f, case_type: e.target.value }))}
                className="w-full border border-slate-300 rounded px-3 py-2 text-xs text-slate-900 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900 focus:border-slate-900"
                disabled={mutation.isPending}
              >
                {CASE_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="nc-priority" className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wide">
                Priority
              </label>
              <select
                id="nc-priority"
                value={form.priority}
                onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
                className="w-full border border-slate-300 rounded px-3 py-2 text-xs text-slate-900 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900 focus:border-slate-900"
                disabled={mutation.isPending}
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Jurisdiction */}
          <div>
            <label htmlFor="nc-jurisdiction" className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wide">
              Jurisdiction <span className="text-red-600">*</span>
            </label>
            <input
              id="nc-jurisdiction"
              type="text"
              placeholder="e.g. DELHI_NCR, MUMBAI, NATIONAL"
              value={form.jurisdiction}
              onChange={(e) => setForm((f) => ({ ...f, jurisdiction: e.target.value }))}
              className="w-full border border-slate-300 rounded px-3 py-2 text-xs font-mono text-slate-900 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900 focus:border-slate-900 placeholder-slate-400"
              required
              disabled={mutation.isPending}
            />
          </div>

          {/* Investigating Unit (optional) */}
          <div>
            <label htmlFor="nc-unit" className="block text-xs font-semibold text-slate-700 mb-1 uppercase tracking-wide">
              Investigating Unit <span className="text-slate-400 font-normal">(optional)</span>
            </label>
            <input
              id="nc-unit"
              type="text"
              placeholder="e.g. Delhi NCR Task Force"
              value={form.investigating_unit}
              onChange={(e) => setForm((f) => ({ ...f, investigating_unit: e.target.value }))}
              className="w-full border border-slate-300 rounded px-3 py-2 text-xs text-slate-900 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900 focus:border-slate-900 placeholder-slate-400"
              disabled={mutation.isPending}
            />
          </div>

          {/* Error */}
          {formError && (
            <div className="flex items-start space-x-2 bg-red-50 border border-red-200 rounded p-3">
              <AlertTriangle className="w-3.5 h-3.5 text-red-600 flex-shrink-0 mt-0.5" />
              <span className="text-xs text-red-700">{formError}</span>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={mutation.isPending}
              className="px-4 py-2 text-xs font-semibold text-slate-700 bg-slate-100 border border-slate-300 rounded hover:bg-slate-200 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="flex items-center space-x-2 px-4 py-2 text-xs font-bold bg-slate-900 text-white rounded hover:bg-slate-800 transition-colors disabled:opacity-50 shadow-sm"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Opening...</span>
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5 text-amber-400" />
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

// ── Case Preview Panel ────────────────────────────────────────────────────────

interface CasePreviewProps {
  caseItem: CaseListItem;
  onOpenCase: (caseId: string) => void;
}

const CasePreview: React.FC<CasePreviewProps> = ({ caseItem, onOpenCase }) => {
  const statusVariant = STATUS_VARIANTS[caseItem.status?.toUpperCase()] || 'default';
  const priorityVariant = PRIORITY_VARIANTS[caseItem.priority?.toUpperCase()] || 'default';

  return (
    <div className="bg-white border border-slate-200 rounded shadow-sm overflow-hidden">
      {/* Preview header */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <div>
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">Case Preview</h3>
          <p className="text-[11px] text-slate-500 font-mono mt-0.5">{caseItem.case_number}</p>
        </div>
        <button
          onClick={() => onOpenCase(caseItem.case_id)}
          className="flex items-center space-x-1.5 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 px-3 py-1.5 rounded transition-colors shadow-sm"
        >
          <span>Open Investigation</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Preview body */}
      <div className="p-4 space-y-3">
        <div>
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Title / Subject</p>
          <p className="text-sm font-bold text-slate-900">{caseItem.title}</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Status</p>
            <Badge variant={statusVariant as any}>{caseItem.status}</Badge>
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Priority</p>
            <Badge variant={priorityVariant as any}>{caseItem.priority}</Badge>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Case Type</p>
            <p className="text-xs font-mono font-semibold text-slate-800">{caseItem.case_type}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-1">Jurisdiction</p>
            <p className="text-xs font-mono font-semibold text-slate-800">{caseItem.jurisdiction}</p>
          </div>
        </div>

        <div className="pt-2 border-t border-slate-100">
          <p className="text-[10px] font-mono text-slate-400">
            CASE ID: {caseItem.case_id}
          </p>
        </div>
      </div>
    </div>
  );
};

// ── Main CasesPage ────────────────────────────────────────────────────────────

export const CasesPage: React.FC = () => {
  const navigate = useNavigate();
  const { selectedCaseId, setSelectedCaseId } = useCaseSelection();

  const [search, setSearch] = useState('');
  const [filters, setFilters] = useState<FilterState>(INITIAL_FILTERS);
  const [sortField, setSortField] = useState<SortField>('priority');
  const [sortAsc, setSortAsc] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [showNewCaseModal, setShowNewCaseModal] = useState(false);
  const [newCaseSuccess, setNewCaseSuccess] = useState<string | null>(null);

  // ── Data fetching ────────────────────────────────────────────────────────
  const { data: cases, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['cases'],
    queryFn: () => casesApi.listCases(),
    staleTime: 30_000,
  });

  // ── Client-side filtering + sorting ─────────────────────────────────────
  // NOTE: Backend GET /cases does not expose query params for server-side
  // filtering. This client-side filter operates on the full user-accessible
  // case list (enforced by RLS). Future scale: if case count grows large,
  // a backend filter param should be requested.
  const filtered = React.useMemo(() => {
    if (!cases) return [];
    let result = cases.filter((c) => matchesFilter(c, filters, search));
    result.sort((a, b) => {
      let va: string | number = '';
      let vb: string | number = '';
      if (sortField === 'priority') {
        va = PRIORITY_ORDER[a.priority?.toUpperCase()] ?? 99;
        vb = PRIORITY_ORDER[b.priority?.toUpperCase()] ?? 99;
      } else {
        va = (a[sortField] || '').toLowerCase();
        vb = (b[sortField] || '').toLowerCase();
      }
      if (va < vb) return sortAsc ? -1 : 1;
      if (va > vb) return sortAsc ? 1 : -1;
      return 0;
    });
    return result;
  }, [cases, filters, search, sortField, sortAsc]);

  // ── Derived filter options from actual data ──────────────────────────────
  const filterOptions = React.useMemo(() => {
    if (!cases) return { statuses: [], priorities: [], jurisdictions: [] };
    return {
      statuses: [...new Set(cases.map((c) => c.status).filter(Boolean))].sort(),
      priorities: [...new Set(cases.map((c) => c.priority).filter(Boolean))].sort(),
      jurisdictions: [...new Set(cases.map((c) => c.jurisdiction).filter(Boolean))].sort(),
    };
  }, [cases]);

  const hasActiveFilters = filters.status || filters.priority || filters.jurisdiction || search;

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortAsc((v) => !v);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  }

  function handleCaseSelect(caseItem: CaseListItem) {
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

  const selectedCase = filtered.find((c) => c.case_id === selectedCaseId) ||
    cases?.find((c) => c.case_id === selectedCaseId);

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-slate-200 gap-3">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight uppercase">Cases</h1>
            {cases && (
              <span className="text-[11px] font-mono font-bold bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded border border-slate-300">
                {cases.length} CASE{cases.length !== 1 ? 'S' : ''}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5 font-medium">Case Registry &amp; Investigation Management</p>
        </div>

        {/* New Case CTA */}
        <button
          id="new-case-btn"
          onClick={() => setShowNewCaseModal(true)}
          className="flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs px-4 py-2.5 rounded transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4 text-amber-400" />
          <span>New Case</span>
        </button>
      </div>

      {/* Success banner */}
      {newCaseSuccess && (
        <div className="flex items-center space-x-2 bg-emerald-50 border border-emerald-300 text-emerald-800 text-xs font-semibold px-4 py-2.5 rounded">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>Investigation opened successfully. Case ID: <span className="font-mono">{newCaseSuccess}</span></span>
        </div>
      )}

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" />
          <input
            id="cases-search"
            type="text"
            placeholder="Search cases, title, jurisdiction..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-2 border border-slate-300 rounded text-xs text-slate-900 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900 focus:border-slate-900 placeholder-slate-400"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Filter Toggle */}
        <button
          id="cases-filter-toggle"
          onClick={() => setShowFilters((v) => !v)}
          className={`flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold rounded border transition-colors ${
            showFilters || (filters.status || filters.priority || filters.jurisdiction)
              ? 'bg-slate-900 text-white border-slate-900'
              : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
          }`}
        >
          <Filter className="w-3.5 h-3.5" />
          <span>Filters</span>
          {(filters.status || filters.priority || filters.jurisdiction) && (
            <span className="bg-amber-500 text-white rounded-full w-4 h-4 text-[9px] font-bold flex items-center justify-center">
              {[filters.status, filters.priority, filters.jurisdiction].filter(Boolean).length}
            </span>
          )}
        </button>

        {/* Refresh */}
        <button
          id="cases-refresh"
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded hover:bg-slate-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>

        {/* Clear filters */}
        {hasActiveFilters && (
          <button
            id="cases-clear-filters"
            onClick={() => { setFilters(INITIAL_FILTERS); setSearch(''); }}
            className="flex items-center space-x-1.5 px-3 py-2 text-xs font-semibold text-slate-600 bg-slate-100 border border-slate-200 rounded hover:bg-slate-200 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
            <span>Clear</span>
          </button>
        )}
      </div>

      {/* Filter Bar */}
      {showFilters && (
        <div className="flex flex-wrap gap-3 p-3 bg-slate-50 border border-slate-200 rounded">
          <div className="flex items-center space-x-2">
            <label htmlFor="filter-status" className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Status</label>
            <select
              id="filter-status"
              value={filters.status}
              onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
              className="border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
            >
              <option value="">All</option>
              {filterOptions.statuses.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <label htmlFor="filter-priority" className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Priority</label>
            <select
              id="filter-priority"
              value={filters.priority}
              onChange={(e) => setFilters((f) => ({ ...f, priority: e.target.value }))}
              className="border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
            >
              <option value="">All</option>
              {filterOptions.priorities.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <label htmlFor="filter-jurisdiction" className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Jurisdiction</label>
            <select
              id="filter-jurisdiction"
              value={filters.jurisdiction}
              onChange={(e) => setFilters((f) => ({ ...f, jurisdiction: e.target.value }))}
              className="border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
            >
              <option value="">All</option>
              {filterOptions.jurisdictions.map((j) => (
                <option key={j} value={j}>{j}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex gap-5 items-start">
        {/* Case Registry Table */}
        <div className="flex-1 min-w-0">
          <Panel
            title="CASE REGISTRY"
            subtitle="Active investigations visible under current investigator context"
            headerAction={
              <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-widest">
                {isLoading ? '...' : `${filtered.length} results`}
              </span>
            }
          >
            {/* Loading state */}
            {isLoading && (
              <div className="flex items-center justify-center py-16 space-x-2 text-slate-400">
                <Loader2 className="w-5 h-5 animate-spin text-amber-600" />
                <span className="text-xs font-mono">Loading case registry...</span>
              </div>
            )}

            {/* Error state */}
            {!isLoading && error && (
              <div className="py-12 text-center space-y-3">
                <div className="flex justify-center">
                  <AlertTriangle className="w-8 h-8 text-red-400" />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-900 uppercase tracking-wide">Case Registry Unavailable</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Unable to retrieve case records from the investigation service.
                  </p>
                </div>
                <button
                  onClick={() => refetch()}
                  className="inline-flex items-center space-x-2 px-4 py-2 text-xs font-semibold text-white bg-slate-900 rounded hover:bg-slate-800 transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry</span>
                </button>
              </div>
            )}

            {/* Empty: no cases at all */}
            {!isLoading && !error && cases && cases.length === 0 && (
              <div className="py-12 text-center space-y-2">
                <Briefcase className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-sm font-semibold text-slate-700">No investigations available.</p>
                <p className="text-xs text-slate-400">Open a new investigation to begin.</p>
              </div>
            )}

            {/* Empty: filtered returns nothing */}
            {!isLoading && !error && cases && cases.length > 0 && filtered.length === 0 && (
              <div className="py-12 text-center space-y-2">
                <Filter className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-sm font-semibold text-slate-700">No cases match the current filters.</p>
                <button
                  onClick={() => { setFilters(INITIAL_FILTERS); setSearch(''); }}
                  className="text-xs text-slate-500 underline hover:text-slate-700"
                >
                  Clear all filters
                </button>
              </div>
            )}

            {/* Table */}
            {!isLoading && !error && filtered.length > 0 && (
              <div className="overflow-x-auto -m-4">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      {([
                        { label: 'Case ID', field: 'case_number' as SortField },
                        { label: 'Title / Subject', field: 'title' as SortField },
                        { label: 'Status', field: 'status' as SortField },
                        { label: 'Priority', field: 'priority' as SortField },
                        { label: 'Jurisdiction', field: 'jurisdiction' as SortField },
                        { label: 'Type', field: null },
                      ]).map(({ label, field }) => (
                        <th
                          key={label}
                          className={`text-left px-4 py-2.5 text-[10px] font-bold text-slate-500 uppercase tracking-widest whitespace-nowrap ${field ? 'cursor-pointer hover:text-slate-700 select-none' : ''}`}
                          onClick={field ? () => handleSort(field) : undefined}
                        >
                          <div className="flex items-center space-x-1">
                            <span>{label}</span>
                            {field && sortField === field && (
                              <ArrowUpDown className="w-2.5 h-2.5 text-amber-600" />
                            )}
                          </div>
                        </th>
                      ))}
                      <th className="text-right px-4 py-2.5 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((caseItem, idx) => {
                      const isSelected = caseItem.case_id === selectedCaseId;
                      const statusVariant = STATUS_VARIANTS[caseItem.status?.toUpperCase()] || 'default';
                      const priorityVariant = PRIORITY_VARIANTS[caseItem.priority?.toUpperCase()] || 'default';

                      return (
                        <tr
                          key={caseItem.case_id}
                          id={`case-row-${caseItem.case_id}`}
                          onClick={() => handleCaseSelect(caseItem)}
                          className={`border-b transition-colors cursor-pointer ${
                            isSelected
                              ? 'bg-blue-50 border-blue-200 hover:bg-blue-50'
                              : idx % 2 === 0
                              ? 'bg-white border-slate-100 hover:bg-slate-50'
                              : 'bg-slate-50/50 border-slate-100 hover:bg-slate-50'
                          }`}
                        >
                          {/* Case ID */}
                          <td className="px-4 py-2.5 whitespace-nowrap">
                            <div className="flex items-center space-x-2">
                              {isSelected && (
                                <span className="w-1.5 h-1.5 rounded-full bg-blue-700 flex-shrink-0" />
                              )}
                              <span className={`font-mono font-bold text-[11px] ${isSelected ? 'text-blue-900' : 'text-slate-900'}`}>
                                {caseItem.case_number}
                              </span>
                            </div>
                          </td>

                          {/* Title */}
                          <td className="px-4 py-2.5 max-w-[260px]">
                            <span className={`font-semibold leading-tight ${isSelected ? 'text-blue-900' : 'text-slate-900'}`}>
                              {caseItem.title}
                            </span>
                          </td>

                          {/* Status */}
                          <td className="px-4 py-2.5 whitespace-nowrap">
                            <Badge variant={statusVariant as any}>{caseItem.status}</Badge>
                          </td>

                          {/* Priority */}
                          <td className="px-4 py-2.5 whitespace-nowrap">
                            <Badge variant={priorityVariant as any}>{caseItem.priority}</Badge>
                          </td>

                          {/* Jurisdiction */}
                          <td className="px-4 py-2.5 whitespace-nowrap">
                            <span className="font-mono text-[10px] text-slate-600">{caseItem.jurisdiction}</span>
                          </td>

                          {/* Case Type */}
                          <td className="px-4 py-2.5 whitespace-nowrap">
                            <span className="font-mono text-[10px] text-slate-500">{caseItem.case_type}</span>
                          </td>

                          {/* Actions */}
                          <td className="px-4 py-2.5 text-right whitespace-nowrap">
                            <button
                              id={`open-case-${caseItem.case_id}`}
                              onClick={(e) => { e.stopPropagation(); handleCaseOpen(caseItem.case_id); }}
                              className="inline-flex items-center space-x-1 px-2.5 py-1 text-[10px] font-bold text-slate-700 bg-white border border-slate-300 rounded hover:bg-slate-900 hover:text-white hover:border-slate-900 transition-colors shadow-2xs"
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

                {/* Scale note — backend has no pagination for this endpoint */}
                <div className="px-4 py-2 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-400">
                    Showing {filtered.length} of {cases?.length ?? 0} accessible cases
                  </span>
                  {isFetching && (
                    <span className="text-[10px] font-mono text-amber-600 flex items-center space-x-1">
                      <Loader2 className="w-2.5 h-2.5 animate-spin" />
                      <span>Updating...</span>
                    </span>
                  )}
                </div>
              </div>
            )}
          </Panel>
        </div>

        {/* Case Preview Panel */}
        {selectedCase && (
          <div className="w-72 flex-shrink-0">
            <CasePreview caseItem={selectedCase} onOpenCase={handleCaseOpen} />
          </div>
        )}
      </div>

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
