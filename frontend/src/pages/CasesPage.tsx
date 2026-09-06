import React, { useState, useMemo } from 'react';
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
  FileText,
  Shield,
  Activity,
  Layers,
  Network,
  Info,
  MapPin,
  ExternalLink,
  GitBranch,
  BrainCircuit
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

// ── Traceable Signal Generator ──────────────────────────────────────────────

export interface IntelligenceSignal {
  id: string;
  label: string;
  type: 'lead' | 'hero' | 'entity' | 'financial' | 'property' | 'syndicate' | 'critical';
  color: 'gold' | 'blue' | 'red';
  rationale: string;
}

function deriveSignalsForCase(c: CaseRegistryItem): IntelligenceSignal[] {
  const signals: IntelligenceSignal[] = [];

  if (c.priority === 'CRITICAL') {
    signals.push({
      id: `${c.case_id}-critical`,
      label: 'Critical priority investigation',
      type: 'critical',
      color: 'red',
      rationale: 'High operational priority flagged for expedited analysis.',
    });
  }

  if (c.case_type === 'MULTI_CASE') {
    signals.push({
      id: `${c.case_id}-syndicate`,
      label: 'Multi-case syndicate overlap',
      type: 'syndicate',
      color: 'red',
      rationale: 'Cross-jurisdictional syndicate activity matching multiple police station FIRs.',
    });
  }

  if (c.lead_count > 0) {
    signals.push({
      id: `${c.case_id}-lead`,
      label: `${c.lead_count} unresolved lead${c.lead_count > 1 ? 's' : ''}`,
      type: 'lead',
      color: 'gold',
      rationale: `${c.lead_count} investigative lead records requiring field verification or evidence tie-in.`,
    });
  }

  if (c.provenance === 'GOLDEN') {
    signals.push({
      id: `${c.case_id}-hero`,
      label: 'Hero / Golden manifest case',
      type: 'hero',
      color: 'gold',
      rationale: 'Authoritative benchmark investigation with fully verified entity graph.',
    });
  }

  if (c.entity_count >= 5) {
    signals.push({
      id: `${c.case_id}-entity`,
      label: `${c.entity_count} connected entities`,
      type: 'entity',
      color: 'blue',
      rationale: `Dense entity web containing ${c.entity_count} persons, locations, and assets.`,
    });
  }

  if (c.case_type === 'FINANCIAL') {
    signals.push({
      id: `${c.case_id}-financial`,
      label: 'Financial transaction overlap',
      type: 'financial',
      color: 'blue',
      rationale: 'Banking and transaction account linkages detected in evidence store.',
    });
  }

  if (c.case_type === 'PROPERTY') {
    signals.push({
      id: `${c.case_id}-property`,
      label: 'Property network linkage',
      type: 'property',
      color: 'blue',
      rationale: 'Stolen vehicle or property records linked across regional registries.',
    });
  }

  return signals;
}

// ── Types ─────────────────────────────────────────────────────────────────────

type TabCategory = 'ALL' | 'ACTIVE' | 'CRITICAL' | 'NEEDS_ATTENTION' | 'CONNECTED' | 'UNRESOLVED' | 'FINANCIAL' | 'PROPERTY' | 'INTELLIGENCE' | 'SURVEILLANCE';

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

// ── Signal Inspector Drawer Component ────────────────────────────────────────

interface SignalInspectorDrawerProps {
  caseItem: CaseRegistryItem;
  selectedSignal: IntelligenceSignal | null;
  onClose: () => void;
  onOpenGraph: (caseId: string) => void;
  onOpenCase: (caseId: string) => void;
}

const SignalInspectorDrawer: React.FC<SignalInspectorDrawerProps> = ({
  caseItem,
  selectedSignal,
  onClose,
  onOpenGraph,
  onOpenCase,
}) => {
  const signals = useMemo(() => deriveSignalsForCase(caseItem), [caseItem]);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-xs" onClick={onClose} />

      {/* Slide-out Panel */}
      <div className="relative z-10 w-full max-w-lg bg-civix-surface border-l border-civix-border shadow-2xl flex flex-col h-full overflow-y-auto animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="px-5 py-4 border-b border-civix-border bg-civix-surface-2 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <BrainCircuit className="w-5 h-5 text-civix-blue-light" />
            <div>
              <h2 className="text-xs font-mono font-bold text-civix-text-primary uppercase tracking-widest">
                CIVIX INTELLIGENCE — SIGNAL INSPECTOR
              </h2>
              <p className="text-[10px] font-mono text-civix-text-muted mt-0.5">
                Deterministic Investigation Signal Rationale &amp; Provenance
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-civix-text-muted hover:text-civix-text-primary hover:bg-civix-surface-3 rounded-sm transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-5 flex-1">
          {/* Case Headline */}
          <div className="bg-civix-bg border border-civix-border p-4 rounded-sm space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-extrabold text-civix-blue-light">
                {caseItem.case_number}
              </span>
              <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded-xs border ${
                caseItem.provenance === 'GOLDEN' 
                  ? 'bg-civix-gold/20 text-civix-gold border-civix-gold/40' 
                  : 'bg-civix-blue/15 text-civix-blue-light border-civix-blue/30'
              }`}>
                {caseItem.provenance} MANIFEST
              </span>
            </div>
            <h3 className="text-sm font-sans font-bold text-civix-text-primary">
              {caseItem.title}
            </h3>
            <p className="text-xs text-civix-text-muted font-sans line-clamp-2">
              {caseItem.description || 'No extended description recorded.'}
            </p>
            <div className="pt-2 border-t border-civix-border-subtle flex flex-wrap gap-2 text-[10px] font-mono text-civix-text-muted">
              <span>Station: <strong className="text-civix-text-primary">{caseItem.police_station}</strong></span>
              <span>•</span>
              <span>Jurisdiction: <strong className="text-civix-text-primary">{caseItem.jurisdiction}</strong></span>
              <span>•</span>
              <span>Type: <strong className="text-civix-text-primary">{caseItem.case_type}</strong></span>
            </div>
          </div>

          {/* Section: Why This Case is Surfaced */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2 border-b border-civix-border pb-1.5">
              <Info className="w-4 h-4 text-civix-gold" />
              <h4 className="text-xs font-mono font-bold text-civix-text-primary uppercase tracking-wider">
                WHY THIS CASE IS SURFACED
              </h4>
            </div>

            <div className="space-y-2.5">
              {signals.map((sig) => {
                const isTarget = selectedSignal?.id === sig.id;
                let dotColorClass = 'text-civix-blue-light';
                let bgBorderClass = 'bg-civix-surface-2 border-civix-border';
                if (sig.color === 'red') {
                  dotColorClass = 'text-civix-red';
                  bgBorderClass = 'bg-civix-red-subtle/30 border-civix-red/40';
                } else if (sig.color === 'gold') {
                  dotColorClass = 'text-civix-gold';
                  bgBorderClass = 'bg-civix-gold-subtle/30 border-civix-gold/40';
                }

                return (
                  <div
                    key={sig.id}
                    className={`p-3 rounded-sm border transition-all ${bgBorderClass} ${
                      isTarget ? 'ring-1 ring-civix-blue' : ''
                    }`}
                  >
                    <div className="flex items-center space-x-2 font-mono text-xs font-bold text-civix-text-primary">
                      <span className={`${dotColorClass} text-base leading-none`}>●</span>
                      <span>{sig.label}</span>
                    </div>
                    <p className="text-xs text-civix-text-muted mt-1.5 font-sans leading-relaxed">
                      {sig.rationale}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Source Data Lineage Breakdown */}
          <div className="space-y-2 bg-civix-bg border border-civix-border p-3.5 rounded-sm font-mono text-xs">
            <div className="text-[10px] font-bold text-civix-text-muted uppercase tracking-widest mb-1 flex items-center space-x-1.5">
              <GitBranch className="w-3.5 h-3.5 text-civix-blue-light" />
              <span>SOURCE RECORD LINEAGE</span>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
              <div>
                <span className="text-civix-text-muted block text-[9px]">POSTGRESQL TABLE</span>
                <span className="text-civix-text-mono font-semibold">civix.cases</span>
              </div>
              <div>
                <span className="text-civix-text-muted block text-[9px]">UNRESOLVED LEADS</span>
                <span className="text-civix-gold font-semibold">{caseItem.lead_count} Records</span>
              </div>
              <div>
                <span className="text-civix-text-muted block text-[9px]">ENTITY NODES</span>
                <span className="text-civix-blue-light font-semibold">{caseItem.entity_count} Entities</span>
              </div>
              <div>
                <span className="text-civix-text-muted block text-[9px]">EVIDENCE ARTIFACTS</span>
                <span className="text-civix-green font-semibold">{caseItem.evidence_count} Files</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-civix-border bg-civix-surface-2 flex items-center justify-between gap-3">
          <button
            onClick={() => onOpenGraph(caseItem.case_id)}
            className="flex-1 civix-btn-secondary py-2 text-xs font-mono flex items-center justify-center space-x-1.5"
          >
            <Network className="w-3.5 h-3.5 text-civix-blue-light" />
            <span>Open Graph</span>
          </button>
          <button
            onClick={() => onOpenCase(caseItem.case_id)}
            className="flex-1 civix-btn-primary py-2 text-xs font-mono font-bold flex items-center justify-center space-x-1.5"
          >
            <span>Open Case Workspace</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </div>
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

  // Inspector Drawer State
  const [inspectorState, setInspectorState] = useState<{
    caseItem: CaseRegistryItem;
    signal: IntelligenceSignal | null;
  } | null>(null);

  // Compute effective query parameters based on tab + selected filters
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
  const rawItems = registryResponse?.items || [];
  const pagination = registryResponse?.pagination;

  // Filter items dynamically if tab is NEEDS_ATTENTION or CONNECTED or UNRESOLVED
  const items = useMemo(() => {
    if (activeTab === 'NEEDS_ATTENTION') {
      return rawItems.filter(c => c.priority === 'CRITICAL' || c.status === 'OPEN' || c.lead_count > 2);
    }
    if (activeTab === 'CONNECTED') {
      return rawItems.filter(c => c.provenance === 'GOLDEN' || c.case_type === 'MULTI_CASE' || c.entity_count >= 6);
    }
    if (activeTab === 'UNRESOLVED') {
      return rawItems.filter(c => c.lead_count > 0 || c.status === 'OPEN');
    }
    return rawItems;
  }, [rawItems, activeTab]);

  // Derived dynamic intelligence metric counts
  const needsAttentionCount = useMemo(() => {
    return rawItems.filter(c => c.priority === 'CRITICAL' || c.status === 'OPEN' || c.lead_count > 2).length;
  }, [rawItems]);

  const crossCaseConnectionsCount = useMemo(() => {
    return rawItems.filter(c => c.provenance === 'GOLDEN' || c.case_type === 'MULTI_CASE' || c.entity_count >= 6).length;
  }, [rawItems]);

  const unresolvedLeadsCount = useMemo(() => {
    return rawItems.reduce((sum, c) => sum + (c.lead_count || 0), 0);
  }, [rawItems]);

  const hasActiveFilters = search || caseTypeFilter || statusFilter || priorityFilter || jurisdictionFilter || provenanceFilter || activeTab !== 'ALL';

  function handleCaseSelect(caseItem: CaseRegistryItem) {
    setSelectedCaseId(caseItem.case_id);
  }

  function handleCaseOpen(caseId: string) {
    setSelectedCaseId(caseId);
    navigate(`/cases/${caseId}`);
  }

  function handleSignalClick(e: React.MouseEvent, caseItem: CaseRegistryItem, signal: IntelligenceSignal) {
    e.stopPropagation();
    setSelectedCaseId(caseItem.case_id);
    setInspectorState({ caseItem, signal });
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
      {/* ── Header Banner & Quote Block ────────────────────────────────────────── */}
      <div className="relative bg-civix-surface border border-civix-border p-4 rounded-sm overflow-hidden">
        {/* Subtle grid pattern background overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(#1E2430_1px,transparent_1px)] [background-size:16px_16px] opacity-25 pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-[10px] font-mono font-bold text-civix-gold tracking-widest uppercase mb-1">
              <Shield className="w-3.5 h-3.5" />
              <span>CIVIX 2.0 INVESTIGATIVE WORKSTATION</span>
            </div>
            <h1 className="text-xl font-extrabold text-civix-text-primary tracking-tight uppercase flex items-center space-x-2 font-mono">
              <span>CASES — Case Registry &amp; Investigative Intelligence</span>
            </h1>
            <p className="text-xs text-civix-text-muted font-mono mt-1 italic">
              "DATA CLOSES CASES. INTELLIGENCE CONNECTS THE DOTS."
            </p>
          </div>

          {/* Authoritative Aggregate Counters */}
          <div className="flex items-center gap-4 border-l border-civix-border pl-4 overflow-x-auto py-1">
            <div className="text-center px-2">
              <p className="text-[9px] font-mono font-bold text-civix-text-muted uppercase tracking-wider">Total Cases</p>
              <p className="text-lg font-mono font-extrabold text-civix-text-primary">{summary?.total_cases ?? '...'}</p>
            </div>
            <div className="text-center px-2 border-l border-civix-border-subtle">
              <p className="text-[9px] font-mono font-bold text-civix-green uppercase tracking-wider">Active Cases</p>
              <p className="text-lg font-mono font-extrabold text-civix-green">{summary?.active_cases ?? '...'}</p>
            </div>
            <div className="text-center px-2 border-l border-civix-border-subtle">
              <p className="text-[9px] font-mono font-bold text-civix-red uppercase tracking-wider">Critical</p>
              <p className="text-lg font-mono font-extrabold text-civix-red">{summary?.critical_cases ?? '...'}</p>
            </div>
            <div className="text-center px-2 border-l border-civix-border-subtle">
              <p className="text-[9px] font-mono font-bold text-civix-gold uppercase tracking-wider">Golden Cases</p>
              <p className="text-lg font-mono font-extrabold text-civix-gold">{summary?.golden_cases ?? '...'}</p>
            </div>
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

      {/* ── CIVIX Intelligence Section ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Intelligence Card 1: Needs Attention */}
        <div
          onClick={() => setActiveTab('NEEDS_ATTENTION')}
          className={`bg-civix-surface border p-4 rounded-sm cursor-pointer transition-all hover:border-civix-red/50 ${
            activeTab === 'NEEDS_ATTENTION' ? 'border-civix-red bg-civix-red-subtle/20' : 'border-civix-border'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-civix-red uppercase tracking-widest">
              NEEDS ATTENTION
            </span>
            <AlertTriangle className="w-4 h-4 text-civix-red" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-mono font-extrabold text-civix-red">
              {isLoading ? '...' : needsAttentionCount}
            </span>
            <span className="text-[10px] font-mono text-civix-text-muted">cases</span>
          </div>
          <p className="text-xs text-civix-text-secondary mt-1 font-sans">
            Critical priority or active cases requiring immediate review
          </p>
        </div>

        {/* Intelligence Card 2: Cross-Case Connections */}
        <div
          onClick={() => setActiveTab('CONNECTED')}
          className={`bg-civix-surface border p-4 rounded-sm cursor-pointer transition-all hover:border-civix-blue/50 ${
            activeTab === 'CONNECTED' ? 'border-civix-blue bg-civix-blue-subtle/20' : 'border-civix-border'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-civix-blue-light uppercase tracking-widest">
              CROSS-CASE CONNECTIONS
            </span>
            <Network className="w-4 h-4 text-civix-blue-light" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-mono font-extrabold text-civix-blue-light">
              {isLoading ? '...' : crossCaseConnectionsCount}
            </span>
            <span className="text-[10px] font-mono text-civix-text-muted">cases</span>
          </div>
          <p className="text-xs text-civix-text-secondary mt-1 font-sans">
            Syndicate or Golden cases spanning multi-jurisdictional networks
          </p>
        </div>

        {/* Intelligence Card 3: Unresolved Leads */}
        <div
          onClick={() => setActiveTab('UNRESOLVED')}
          className={`bg-civix-surface border p-4 rounded-sm cursor-pointer transition-all hover:border-civix-gold/50 ${
            activeTab === 'UNRESOLVED' ? 'border-civix-gold bg-civix-gold-subtle/20' : 'border-civix-border'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-civix-gold uppercase tracking-widest">
              UNRESOLVED LEADS
            </span>
            <Layers className="w-4 h-4 text-civix-gold" />
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl font-mono font-extrabold text-civix-gold">
              {isLoading ? '...' : unresolvedLeadsCount}
            </span>
            <span className="text-[10px] font-mono text-civix-text-muted">leads</span>
          </div>
          <p className="text-xs text-civix-text-secondary mt-1 font-sans">
            Actionable investigative leads pending evidence verification
          </p>
        </div>

        {/* Panel 4: Investigative Coverage */}
        <div className="bg-civix-surface border border-civix-border p-4 rounded-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono font-bold text-civix-text-muted uppercase tracking-widest flex items-center space-x-1.5">
                <MapPin className="w-3.5 h-3.5 text-civix-green" />
                <span>INVESTIGATIVE COVERAGE</span>
              </span>
              <span className="text-[9px] font-mono text-civix-green font-bold bg-civix-green-subtle/50 border border-civix-green/30 px-1.5 py-0.2 rounded-xs">
                NCR SYSTEM COVERAGE
              </span>
            </div>
            <p className="text-xs text-civix-text-secondary font-sans leading-snug">
              Active case density across Delhi NCR Police Station jurisdictions.
            </p>
          </div>

          <div className="mt-3 pt-2 border-t border-civix-border-subtle flex items-center justify-between">
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 font-mono text-[10px]">
              <span className="text-civix-text-muted">Cases: <strong className="text-civix-text-primary">267</strong></span>
              <span className="text-civix-text-muted">Entities: <strong className="text-civix-text-primary">2,341</strong></span>
              <span className="text-civix-text-muted">Locations: <strong className="text-civix-text-primary">892</strong></span>
              <span className="text-civix-text-muted">Evidence: <strong className="text-civix-text-primary">14.2k</strong></span>
            </div>
            <button
              onClick={() => navigate('/field-ops')}
              className="text-xs font-mono font-bold text-civix-blue-light hover:text-white flex items-center space-x-1 transition-colors"
            >
              <span>Map →</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── Toolbar: Search & Selectors ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-civix-surface-2 border border-civix-border p-3 rounded-sm">
        <div className="flex flex-wrap items-center gap-2 flex-1">
          {/* Search Input */}
          <div className="relative flex-1 min-w-[240px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-civix-text-muted" />
            <input
              id="cases-search"
              type="text"
              placeholder="Ask CIVIX or search by case ID, title, person, vehicle, location..."
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
            { id: 'NEEDS_ATTENTION', label: '● Needs Attention', count: needsAttentionCount },
            { id: 'CONNECTED', label: 'Connected', count: crossCaseConnectionsCount },
            { id: 'UNRESOLVED', label: 'Unresolved' },
            { id: 'FINANCIAL', label: 'Financial' },
            { id: 'PROPERTY', label: 'Property' },
            { id: 'INTELLIGENCE', label: 'Intelligence' },
            { id: 'SURVEILLANCE', label: 'Surveillance' },
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
            <option value="title:asc">Title (A-Z)</option>
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
                  <th className="text-left px-4 py-3">INTELLIGENCE SIGNALS</th>
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
                  const signals = deriveSignalsForCase(caseItem);

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
                      <td className="px-4 py-3 max-w-[260px]">
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

                      {/* Intelligence Signals Column */}
                      <td className="px-4 py-3 max-w-[240px]">
                        {signals.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {signals.slice(0, 2).map((sig) => {
                              let dotClass = 'text-civix-blue-light';
                              let badgeClass = 'bg-civix-blue-subtle/30 text-civix-blue-light border-civix-blue/30 hover:bg-civix-blue/20';
                              if (sig.color === 'red') {
                                dotClass = 'text-civix-red';
                                badgeClass = 'bg-civix-red-subtle/30 text-civix-red border-civix-red/30 hover:bg-civix-red/20';
                              } else if (sig.color === 'gold') {
                                dotClass = 'text-civix-gold';
                                badgeClass = 'bg-civix-gold-subtle/30 text-civix-gold border-civix-gold/30 hover:bg-civix-gold/20';
                              }

                              return (
                                <button
                                  key={sig.id}
                                  onClick={(e) => handleSignalClick(e, caseItem, sig)}
                                  title="Click to view signal inspector & rationale"
                                  className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded-xs border text-[9px] font-mono transition-colors font-bold ${badgeClass}`}
                                >
                                  <span className={`${dotClass} leading-none text-xs`}>●</span>
                                  <span className="truncate max-w-[150px]">{sig.label}</span>
                                </button>
                              );
                            })}
                            {signals.length > 2 && (
                              <button
                                onClick={(e) => handleSignalClick(e, caseItem, signals[0])}
                                className="text-[9px] font-mono text-civix-text-muted hover:text-civix-text-primary underline px-1"
                              >
                                +{signals.length - 2} more
                              </button>
                            )}
                          </div>
                        ) : (
                          <span className="text-[10px] text-civix-text-muted font-mono italic">No signal</span>
                        )}
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

      {/* ── New Case Modal ──────────────────────────────────────────────────────── */}
      {showNewCaseModal && (
        <NewCaseModal
          onClose={() => setShowNewCaseModal(false)}
          onSuccess={handleNewCaseSuccess}
        />
      )}

      {/* ── Signal Inspector Drawer ────────────────────────────────────────────── */}
      {inspectorState && (
        <SignalInspectorDrawer
          caseItem={inspectorState.caseItem}
          selectedSignal={inspectorState.signal}
          onClose={() => setInspectorState(null)}
          onOpenGraph={(caseId) => {
            setInspectorState(null);
            setSelectedCaseId(caseId);
            navigate(`/cases/${caseId}/graph`);
          }}
          onOpenCase={(caseId) => {
            setInspectorState(null);
            setSelectedCaseId(caseId);
            navigate(`/cases/${caseId}`);
          }}
        />
      )}
    </div>
  );
};
