import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { casesApi } from '../api/cases';
import { useCaseSelection } from '../context/CaseSelectionContext';
import { Badge } from '../components/ui/Badge';
import { ArrowLeft, Briefcase, Loader2, AlertTriangle, GitFork, ChevronRight } from 'lucide-react';

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

export const CaseWorkspacePage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const { setSelectedCaseId } = useCaseSelection();

  const { data: caseData, isLoading, error } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => (caseId ? casesApi.getCase(caseId) : Promise.reject(new Error('No case ID'))),
    enabled: !!caseId,
    retry: 1,
  });

  // Sync selected case context on load
  React.useEffect(() => {
    if (caseId) setSelectedCaseId(caseId);
  }, [caseId, setSelectedCaseId]);

  function handleBack() {
    navigate('/cases');
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24 space-x-2 text-slate-400">
        <Loader2 className="w-5 h-5 animate-spin text-amber-600" />
        <span className="text-xs font-mono">Loading case workspace...</span>
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div className="py-12 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-red-400 mx-auto" />
        <div>
          <p className="text-sm font-bold text-slate-900 uppercase tracking-wide">Case Not Found</p>
          <p className="text-xs text-slate-500 mt-1">
            Case ID <span className="font-mono">{caseId}</span> could not be retrieved.
            It may not exist or you may not have access.
          </p>
        </div>
        <button
          onClick={handleBack}
          className="inline-flex items-center space-x-2 px-4 py-2 text-xs font-semibold text-white bg-slate-900 rounded hover:bg-slate-800 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Case Registry</span>
        </button>
      </div>
    );
  }

  const statusVariant = STATUS_VARIANTS[caseData.status?.toUpperCase()] || 'default';
  const priorityVariant = PRIORITY_VARIANTS[caseData.priority?.toUpperCase()] || 'default';

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-slate-200 gap-3">
        <div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleBack}
              className="flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Cases</span>
            </button>
            <span className="text-slate-300">/</span>
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight uppercase">
              {caseData.case_number}
            </h1>
            <Badge variant={statusVariant as any}>{caseData.status}</Badge>
            <Badge variant={priorityVariant as any}>{caseData.priority}</Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 font-medium">{caseData.title}</p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono text-slate-600 bg-white border border-slate-200 px-3 py-1.5 rounded shadow-2xs">
          <Briefcase className="w-3.5 h-3.5 text-amber-600" />
          <span className="font-bold text-slate-800">{caseData.jurisdiction}</span>
          <span className="text-slate-300">·</span>
          <span>{caseData.case_type}</span>
        </div>
      </div>

      {/* Workspace Placeholder */}
      <div className="bg-white border border-slate-200 rounded shadow-sm p-10 text-center space-y-4">
        <Briefcase className="w-10 h-10 text-slate-200 mx-auto" />
        <div className="space-y-1.5">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
            Case Workspace — {caseData.case_number}
          </h2>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            The full Case Workspace (leads, entities, evidence, graph, timeline) will be
            implemented in the next authorized frontend phase.
          </p>
          <p className="text-[11px] font-mono text-slate-400">
            Case ID: {caseData.case_id}
          </p>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-lg mx-auto pt-4 border-t border-slate-100">
          {[
            { label: 'Status', value: caseData.status },
            { label: 'Priority', value: caseData.priority },
            { label: 'Type', value: caseData.case_type },
            { label: 'Jurisdiction', value: caseData.jurisdiction },
          ].map(({ label, value }) => (
            <div key={label} className="text-left">
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{label}</p>
              <p className="text-xs font-semibold font-mono text-slate-800 mt-0.5">{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Workspace Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl">
        <button
          onClick={() => navigate(`/cases/${caseId}/graph`)}
          className="flex items-center justify-between px-4 py-3 bg-white border border-slate-200 rounded shadow-sm hover:border-slate-300 hover:bg-slate-50 transition-colors group"
        >
          <div className="flex items-center space-x-3">
            <GitFork className="w-5 h-5 text-slate-500 group-hover:text-slate-700" />
            <div className="text-left">
              <p className="text-xs font-bold text-slate-900">Investigative Graph</p>
              <p className="text-[10px] text-slate-500">Relationship network · Neo4j projection</p>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-700" />
        </button>
        <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border border-slate-200 rounded opacity-60 cursor-not-allowed">
          <div className="flex items-center space-x-3">
            <Briefcase className="w-5 h-5 text-slate-400" />
            <div className="text-left">
              <p className="text-xs font-bold text-slate-500">Evidence Explorer</p>
              <p className="text-[10px] text-slate-400">Authorized in a future phase</p>
            </div>
          </div>
          <span className="text-[9px] font-mono font-bold text-slate-400 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded">PHASE 5</span>
        </div>
      </div>
    </div>
  );
};
