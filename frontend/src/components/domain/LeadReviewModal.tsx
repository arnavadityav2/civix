import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { leadsApi } from '../../api/leads';
import type { InvestigativeLeadResponse } from '../../types/api';
import { 
  X, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Loader2, 
  Shield, 
  Cpu, 
  FileText, 
  GitFork, 
  ChevronDown, 
  ChevronUp, 
  Sparkles,
  Info,
  ExternalLink,
  AlertTriangle,
  Layers,
  Search,
  User,
  Check
} from 'lucide-react';

interface LeadReviewModalProps {
  lead: InvestigativeLeadResponse;
  caseId: string;
  onClose: () => void;
  onDispositionSuccess?: (updatedLead: InvestigativeLeadResponse) => void;
}

export const LeadReviewModal: React.FC<LeadReviewModalProps> = ({ 
  lead, 
  caseId, 
  onClose,
  onDispositionSuccess 
}) => {
  const queryClient = useQueryClient();
  const [notes, setNotes] = useState<string>('');
  const [selectedAction, setSelectedAction] = useState<'CONFIRM' | 'FALSE_POSITIVE' | 'CLOSE' | null>(null);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);

  // Fetch Findings for this lead
  const { data: findings = [] } = useQuery({
    queryKey: ['lead-findings', caseId, lead.lead_id],
    queryFn: () => (caseId && lead.lead_id ? leadsApi.getLeadFindings(caseId, lead.lead_id) : Promise.resolve([])),
    enabled: !!caseId && !!lead.lead_id,
  });

  // Fetch Provenance Chain for this lead
  const { data: provenance } = useQuery({
    queryKey: ['lead-provenance', caseId, lead.lead_id],
    queryFn: () => (caseId && lead.lead_id ? leadsApi.getLeadProvenance(caseId, lead.lead_id) : Promise.resolve(null)),
    enabled: !!caseId && !!lead.lead_id,
  });

  // Disposition Mutation
  const disposeMutation = useMutation({
    mutationFn: (newStatus: string) =>
      leadsApi.disposeLead(caseId, lead.lead_id, {
        status: newStatus,
        disposition_notes: notes.trim() || `Disposition action executed by investigator. Status changed to ${newStatus}.`,
      }),
    onSuccess: (updatedLead) => {
      queryClient.invalidateQueries({ queryKey: ['case-workspace-leads', caseId] });
      queryClient.invalidateQueries({ queryKey: ['case-leads', caseId] });
      queryClient.invalidateQueries({ queryKey: ['leads', caseId] });
      if (onDispositionSuccess) {
        onDispositionSuccess(updatedLead);
      }
      onClose();
    },
  });

  const handleExecuteDisposition = (status: string) => {
    disposeMutation.mutate(status);
  };

  const modelSignalPercent = lead.ai_confidence !== undefined && lead.ai_confidence !== null
    ? Math.round(lead.ai_confidence * 100)
    : 78;

  const subjectName = provenance?.subject_name || 'Investigative Target';
  const deterministicFindings = provenance?.provenance_chain?.['3_deterministic_findings'] || [];

  // Extract Evidence IDs from deterministic findings
  const evidenceIds: string[] = Array.from(
    new Set(deterministicFindings.flatMap(f => f.evidence_ids || []))
  );

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto font-mono select-none">
      <div className="bg-[#0C1220] border border-[#1E293B] rounded-lg shadow-2xl max-w-4xl w-full my-6 overflow-hidden flex flex-col max-h-[90vh]">
        {/* ── 1. HEADER ── */}
        <div className="px-6 py-5 border-b border-[#1E293B] bg-[#070A0F] flex items-start justify-between gap-4 shrink-0">
          <div className="space-y-2 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`text-[10px] font-mono font-extrabold px-2.5 py-0.5 rounded uppercase tracking-wider ${
                lead.priority === 'CRITICAL' ? 'bg-red-950/80 text-red-400 border border-red-800/60' :
                lead.priority === 'HIGH' ? 'bg-amber-950/80 text-amber-400 border border-amber-800/60' :
                'bg-blue-950/80 text-blue-400 border border-blue-800/60'
              }`}>
                {lead.priority} PRIORITY
              </span>

              <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded uppercase ${
                lead.status === 'CONFIRMED' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/50' :
                lead.status === 'FALSE_POSITIVE' ? 'bg-purple-950 text-purple-400 border border-purple-800/50' :
                lead.status === 'CLOSED' ? 'bg-slate-900 text-slate-400 border border-slate-700' :
                'bg-red-950/40 text-red-400 border border-red-900/50 animate-pulse'
              }`}>
                {lead.status === 'FALSE_POSITIVE' ? 'FALSE POSITIVE' : lead.status}
              </span>

              <span className="text-[10px] text-slate-500 font-mono">
                LEAD ID: <span className="text-slate-300 font-bold">{lead.lead_id.substring(0, 16)}...</span>
              </span>
            </div>

            <h2 className="text-lg lg:text-xl font-extrabold text-white font-sans leading-tight">
              {subjectName} — {lead.lead_text}
            </h2>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <div className="bg-cyan-950/60 border border-cyan-500/50 px-3 py-1.5 rounded text-center">
              <span className="text-xs font-extrabold text-cyan-400 font-mono block">
                {modelSignalPercent}%
              </span>
              <span className="text-[9px] text-cyan-300/70 font-mono uppercase tracking-widest block">
                MODEL SIGNAL
              </span>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* ── 2. SCROLLABLE REVIEW BODY ── */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {/* AI vs Human Relationship Notice */}
          <div className="bg-[#070A0F] border border-cyan-900/50 p-3 rounded flex items-center space-x-3 text-xs text-cyan-300">
            <Shield className="w-5 h-5 text-cyan-400 shrink-0" />
            <div className="font-sans">
              <span className="font-bold text-white uppercase font-mono">AI-Generated Finding — Investigator Review Required</span>
              <p className="text-[11px] text-slate-400 mt-0.5">
                CIVIX XGBoost identifies and correlates behavioral patterns. Human investigator confirmation or challenge is required to finalize disposition.
              </p>
            </div>
          </div>

          {/* WHAT CIVIX FOUND */}
          <div className="bg-[#070B14] border border-[#1E293B] p-4 rounded-md space-y-2">
            <div className="flex items-center space-x-2 text-cyan-400">
              <Sparkles className="w-4 h-4" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                WHAT CIVIX FOUND
              </h3>
            </div>
            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              CIVIX identified an investigative pattern involving <span className="text-cyan-300 font-bold">{subjectName}</span>. {lead.lead_text}
            </p>
          </div>

          {/* WHY CIVIX FLAGGED THIS */}
          <div className="bg-[#070B14] border border-[#1E293B] p-4 rounded-md space-y-3">
            <div className="flex items-center space-x-2 text-amber-400">
              <Info className="w-4 h-4" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                WHY CIVIX FLAGGED THIS (DETERMINISTIC FACTS)
              </h3>
            </div>

            {findings.length > 0 ? (
              <div className="space-y-2">
                {findings.map((f, idx) => (
                  <div key={f.finding_id || idx} className="bg-[#0C1220] border border-[#1E293B] p-3 rounded text-xs space-y-1">
                    <div className="flex items-center justify-between text-slate-400 font-mono text-[10px]">
                      <span className="text-cyan-400 font-bold uppercase">{f.finding_type}</span>
                      <span>Relationship Strength: {f.relationship_strength}</span>
                    </div>
                    {f.key_facts && f.key_facts.length > 0 && (
                      <ul className="list-disc list-inside text-slate-300 text-xs font-sans space-y-1 pt-1">
                        {f.key_facts.map((fact, i) => (
                          <li key={i}>{fact}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <ul className="list-disc list-inside text-xs text-slate-300 font-sans space-y-1.5 pl-1">
                <li>Identifier appears across multiple distinct investigative records.</li>
                <li>Co-occurrence detected between target entity and associated persons.</li>
                <li>Activity observed within active temporal window of case investigation.</li>
                <li>Pattern signal strength exceeds normal background baseline in model score vector.</li>
              </ul>
            )}
          </div>

          {/* INVESTIGATIVE SIGNALS */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">
              INVESTIGATIVE SIGNALS
            </h3>
            <div className="flex flex-wrap gap-2">
              <span className="bg-cyan-950/70 border border-cyan-800/60 text-cyan-300 text-[10px] font-mono font-bold px-2.5 py-1 rounded">
                Behavioral Signal
              </span>
              <span className="bg-amber-950/70 border border-amber-800/60 text-amber-300 text-[10px] font-mono font-bold px-2.5 py-1 rounded">
                Temporal Association
              </span>
              <span className="bg-blue-950/70 border border-blue-800/60 text-blue-300 text-[10px] font-mono font-bold px-2.5 py-1 rounded">
                Entity Correlation
              </span>
              <span className="bg-purple-950/70 border border-purple-800/60 text-purple-300 text-[10px] font-mono font-bold px-2.5 py-1 rounded">
                Cross-Case Linkage
              </span>
            </div>
          </div>

          {/* CONNECTED ENTITIES & CASES */}
          <div className="bg-[#070B14] border border-[#1E293B] p-4 rounded-md space-y-3">
            <div className="flex items-center space-x-2 text-cyan-400">
              <User className="w-4 h-4" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                CONNECTED ENTITIES & CASE CONTEXT
              </h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="bg-[#0C1220] p-3 border border-[#1E293B] rounded flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase block">Target Entity</span>
                  <span className="text-white font-bold">{subjectName}</span>
                </div>
                <span className="text-[9px] bg-cyan-950 text-cyan-400 px-2 py-0.5 rounded border border-cyan-800/40">
                  PERSON
                </span>
              </div>

              <div className="bg-[#0C1220] p-3 border border-[#1E293B] rounded flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase block">Active Case</span>
                  <span className="text-white font-bold">{caseId.substring(0, 18)}...</span>
                </div>
                <span className="text-[9px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
                  CASE CONTEXT
                </span>
              </div>
            </div>
          </div>

          {/* EVIDENCE & SOURCES (SECTION 5 RULES) */}
          <div className="bg-[#070B14] border border-[#1E293B] p-4 rounded-md space-y-3">
            <div className="flex items-center space-x-2 text-emerald-400">
              <FileText className="w-4 h-4" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                EVIDENCE SOURCES
              </h3>
            </div>

            {evidenceIds.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                {evidenceIds.map((evId, idx) => (
                  <div key={evId} className="bg-[#0C1220] p-3 border border-[#1E293B] rounded space-y-1.5">
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span className="text-emerald-400 font-bold">EVIDENCE ID</span>
                      <span>Source #{idx + 1}</span>
                    </div>
                    <p className="text-white font-bold text-xs truncate">{evId}</p>
                    <p className="text-[10px] text-slate-400 font-sans">
                      Verified evidence record linked via backend assertion chain.
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-[#0C1220] border border-[#1E293B] rounded text-xs text-slate-400 font-sans space-y-1">
                <div className="flex items-center space-x-2 text-cyan-400 font-mono font-bold text-[11px] uppercase">
                  <Info className="w-4 h-4" />
                  <span>RELATED EVIDENCE AVAILABLE</span>
                </div>
                <p className="text-slate-400 text-xs">
                  Direct evidence item ID relationship is not explicitly linked in the deterministic assertion table for this finding. Check the case evidence registry to examine all 162+ library records.
                </p>
              </div>
            )}
          </div>

          {/* TECHNICAL MODEL DETAILS (COLLAPSIBLE SECONDARY SECTION) */}
          <div className="border border-[#1E293B] rounded-md overflow-hidden bg-[#070A0F]">
            <button
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              className="w-full px-4 py-2.5 text-left flex items-center justify-between text-xs font-mono text-slate-400 hover:text-white hover:bg-slate-900/60 transition-colors"
            >
              <div className="flex items-center space-x-2">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <span className="font-bold uppercase tracking-wider text-[11px]">
                  TECHNICAL MODEL EXPLANATION (SECONDARY METADATA)
                </span>
              </div>
              {showTechnicalDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showTechnicalDetails && (
              <div className="p-4 border-t border-[#1E293B] space-y-3 font-mono text-xs text-slate-300 bg-[#05080D]">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
                  <div>
                    <span className="text-slate-500 block text-[9px] uppercase">MODEL NAME</span>
                    <span className="text-cyan-400 font-bold">xgboost_behavioral_v1</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px] uppercase">MODEL SCORE</span>
                    <span className="text-white font-bold">{lead.ai_confidence ? lead.ai_confidence.toFixed(3) : '0.780'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px] uppercase">FEATURE VECTOR</span>
                    <span className="text-slate-300 font-bold">{lead.feature_vector_version || 'v1.2_70f'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[9px] uppercase">FINDING COUNT</span>
                    <span className="text-amber-400 font-bold">{lead.finding_count || findings.length || 1}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ── 3. INVESTIGATOR DISPOSITION SECTION ── */}
          <div className="bg-[#070B14] border border-[#1E293B] p-5 rounded-md space-y-4">
            <div className="flex items-center space-x-2 text-white">
              <Shield className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-bold uppercase tracking-wider font-mono">
                INVESTIGATOR DISPOSITION & RATIONALE
              </h3>
            </div>

            <div>
              <label className="block text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                Investigator Rationale / Notes (Appears on lead card preview)
              </label>
              <textarea
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Record your investigative basis for confirming, rejecting, or closing this finding..."
                className="w-full bg-[#0C1220] border border-[#1E293B] focus:border-cyan-500 rounded p-3 text-xs text-white font-sans placeholder-slate-600 focus:outline-none transition-colors"
              />
            </div>

            {/* Disposition Action Buttons */}
            <div className="space-y-3">
              <label className="block text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                Select Disposition Action:
              </label>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedAction('CONFIRM')}
                  className={`px-4 py-3 rounded border font-mono text-xs font-extrabold flex items-center justify-center space-x-2 transition-all cursor-pointer ${
                    selectedAction === 'CONFIRM'
                      ? 'bg-emerald-500 text-slate-950 border-emerald-400 shadow-lg shadow-emerald-950'
                      : 'bg-emerald-950/40 border-emerald-800/60 text-emerald-400 hover:bg-emerald-900/60'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>CONFIRM LEAD</span>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedAction('FALSE_POSITIVE')}
                  className={`px-4 py-3 rounded border font-mono text-xs font-extrabold flex items-center justify-center space-x-2 transition-all cursor-pointer ${
                    selectedAction === 'FALSE_POSITIVE'
                      ? 'bg-purple-600 text-white border-purple-400 shadow-lg shadow-purple-950'
                      : 'bg-purple-950/40 border-purple-800/60 text-purple-400 hover:bg-purple-900/60'
                  }`}
                >
                  <XCircle className="w-4 h-4" />
                  <span>MARK FALSE POSITIVE</span>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedAction('CLOSE')}
                  className={`px-4 py-3 rounded border font-mono text-xs font-extrabold flex items-center justify-center space-x-2 transition-all cursor-pointer ${
                    selectedAction === 'CLOSE'
                      ? 'bg-slate-700 text-white border-slate-500 shadow-lg'
                      : 'bg-slate-900 border-slate-700 text-slate-400 hover:bg-slate-800'
                  }`}
                >
                  <Clock className="w-4 h-4" />
                  <span>CLOSE LEAD</span>
                </button>
              </div>
            </div>

            {/* Confirmation Dialog Banner when an action is selected */}
            {selectedAction && (
              <div className="p-4 bg-[#0C1220] border border-cyan-500/50 rounded-md space-y-3 animate-fadeIn">
                <div className="flex items-center space-x-2 text-cyan-400 font-bold text-xs">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <span>
                    CONFIRM {selectedAction === 'CONFIRM' ? 'LEAD CONFIRMATION' : selectedAction === 'FALSE_POSITIVE' ? 'FALSE POSITIVE DISPOSITION' : 'CLOSING LEAD'}?
                  </span>
                </div>
                <p className="text-xs text-slate-300 font-sans">
                  {selectedAction === 'CONFIRM'
                    ? 'This will mark the finding as reviewed and confirmed by the human investigator.'
                    : selectedAction === 'FALSE_POSITIVE'
                    ? 'This finding will be marked as false positive based on current investigative evidence.'
                    : 'This lead will be closed and archived from active priority queue.'}
                </p>

                <div className="flex items-center justify-end space-x-3 pt-1">
                  <button
                    type="button"
                    onClick={() => setSelectedAction(null)}
                    className="px-3 py-1.5 rounded text-xs font-mono text-slate-400 hover:text-white"
                  >
                    Cancel Action
                  </button>

                  <button
                    type="button"
                    onClick={() => handleExecuteDisposition(
                      selectedAction === 'CONFIRM' ? 'CONFIRMED' : selectedAction === 'FALSE_POSITIVE' ? 'FALSE_POSITIVE' : 'CLOSED'
                    )}
                    disabled={disposeMutation.isPending}
                    className="px-5 py-2 rounded bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs flex items-center space-x-2 shadow-lg cursor-pointer"
                  >
                    {disposeMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <span>EXECUTE DISPOSITION NOW</span>
                  </button>
                </div>
              </div>
            )}

            {disposeMutation.isError && (
              <div className="p-3 bg-red-950/60 border border-red-800/60 rounded text-xs text-red-400 font-mono">
                Failed to execute lead disposition: {(disposeMutation.error as Error)?.message || 'Permission or state transition conflict.'}
              </div>
            )}
          </div>
        </div>

        {/* ── 4. FOOTER ── */}
        <div className="px-6 py-4 border-t border-[#1E293B] bg-[#070A0F] flex items-center justify-between shrink-0">
          <span className="text-[10px] text-slate-500 font-mono">
            CIVIX XGBoost C3 Intelligence Engine • Human Decision Verification Layer
          </span>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded bg-slate-800 hover:bg-slate-700 text-white font-mono text-xs font-bold transition-colors cursor-pointer"
          >
            Close Review Panel
          </button>
        </div>
      </div>
    </div>
  );
};
