import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { leadsApi } from '../../api/leads';
import { useCaseSelection } from '../../context/CaseSelectionContext';
import { Panel } from '../ui/Panel';
import { HierarchyBadge } from './HierarchyBadge';
import { LeadReviewModal } from './LeadReviewModal';
import type { InvestigativeLeadResponse } from '../../types/api';
import { ArrowRight, Loader2, FileText, RefreshCw } from 'lucide-react';



export const PriorityLeadsWidget: React.FC = () => {
  const { selectedCaseId } = useCaseSelection();
  const [activeReviewLead, setActiveReviewLead] = React.useState<InvestigativeLeadResponse | null>(null);
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
      title="NEW INVESTIGATIVE SIGNAL"
      subtitle="C3 Intelligence Engine — ML & Deterministic Findings"
      accent="red"
      headerAction={
        <div className="flex items-center space-x-2">
          {selectedCaseId && (
            <button
              onClick={() => generateMutation.mutate()}
              disabled={generateMutation.isPending}
              className="civix-btn-gold flex items-center space-x-1.5 disabled:opacity-50"
            >
              {generateMutation.isPending ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              <span>Run C3 Analysis</span>
            </button>
          )}
          <button className="text-[11px] font-semibold text-civix-blue-light hover:text-civix-text-primary flex items-center space-x-1 transition-colors font-mono">
            <span>View All Leads</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>
      }
      className="h-full"
    >
      {!selectedCaseId ? (
        <div className="py-10 text-center text-xs text-civix-text-muted font-mono">
          Select an active case to view priority investigative signals.
        </div>
      ) : isLoading ? (
        <div className="py-10 flex items-center justify-center text-civix-text-muted space-x-2 text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-civix-blue-light" />
          <span>Evaluating C3 model signals...</span>
        </div>
      ) : error ? (
        <div className="py-8 text-center text-xs text-civix-red font-mono">
          Failed to fetch investigative leads.
        </div>
      ) : !topLead ? (
        <div className="py-8 text-center space-y-3">
          <p className="text-xs text-civix-text-muted font-mono">No leads generated for this case yet.</p>
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="civix-btn-primary inline-flex items-center space-x-2"
          >
            {generateMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            <span>Generate C3 Investigative Leads</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Priority Lead Card — HIGH SIGNAL */}
          <div className="border border-civix-red-muted bg-civix-red-subtle rounded-sm p-4 space-y-3">
            {/* Header: priority signal label + status */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-civix-border">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-civix-red animate-pulse" />
                <span className="text-xs font-extrabold font-mono text-civix-text-primary uppercase tracking-widest">
                  HIGH PRIORITY
                </span>
                <span className="text-civix-text-muted text-[10px] font-mono">·</span>
                <span className="text-[10px] font-mono text-civix-text-muted">
                  TARGET: {topLead.target_entity_id ? `ID ${topLead.target_entity_id.substring(0, 8)}...` : 'LEAD CANDIDATE'}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <HierarchyBadge tier="MODEL_SIGNAL" />
                <span className="text-[10px] font-mono font-bold text-civix-gold bg-civix-gold-subtle px-2 py-0.5 rounded-sm border border-civix-gold-muted">
                  SCORE: {topLead.ai_confidence ? topLead.ai_confidence.toFixed(3) : 'N/A'}
                </span>
                <span className="text-[10px] font-mono font-bold text-civix-gold-light bg-civix-gold-subtle px-2 py-0.5 rounded-sm border border-civix-gold-muted uppercase tracking-widest">
                  {topLead.status === 'OPEN' ? 'PENDING REVIEW' : topLead.status}
                </span>
              </div>
            </div>

            {/* Intelligence Summary */}
            <div className="space-y-1">
              <div className="text-[9px] font-mono font-bold text-civix-text-muted uppercase tracking-widest">
                INTELLIGENCE SUMMARY
              </div>
              <h4 className="text-sm font-bold text-civix-text-primary leading-snug font-sans">
                {topLead.lead_text}
              </h4>
            </div>

            {/* Why This Matters — Deterministic Finding */}
            <div className="bg-civix-surface-2 p-3 rounded-sm border border-civix-border space-y-1.5">
              <div className="text-[9px] font-mono font-bold text-civix-text-muted uppercase tracking-widest flex items-center space-x-1.5">
                <HierarchyBadge tier="DETERMINISTIC_FINDING" />
                <span>WHY THIS MATTERS</span>
              </div>
              <p className="text-xs font-semibold text-civix-text-primary pl-1 leading-relaxed">
                {topLead.findings && topLead.findings.length > 0
                  ? topLead.findings[0].finding_text
                  : 'ML behavioral anomaly signal evaluated without direct deterministic finding.'}
              </p>
            </div>

            {/* Evidence footer + actions */}
            <div className="flex flex-wrap items-center justify-between text-[10px] font-mono text-civix-text-muted pt-1 gap-3 border-t border-civix-border-subtle">
              <div className="flex items-center space-x-3">
                <span className="flex items-center font-bold text-civix-text-secondary">
                  <FileText className="w-3 h-3 mr-1 text-civix-text-muted" />
                  {topLead.finding_count || topLead.findings?.length || 0} SOURCES
                </span>
                <span className="text-civix-border-strong">·</span>
                <span className="text-civix-text-muted">
                  Model: {topLead.feature_vector_version || 'behavioral_xgboost_v1'}
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setActiveReviewLead(topLead)}
                  className="px-4 py-1.5 bg-civix-red hover:bg-civix-red-light text-white rounded-sm text-xs font-bold font-mono transition-colors"
                >
                  VIEW FULL DETAILS
                </button>
                <button
                  onClick={() => setActiveReviewLead(topLead)}
                  className="civix-btn-secondary px-3 py-1.5 text-xs"
                >
                  Review Lead
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
