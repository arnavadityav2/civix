import React, { useState } from 'react';
import { 
  X, 
  Send, 
  AlertCircle, 
  CheckCircle2, 
  FileText, 
  ArrowRight, 
  ShieldAlert,
  Search
} from 'lucide-react';
import type { GraphNode } from '../../types/api';
import { ALLOWED_INVESTIGATOR_PREDICATES, type AssertionProposalResponse } from '../../types/graph';
import { assertionsApi } from '../../api/assertions';

interface ProposalDrawerProps {
  isOpen: boolean;
  caseId: string;
  sourceNode: GraphNode | null;
  targetNode: GraphNode | null;
  allNodes: GraphNode[];
  onClose: () => void;
  onSelectSourceNode?: (node: GraphNode) => void;
  onSelectTargetNode?: (node: GraphNode) => void;
  onProposalSubmitted: (response: AssertionProposalResponse) => void;
}

function deriveDisplayName(node: GraphNode | null): string {
  if (!node) return 'None Selected';
  const p = node.properties || {};
  const raw = (
    p.display_name ||
    p.name ||
    p.legal_name ||
    p.msisdn ||
    p.registration_number ||
    p.title ||
    p.raw_identifier ||
    node.id
  );
  return String(raw).replace(/_[0-9a-f]{8}$/i, '');
}

export const ProposalDrawer: React.FC<ProposalDrawerProps> = ({
  isOpen,
  caseId,
  sourceNode,
  targetNode,
  allNodes,
  onClose,
  onSelectSourceNode,
  onSelectTargetNode,
  onProposalSubmitted,
}) => {
  const [selectedPredicate, setSelectedPredicate] = useState<string>('ASSOCIATED_WITH');
  const [justification, setJustification] = useState<string>('');
  const [predicateFilter, setPredicateFilter] = useState<string>('');
  
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successResponse, setSuccessResponse] = useState<AssertionProposalResponse | null>(null);

  if (!isOpen) return null;

  const sourceName = deriveDisplayName(sourceNode);
  const targetName = deriveDisplayName(targetNode);

  const filteredPredicates = ALLOWED_INVESTIGATOR_PREDICATES.filter((p) =>
    p.toLowerCase().includes(predicateFilter.toLowerCase())
  );

  const isFormValid =
    !!sourceNode &&
    !!targetNode &&
    sourceNode.id !== targetNode.id &&
    justification.trim().length >= 10 &&
    ALLOWED_INVESTIGATOR_PREDICATES.includes(selectedPredicate as any);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceNode || !targetNode) {
      setErrorMsg('Both Source and Target entities must be selected.');
      return;
    }
    if (sourceNode.id === targetNode.id) {
      setErrorMsg('Source and Target entity must be different.');
      return;
    }
    if (justification.trim().length < 10) {
      setErrorMsg('Investigator justification must be at least 10 characters.');
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg(null);

      const response = await assertionsApi.proposeAssertion(caseId, {
        subject_entity_id: sourceNode.id,
        predicate: selectedPredicate,
        object_entity_id: targetNode.id,
        investigator_justification: justification.trim(),
      });

      setSuccessResponse(response);
      onProposalSubmitted(response);
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Failed to submit proposal';
      setErrorMsg(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setSuccessResponse(null);
    setJustification('');
    setErrorMsg(null);
  };

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-[#0d1322] border-l border-[#1e2d4a] shadow-2xl z-50 flex flex-col text-slate-200 select-none antialiased">
      {/* Drawer Header */}
      <div className="p-3 border-b border-[#162035] bg-[#0b0f19] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <h2 className="text-xs font-bold font-mono text-white uppercase tracking-wider">
            CONNECT ENTITY — PROPOSE RELATIONSHIP
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-white rounded hover:bg-[#131b2e] transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Drawer Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-sans text-xs">
        {successResponse ? (
          <div className="space-y-4">
            <div className="p-3 rounded bg-amber-950/60 border border-amber-500/60 space-y-2">
              <div className="flex items-center gap-2 text-amber-400 font-bold font-mono text-xs">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>INVESTIGATOR PROPOSAL RECORDED</span>
              </div>
              <p className="text-[11px] text-amber-200 leading-relaxed">
                Proposal state: <strong className="font-mono text-amber-300">PROPOSED</strong> (Awaiting Supervisor Review).
              </p>
              <p className="text-[10px] text-slate-400 leading-normal">
                This relationship is stored in the PostgreSQL assertion ledger. It remains non-authoritative and will NOT be projected to Neo4j until approved by a supervisor.
              </p>
            </div>

            <div className="bg-[#131b2e]/80 border border-[#1e2d4a] rounded p-3 space-y-2 font-mono text-[11px]">
              <div className="flex items-center justify-between text-slate-400">
                <span>ASSERTION ID:</span>
                <span className="text-white truncate max-w-[180px]">{successResponse.assertion_id}</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>PREDICATE:</span>
                <span className="text-amber-400 font-bold">{successResponse.predicate}</span>
              </div>
              <div className="flex items-center justify-between text-slate-400">
                <span>EPISTEMIC STATE:</span>
                <span className="text-amber-400 font-bold">PROPOSED</span>
              </div>
            </div>

            <button
              onClick={handleReset}
              className="w-full py-2 bg-cyan-950/80 border border-cyan-500/60 hover:bg-cyan-900/80 text-cyan-300 text-xs font-semibold rounded font-mono transition-colors"
            >
              PROPOSE ANOTHER RELATIONSHIP
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Epistemic Safety Notice */}
            <div className="p-2.5 rounded bg-[#131b2e]/60 border border-cyan-800/40 text-[11px] text-slate-300 space-y-1">
              <p className="font-semibold text-cyan-400">Authoritative Governance Rule</p>
              <p className="text-[10px] text-slate-400 leading-tight">
                Investigator relationship proposals require supervisor approval before becoming authoritative graph facts.
              </p>
            </div>

            {/* Source & Target Entity Summary */}
            <div className="space-y-2">
              <label className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                SUBJECT & OBJECT ENTITIES
              </label>

              <div className="p-2.5 rounded bg-[#131b2e]/80 border border-[#1e2d4a] flex items-center justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <span className="text-[9px] font-mono text-cyan-400 uppercase block">SOURCE (SUBJECT)</span>
                  <span className="font-semibold text-white truncate block">{sourceName}</span>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-500 shrink-0" />
                <div className="min-w-0 flex-1 text-right">
                  <span className="text-[9px] font-mono text-cyan-400 uppercase block">TARGET (OBJECT)</span>
                  <span className="font-semibold text-white truncate block">{targetName}</span>
                </div>
              </div>
            </div>

            {/* Predicate Selector */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                <span>RELATIONSHIP PREDICATE</span>
                <span className="text-cyan-400 font-normal">INV-18 AUTHORITATIVE</span>
              </label>

              <div className="relative mb-1">
                <Search className="w-3 h-3 absolute left-2 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  value={predicateFilter}
                  onChange={(e) => setPredicateFilter(e.target.value)}
                  placeholder="Filter allowed predicates..."
                  className="w-full bg-[#131b2e] border border-[#1e2d4a] rounded pl-7 pr-2 py-1 text-[11px] text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 font-mono"
                />
              </div>

              <select
                value={selectedPredicate}
                onChange={(e) => setSelectedPredicate(e.target.value)}
                className="w-full bg-[#131b2e] border border-[#1e2d4a] rounded p-2 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500/60"
                size={5}
              >
                {filteredPredicates.map((p) => (
                  <option key={p} value={p} className="py-1 px-2 bg-[#0d1322] hover:bg-cyan-950">
                    {p.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </div>

            {/* Justification Input */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <label className="font-bold text-slate-400 uppercase tracking-wider">
                  INVESTIGATOR JUSTIFICATION
                </label>
                <span className={justification.trim().length >= 10 ? 'text-emerald-400' : 'text-amber-400'}>
                  {justification.trim().length} / MIN 10 CHARS
                </span>
              </div>
              <textarea
                value={justification}
                onChange={(e) => setJustification(e.target.value)}
                rows={4}
                placeholder="Mandatory investigator rationale explaining why this relationship is proposed based on evidence or field reports..."
                className="w-full bg-[#131b2e] border border-[#1e2d4a] rounded p-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 resize-none font-sans"
              />
            </div>

            {/* Error Message Alert */}
            {errorMsg && (
              <div className="p-2.5 rounded bg-rose-950/60 border border-rose-800/60 flex items-center gap-2 text-rose-300 text-xs">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!isFormValid || isSubmitting}
              className={`w-full flex items-center justify-center gap-2 py-2 rounded text-xs font-bold font-mono tracking-wider transition-colors ${
                isFormValid && !isSubmitting
                  ? 'bg-amber-950/90 border border-amber-500 text-amber-300 hover:bg-amber-900 cursor-pointer'
                  : 'bg-[#131b2e] border border-[#1e2d4a] text-slate-500 cursor-not-allowed'
              }`}
            >
              <Send className="w-3.5 h-3.5" />
              <span>{isSubmitting ? 'SUBMITTING PROPOSAL...' : 'SUBMIT RELATIONSHIP PROPOSAL'}</span>
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
