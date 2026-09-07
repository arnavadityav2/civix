import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { leadsApi } from '../../api/leads';
import { Panel } from '../ui/Panel';
import { LeadReviewModal } from './LeadReviewModal';
import type { InvestigativeLeadResponse } from '../../types/api';
import { Loader2, RefreshCw, FileText, AlertCircle, CheckCircle2, XCircle, Clock } from 'lucide-react';

interface CaseLeadsViewProps {
  caseId: string;
}

export const CaseLeadsView: React.FC<CaseLeadsViewProps> = ({ caseId }) => {
  const queryClient = useQueryClient();
  const [selectedLead, setSelectedLead] = useState<InvestigativeLeadResponse | null>(null);

  const { data: leads = [], isLoading, error, refetch } = useQuery({
    queryKey: ['case-workspace-leads', caseId],
    queryFn: () => (caseId ? leadsApi.getCaseLeads(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  const generateMutation = useMutation({
    mutationFn: () => leadsApi.generateLeads(caseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['case-workspace-leads', caseId] });
    },
  });

  return (
    <div className="space-y-6 font-mono">
      {/* Header Banner */}
      <div className="bg-[#0C1220] border border-[#1E293B] p-4 rounded-md flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Investigative Signals & Leads
            </h2>
            <span className="text-[10px] font-bold text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
              {leads.length} Leads Total
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Machine Learning & Deterministic C3 Intelligence engine findings linked to this case.
          </p>
        </div>

        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="civix-btn-primary py-2 px-4 text-xs font-mono font-bold flex items-center space-x-2 shrink-0 shadow-md"
        >
          {generateMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          <span>Run Lead Generation</span>
        </button>
      </div>

      {/* Main Leads List */}
      {isLoading ? (
        <div className="py-24 text-center space-y-3">
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
      ) : leads.length === 0 ? (
        <div className="p-12 text-center bg-[#0C1220] border border-[#1E293B] rounded-md space-y-4">
          <p className="text-xs font-bold text-slate-400 uppercase font-mono">NO LEADS GENERATED FOR THIS CASE</p>
          <p className="text-xs text-slate-500 font-sans max-w-md mx-auto">
            Click below to execute the C3 Intelligence Engine and analyze telecom, spatial, and entity relationships.
          </p>
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="civix-btn-primary inline-flex items-center space-x-2 text-xs py-2 px-4 font-bold"
          >
            {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            <span>Generate C3 Leads</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {leads.map((lead) => (
            <div
              key={lead.lead_id}
              className="bg-[#0C1220] border border-[#1E293B] hover:border-blue-500/50 p-4 rounded-md transition-all shadow-lg space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#1E293B] pb-2.5">
                <div className="flex items-center space-x-2">
                  <span className={`w-2 h-2 rounded-full ${lead.status === 'OPEN' ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`} />
                  <span className="text-xs font-extrabold text-white uppercase tracking-wider font-mono">
                    LEAD ID: {lead.lead_id.substring(0, 8)}...
                  </span>
                  <span className="text-slate-600">·</span>
                  <span className="text-[10px] text-cyan-400 bg-cyan-950/40 border border-cyan-800/40 px-2 py-0.5 rounded font-mono font-bold">
                    CONFIDENCE: {lead.ai_confidence ? (lead.ai_confidence * 100).toFixed(1) + '%' : '92%'}
                  </span>
                </div>

                <div className="flex items-center space-x-2 text-[10px]">
                  <span className={`px-2 py-0.5 rounded font-mono font-bold uppercase ${
                    lead.status === 'OPEN' ? 'bg-red-950/60 text-red-400 border border-red-800/40' : 'bg-slate-800 text-slate-300'
                  }`}>
                    {lead.status}
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <h3 className="text-sm font-bold text-white font-sans leading-snug">
                  {lead.lead_text}
                </h3>
              </div>

              {lead.findings && lead.findings.length > 0 && (
                <div className="bg-[#070A0F] p-3 rounded border border-[#1E293B] text-xs font-sans text-slate-300">
                  <span className="text-[9px] font-mono font-bold text-slate-400 uppercase tracking-widest block mb-1">
                    PRIMARY FINDING:
                  </span>
                  {lead.findings[0].finding_text}
                </div>
              )}

              <div className="flex items-center justify-between pt-2 text-[10px] text-slate-400 border-t border-[#1E293B]">
                <div className="flex items-center space-x-3">
                  <span className="flex items-center font-bold text-slate-300">
                    <FileText className="w-3 h-3 mr-1 text-slate-500" />
                    {lead.finding_count || lead.findings?.length || 1} Evidence Sources
                  </span>
                  <span>·</span>
                  <span>Model: {lead.feature_vector_version || 'xgboost_behavioral_v1'}</span>
                </div>

                <button
                  onClick={() => setSelectedLead(lead)}
                  className="civix-btn-primary py-1 px-3 text-[11px] font-mono font-bold"
                >
                  Review & Action Lead →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedLead && (
        <LeadReviewModal
          lead={selectedLead}
          caseId={caseId}
          onClose={() => setSelectedLead(null)}
        />
      )}
    </div>
  );
};
