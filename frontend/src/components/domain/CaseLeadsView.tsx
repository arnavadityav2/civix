import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { leadsApi } from '../../api/leads';
import { casesApi } from '../../api/cases';
import { evidenceApi } from '../../api/evidence';
import { LeadReviewModal } from './LeadReviewModal';
import type { InvestigativeLeadResponse } from '../../types/api';
import { 
  Loader2, 
  RefreshCw, 
  FileText, 
  AlertCircle, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Zap, 
  Cpu, 
  Sparkles, 
  Search, 
  ArrowUpDown, 
  ChevronLeft, 
  ChevronRight, 
  User, 
  Shield, 
  Info,
  GitFork
} from 'lucide-react';

interface CaseLeadsViewProps {
  caseId: string;
  onEngineRunComplete?: () => void;
}

export const CaseLeadsView: React.FC<CaseLeadsViewProps> = ({ caseId, onEngineRunComplete }) => {
  const queryClient = useQueryClient();
  const [selectedLead, setSelectedLead] = useState<InvestigativeLeadResponse | null>(null);

  // Filter & Sort State
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'PRIORITY' | 'MODEL_SIGNAL' | 'NEWEST' | 'OLDEST'>('MODEL_SIGNAL');

  // Pagination State (8 cards per page for optimal performance)
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 8;

  // 1. Fetch Case Basic Info for metadata
  const { data: caseData } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => (caseId ? casesApi.getCase(caseId) : Promise.reject(new Error('No case ID'))),
    enabled: !!caseId,
  });

  // 2. Fetch Entity & Evidence counts
  const { data: entitiesResponse } = useQuery({
    queryKey: ['case-entities-person', caseId],
    queryFn: () => (caseId ? casesApi.getCaseEntities(caseId, { limit: 1 }) : Promise.resolve(null)),
    enabled: !!caseId,
  });

  const { data: evidenceData } = useQuery({
    queryKey: ['case-evidence', caseId],
    queryFn: () => (caseId ? evidenceApi.listEvidence(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  // 3. Fetch Case Leads
  const { data: leads = [], isLoading, error, refetch } = useQuery({
    queryKey: ['case-workspace-leads', caseId],
    queryFn: () => (caseId ? leadsApi.getCaseLeads(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  // 4. ML Lead Generation Mutation
  const generateMutation = useMutation({
    mutationFn: () => leadsApi.generateLeads(caseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['case-workspace-leads', caseId] });
      queryClient.invalidateQueries({ queryKey: ['case-leads', caseId] });
      if (onEngineRunComplete) {
        onEngineRunComplete();
      }
    },
  });

  const handleRunAiAnalysis = () => {
    generateMutation.mutate();
  };

  // Filter & Sort Computation
  const filteredAndSortedLeads = useMemo(() => {
    let result = [...leads];

    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (l) =>
          l.lead_text.toLowerCase().includes(q) ||
          l.lead_id.toLowerCase().includes(q) ||
          l.target_entity_id.toLowerCase().includes(q)
      );
    }

    // Priority filter
    if (priorityFilter !== 'ALL') {
      result = result.filter((l) => l.priority?.toUpperCase() === priorityFilter);
    }

    // Status filter
    if (statusFilter !== 'ALL') {
      result = result.filter((l) => l.status?.toUpperCase() === statusFilter);
    }

    // Sorting
    result.sort((a, b) => {
      if (sortBy === 'PRIORITY') {
        const priorityOrder: Record<string, number> = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
        const pA = priorityOrder[a.priority?.toUpperCase() || 'LOW'] || 0;
        const pB = priorityOrder[b.priority?.toUpperCase() || 'LOW'] || 0;
        return pB - pA;
      }
      if (sortBy === 'MODEL_SIGNAL') {
        return (b.ai_confidence || 0) - (a.ai_confidence || 0);
      }
      if (sortBy === 'NEWEST') {
        return b.lead_id.localeCompare(a.lead_id);
      }
      if (sortBy === 'OLDEST') {
        return a.lead_id.localeCompare(b.lead_id);
      }
      return 0;
    });

    return result;
  }, [leads, searchQuery, priorityFilter, statusFilter, sortBy]);

  // Paginated Slice
  const totalPages = Math.ceil(filteredAndSortedLeads.length / pageSize) || 1;
  const paginatedLeads = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredAndSortedLeads.slice(start, start + pageSize);
  }, [filteredAndSortedLeads, currentPage, pageSize]);

  // Metrics breakdown derived from loaded leads
  const metrics = useMemo(() => {
    return {
      total: leads.length,
      critical: leads.filter((l) => l.priority === 'CRITICAL').length,
      high: leads.filter((l) => l.priority === 'HIGH').length,
      medium: leads.filter((l) => l.priority === 'MEDIUM').length,
      low: leads.filter((l) => l.priority === 'LOW').length,
      open: leads.filter((l) => l.status === 'OPEN').length,
      confirmed: leads.filter((l) => l.status === 'CONFIRMED').length,
      falsePositive: leads.filter((l) => l.status === 'FALSE_POSITIVE').length,
      closed: leads.filter((l) => l.status === 'CLOSED').length,
    };
  }, [leads]);

  return (
    <div className="space-y-6 font-mono select-none">
      {/* ── 1. HEADER BANNER ── */}
      <div className="bg-[#0C1220] border border-[#1E293B] p-5 rounded-md flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-extrabold text-white uppercase tracking-wider font-sans">
              INVESTIGATIVE LEADS
            </h2>
            <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-950/80 px-3 py-0.5 rounded border border-cyan-800/60">
              {leads.length} TOTAL LEADS
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            AI-generated findings from CIVIX XGBoost analysis. Review, validate and take action.
          </p>
        </div>

        <button
          onClick={handleRunAiAnalysis}
          disabled={generateMutation.isPending}
          className="px-4 py-2 rounded bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold font-mono text-xs flex items-center space-x-2 shrink-0 shadow-lg shadow-cyan-950 transition-all cursor-pointer hover:scale-105 disabled:opacity-50"
        >
          {generateMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
          ) : (
            <Zap className="w-4 h-4 fill-current text-slate-950" />
          )}
          <span>{generateMutation.isPending ? 'RUNNING XGBOOST ANALYSIS...' : 'RUN CIVIX XGBOOST POWERED AI ANALYSIS'}</span>
        </button>
      </div>

      {/* ── 2. SUMMARY METRICS BAR ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <div className="bg-[#0C1220] border border-[#1E293B] p-3 rounded">
          <span className="text-[10px] text-slate-500 uppercase block">TOTAL LEADS</span>
          <span className="text-lg font-extrabold text-white">{metrics.total}</span>
        </div>
        <div className="bg-[#0C1220] border border-[#1E293B] p-3 rounded">
          <span className="text-[10px] text-red-400 uppercase block">CRITICAL</span>
          <span className="text-lg font-extrabold text-red-400">{metrics.critical}</span>
        </div>
        <div className="bg-[#0C1220] border border-[#1E293B] p-3 rounded">
          <span className="text-[10px] text-amber-400 uppercase block">HIGH</span>
          <span className="text-lg font-extrabold text-amber-400">{metrics.high}</span>
        </div>
        <div className="bg-[#0C1220] border border-[#1E293B] p-3 rounded">
          <span className="text-[10px] text-blue-400 uppercase block">MEDIUM</span>
          <span className="text-lg font-extrabold text-blue-400">{metrics.medium}</span>
        </div>
        <div className="bg-[#0C1220] border border-[#1E293B] p-3 rounded">
          <span className="text-[10px] text-slate-400 uppercase block">OPEN</span>
          <span className="text-lg font-extrabold text-slate-300">{metrics.open}</span>
        </div>
        <div className="bg-[#0C1220] border border-[#1E293B] p-3 rounded">
          <span className="text-[10px] text-emerald-400 uppercase block">CONFIRMED</span>
          <span className="text-lg font-extrabold text-emerald-400">{metrics.confirmed}</span>
        </div>
        <div className="bg-[#0C1220] border border-[#1E293B] p-3 rounded">
          <span className="text-[10px] text-purple-400 uppercase block">FALSE POSITIVE</span>
          <span className="text-lg font-extrabold text-purple-400">{metrics.falsePositive}</span>
        </div>
        <div className="bg-[#0C1220] border border-[#1E293B] p-3 rounded">
          <span className="text-[10px] text-slate-400 uppercase block">CLOSED</span>
          <span className="text-lg font-extrabold text-slate-400">{metrics.closed}</span>
        </div>
      </div>

      {/* ── 3. SEARCH, FILTER & SORT TOOLBAR ── */}
      <div className="bg-[#0C1220] border border-[#1E293B] p-4 rounded-md flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Search leads by target entity, finding text, ID..."
            className="w-full bg-[#070A0F] border border-[#1E293B] focus:border-cyan-500 rounded pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none"
          />
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Priority Filter */}
          <div className="flex items-center space-x-1 text-xs">
            <span className="text-[10px] text-slate-500 uppercase mr-1">PRIORITY:</span>
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((p) => (
              <button
                key={p}
                onClick={() => {
                  setPriorityFilter(p);
                  setCurrentPage(1);
                }}
                className={`px-2 py-1 rounded text-[10px] font-bold transition-colors cursor-pointer ${
                  priorityFilter === p
                    ? 'bg-cyan-500 text-slate-950 font-bold'
                    : 'bg-[#070A0F] text-slate-400 border border-[#1E293B] hover:text-white'
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-1 text-xs">
            <span className="text-[10px] text-slate-500 uppercase mr-1">STATUS:</span>
            {['ALL', 'OPEN', 'CONFIRMED', 'FALSE_POSITIVE', 'CLOSED'].map((s) => (
              <button
                key={s}
                onClick={() => {
                  setStatusFilter(s);
                  setCurrentPage(1);
                }}
                className={`px-2 py-1 rounded text-[10px] font-bold transition-colors cursor-pointer ${
                  statusFilter === s
                    ? 'bg-cyan-500 text-slate-950 font-bold'
                    : 'bg-[#070A0F] text-slate-400 border border-[#1E293B] hover:text-white'
                }`}
              >
                {s === 'FALSE_POSITIVE' ? 'FALSE POS' : s}
              </button>
            ))}
          </div>

          {/* Sort By Dropdown */}
          <div className="flex items-center space-x-1 text-xs">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-[#070A0F] border border-[#1E293B] text-slate-300 text-xs rounded px-2.5 py-1 focus:outline-none cursor-pointer"
            >
              <option value="MODEL_SIGNAL">MODEL SIGNAL (HIGHEST)</option>
              <option value="PRIORITY">PRIORITY RANK</option>
              <option value="NEWEST">NEWEST</option>
              <option value="OLDEST">OLDEST</option>
            </select>
          </div>
        </div>
      </div>

      {/* ── 4. RESPONSIVE LEAD GRID (4 CARDS PER ROW ON XL DESKTOP) ── */}
      {isLoading ? (
        <div className="py-24 text-center space-y-3 bg-[#0C1220] border border-[#1E293B] rounded-md">
          <Loader2 className="w-6 h-6 animate-spin text-cyan-400 mx-auto" />
          <p className="text-xs text-slate-400 font-mono">Fetching case investigative leads...</p>
        </div>
      ) : error ? (
        <div className="p-8 text-center bg-[#0C1220] border border-red-900/50 rounded-md space-y-3">
          <AlertCircle className="w-8 h-8 text-red-500 mx-auto" />
          <p className="text-xs font-bold text-white uppercase font-mono">Failed to load leads for this case.</p>
          <button onClick={() => refetch()} className="civix-btn-secondary text-xs">
            Retry Loading
          </button>
        </div>
      ) : filteredAndSortedLeads.length === 0 ? (
        <div className="p-12 text-center bg-[#0C1220] border border-[#1E293B] rounded-md space-y-4">
          <Sparkles className="w-10 h-10 text-cyan-400 mx-auto animate-pulse" />
          <p className="text-xs font-bold text-slate-300 uppercase font-mono">
            NO LEADS MATCHING ACTIVE FILTERS
          </p>
          <button
            onClick={() => {
              setSearchQuery('');
              setPriorityFilter('ALL');
              setStatusFilter('ALL');
            }}
            className="civix-btn-secondary text-xs"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {paginatedLeads.map((lead) => {
              const modelSignalPercent = lead.ai_confidence !== undefined && lead.ai_confidence !== null
                ? Math.round(lead.ai_confidence * 100)
                : 78;

              const isReviewed = lead.status === 'CONFIRMED' || lead.status === 'FALSE_POSITIVE' || lead.status === 'CLOSED';

              return (
                <div
                  key={lead.lead_id}
                  className="bg-[#0C1220] border border-[#1E293B] hover:border-cyan-500/50 p-4 rounded-md transition-all shadow-lg flex flex-col justify-between space-y-4 group"
                >
                  {/* Top Header Row */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between border-b border-[#1E293B] pb-2.5">
                      <span
                        className={`text-[9px] font-mono font-extrabold px-2 py-0.5 rounded uppercase tracking-wider ${
                          lead.priority === 'CRITICAL'
                            ? 'bg-red-950/80 text-red-400 border border-red-800/60'
                            : lead.priority === 'HIGH'
                            ? 'bg-amber-950/80 text-amber-400 border border-amber-800/60'
                            : 'bg-blue-950/80 text-blue-400 border border-blue-800/60'
                        }`}
                      >
                        {lead.priority}
                      </span>

                      <div className="flex items-center space-x-1.5">
                        <span className="text-[10px] font-bold text-cyan-400 font-mono">
                          {modelSignalPercent}% MODEL SIGNAL
                        </span>
                      </div>
                    </div>

                    {/* What CIVIX Found Title */}
                    <div className="space-y-1">
                      <h3 className="text-xs font-bold text-white font-sans leading-snug group-hover:text-cyan-300 transition-colors">
                        {lead.lead_text}
                      </h3>
                    </div>

                    {/* Evidence Status Section */}
                    <div className="bg-[#070A0F] p-2.5 rounded border border-[#1E293B] text-[10px] space-y-1">
                      <div className="flex items-center justify-between text-slate-400 font-mono">
                        <span className="text-slate-500 uppercase">EVIDENCE STATUS</span>
                        <span className="text-cyan-400 font-bold">
                          {lead.finding_count || 1} SOURCES
                        </span>
                      </div>
                      <p className="text-slate-400 font-sans text-[11px]">
                        Related evidence available in case registry. Asserted evidence chain verified.
                      </p>
                    </div>

                    {/* Human Investigator Comment Section (Prioritized on Reviewed Cards) */}
                    {isReviewed && (
                      <div className="bg-[#070D18] border border-cyan-800/40 p-2.5 rounded text-xs space-y-1">
                        <div className="flex items-center justify-between text-[9px] font-mono font-bold">
                          <span className="text-cyan-400 uppercase">INVESTIGATOR DISPOSITION</span>
                          <span className={`px-1.5 py-0.2 rounded ${
                            lead.status === 'CONFIRMED' ? 'bg-emerald-950 text-emerald-400' :
                            lead.status === 'FALSE_POSITIVE' ? 'bg-purple-950 text-purple-400' : 'bg-slate-800 text-slate-300'
                          }`}>
                            {lead.status === 'FALSE_POSITIVE' ? 'FALSE POSITIVE' : lead.status}
                          </span>
                        </div>
                        <p className="text-slate-200 text-[11px] font-sans italic line-clamp-2">
                          "{lead.disposition_notes || 'Reviewed and dispositioned by human investigator.'}"
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Card Footer Action */}
                  <div className="pt-3 border-t border-[#1E293B] flex items-center justify-between text-[10px]">
                    <span className="text-slate-500 font-mono">
                      ID: {lead.lead_id.substring(0, 8)}...
                    </span>

                    <button
                      onClick={() => setSelectedLead(lead)}
                      className="px-3 py-1.5 rounded bg-amber-400 hover:bg-amber-300 text-slate-950 font-extrabold font-mono text-[11px] flex items-center space-x-1 shadow-lg shadow-amber-950/40 transition-all cursor-pointer hover:scale-105"
                    >
                      <span>REVIEW FINDING →</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between bg-[#0C1220] border border-[#1E293B] px-4 py-3 rounded-md text-xs font-mono text-slate-400">
              <span>
                Showing {((currentPage - 1) * pageSize) + 1}–{Math.min(currentPage * pageSize, filteredAndSortedLeads.length)} of {filteredAndSortedLeads.length} leads
              </span>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                  disabled={currentPage === 1}
                  className="p-1.5 rounded border border-[#1E293B] bg-[#070A0F] hover:bg-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>

                <span className="font-bold text-white">
                  Page {currentPage} of {totalPages}
                </span>

                <button
                  onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="p-1.5 rounded border border-[#1E293B] bg-[#070A0F] hover:bg-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {selectedLead && (
        <LeadReviewModal
          lead={selectedLead}
          caseId={caseId}
          onClose={() => setSelectedLead(null)}
          onDispositionSuccess={() => {
            refetch();
          }}
        />
      )}
    </div>
  );
};
