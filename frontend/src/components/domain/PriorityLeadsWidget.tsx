import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { leadsApi } from '../../api/leads';
import { useCaseSelection } from '../../context/CaseSelectionContext';
import { Panel } from '../ui/Panel';
import { HierarchyBadge } from './HierarchyBadge';
import { LeadReviewModal } from './LeadReviewModal';
import type { InvestigativeLeadResponse } from '../../types/api';
import { ArrowRight, Sparkles, Loader2, FileText } from 'lucide-react';



export const PriorityLeadsWidget: React.FC = () => {
  const { selectedCaseId } = useCaseSelection();
  const [activeReviewLead, setActiveReviewLead] = useState<InvestigativeLeadResponse | null>(null);
  const queryClient = useQueryClient();

  const { data: leads = [], isLoading, error } = useQuery({
    queryKey: ['leads', selectedCaseId],
    queryFn: () => (selectedCaseId ? leadsApi.getCaseLeads(selectedCaseId) : Promise.resolve([])),
    enabled: !!selectedCaseId,
  });

  const generateMutation = useMutation({
    mutationFn: () => (selectedCaseId ? leadsApi.generateLeads(selectedCaseId) : Promise.reject('No case selected')),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads', selectedCaseId] });
    },
  });

  // Filter to open/pending leads
  const openLeads = leads.filter((l) => l.status === 'OPEN' || l.status === 'IN_PROGRESS');
  const topLead = openLeads.length > 0 ? openLeads[0] : leads[0] || null;

  return (
    <Panel
      title="PRIORITY INVESTIGATIVE LEADS"
      subtitle="C3 Intelligence Engine ML & Deterministic Findings"
      headerAction={
        <div className="flex items-center space-x-2">
          {selectedCaseId && (
            <button
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className="text-xs font-semibold bg-amber-50 text-amber-900 border border-amber-300 hover:bg-amber-100 px-2.5 py-1 rounded flex items-center space-x-1.5 transition-colors disabled:opacity-50"
            >
              {generateMutation.isPending ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-700" />
              ) : (
                <Sparkles className="w-3.5 h-3.5 text-amber-700" />
              )}
              <span>Run C3 Analysis</span>
            </button>
          )}
          <button className="text-xs font-semibold text-blue-700 hover:text-blue-900 flex items-center space-x-1">
            <span>View All Leads</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      }
      className="h-full"
    >
      {!selectedCaseId ? (
        <div className="py-12 text-center text-xs text-slate-500 font-mono">
          Select an active case to view priority investigative leads.
        </div>
      ) : isLoading ? (
        <div className="py-12 flex items-center justify-center text-slate-400 space-x-2 text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-amber-600" />
          <span>Evaluating C3 model signals...</span>
        </div>
      ) : error ? (
        <div className="py-8 text-center text-xs text-red-600 font-mono">
          Failed to fetch investigative leads.
        </div>
      ) : !topLead ? (
        <div className="py-8 text-center space-y-3">
          <p className="text-xs text-slate-500 font-mono">No leads generated for this case yet.</p>
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="px-4 py-2 bg-slate-900 text-white rounded text-xs font-semibold hover:bg-slate-800 transition-colors inline-flex items-center space-x-2"
          >
            {generateMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4 text-amber-400" />
            )}
            <span>Generate C3 Investigative Leads</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Top Priority Lead Card */}
          <div className="bg-white border-l-4 border-l-amber-600 border border-slate-200 rounded p-4 shadow-xs space-y-3.5">
            {/* Header: Target Subject & Model Signal */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-3 gap-2">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-extrabold font-mono text-slate-900 uppercase tracking-wide">
                    TARGET ENTITY: {topLead.target_entity_id ? `ID ${topLead.target_entity_id.substring(0, 8)}...` : 'LEAD CANDIDATE'}
                  </span>

                  <span className="text-[10px] font-mono text-slate-400">•</span>
                  <span className="text-xs text-slate-600 font-medium truncate">
                    Lead ID: {topLead.lead_id.substring(0, 8)}...
                  </span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <HierarchyBadge tier="MODEL_SIGNAL" />
                <span className="text-xs font-mono font-bold text-amber-900 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  SCORE: {topLead.ai_confidence ? topLead.ai_confidence.toFixed(3) : 'N/A'}
                </span>
                <span className="text-[10px] font-mono font-bold text-amber-800 bg-amber-100/80 px-2 py-0.5 rounded border border-amber-300 uppercase tracking-wider">
                  {topLead.status === 'OPEN' ? 'PENDING REVIEW' : topLead.status}
                </span>
              </div>
            </div>

            {/* Narrative Story Section: Lead Summary */}
            <div className="space-y-1">
              <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                INTELLIGENCE SUMMARY
              </div>
              <h4 className="text-sm font-bold text-slate-900 leading-snug font-sans">
                {topLead.lead_text}
              </h4>
            </div>

            {/* WHY THIS MATTERS Section: Deterministic Finding */}
            <div className="bg-slate-50 p-3 rounded border border-slate-200 space-y-1">
              <div className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider flex items-center space-x-1.5">
                <HierarchyBadge tier="DETERMINISTIC_FINDING" />
                <span>WHY THIS MATTERS</span>
              </div>
              <p className="text-xs font-semibold text-slate-800 pl-1">
                {topLead.findings && topLead.findings.length > 0
                  ? topLead.findings[0].finding_text
                  : 'ML behavioral anomaly signal evaluated without direct deterministic finding.'}
              </p>
            </div>

            {/* EVIDENCE & ACTION FOOTER */}
            <div className="flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-600 pt-1 gap-3 border-t border-slate-100">
              <div className="flex items-center space-x-3 text-slate-500">
                <span className="flex items-center font-bold text-slate-700">
                  <FileText className="w-3.5 h-3.5 mr-1 text-slate-400" />
                  {topLead.finding_count || topLead.findings?.length || 0} SOURCES
                </span>
                <span>•</span>
                <span className="text-slate-400">
                  Model: {topLead.feature_vector_version || 'behavioral_xgboost_v1'}
                </span>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center space-x-2">

                <button
                  onClick={() => setActiveReviewLead(topLead)}
                  className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-bold shadow-2xs transition-colors"
                >
                  REVIEW LEAD
                </button>
                <button
                  onClick={() => setActiveReviewLead(topLead)}
                  className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded text-xs font-semibold transition-colors"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>

      )}

      {/* Review / Disposition Modal */}
      {activeReviewLead && selectedCaseId && (
        <LeadReviewModal
          lead={activeReviewLead}
          caseId={selectedCaseId}
          onClose={() => setActiveReviewLead(null)}
        />
      )}
    </Panel>
  );
};
