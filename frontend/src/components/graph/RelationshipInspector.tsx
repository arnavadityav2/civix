import React from 'react';
import { X, GitFork, ShieldCheck, ShieldAlert, FileText, ArrowRight, UserCheck, Scale } from 'lucide-react';
import type { GraphNode, GraphRelationship } from '../../types/api';

interface RelationshipInspectorProps {
  relationship: GraphRelationship | null;
  allNodes: GraphNode[];
  onClose: () => void;
  onSelectNode: (node: GraphNode) => void;
}

function deriveDisplayName(node: GraphNode | null): string {
  if (!node) return 'Unknown Entity';
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

export const RelationshipInspector: React.FC<RelationshipInspectorProps> = ({
  relationship,
  allNodes,
  onClose,
  onSelectNode,
}) => {
  if (!relationship) return null;

  const nodeMap = new Map(allNodes.map((n) => [n.id, n]));
  const sourceNode = nodeMap.get(relationship.start_node) || null;
  const targetNode = nodeMap.get(relationship.end_node) || null;

  const sourceName = deriveDisplayName(sourceNode);
  const targetName = deriveDisplayName(targetNode);
  const predicateName = relationship.type.replace(/_/g, ' ');

  const proposalStatus = relationship.properties?.proposal_status || 'CONFIRMED';
  const epistemicStatus = relationship.properties?.epistemic_status || 'SYSTEM_DERIVED';
  const justification = relationship.properties?.investigator_justification || relationship.properties?.role_basis || null;
  const confidence = relationship.properties?.confidence ?? null;

  return (
    <div className="flex flex-col h-full bg-[#0d1322] border-l border-[#1e2d4a] text-slate-200 select-none antialiased">
      {/* Inspector Header */}
      <div className="p-3 border-b border-[#162035] bg-[#0b0f19] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitFork className="w-4 h-4 text-cyan-400" />
          <h2 className="text-xs font-bold font-mono text-white uppercase tracking-wider">
            RELATIONSHIP INSPECTOR
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-white rounded hover:bg-[#131b2e] transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Primary Status Banner */}
      <div className="p-3 border-b border-[#162035] bg-[#090d16]">
        {proposalStatus === 'PROPOSED' ? (
          <div className="p-2.5 rounded bg-amber-950/80 border border-amber-500/60 flex items-center gap-2 text-amber-300">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <div className="text-xs">
              <p className="font-bold leading-tight font-mono uppercase">INVESTIGATOR PROPOSED</p>
              <p className="text-[10px] text-amber-400/90 leading-tight">PROPOSED — AWAITING SUPERVISOR REVIEW</p>
            </div>
          </div>
        ) : proposalStatus === 'ACCEPTED_BY_SUPERVISOR' ? (
          <div className="p-2.5 rounded bg-emerald-950/80 border border-emerald-500/60 flex items-center gap-2 text-emerald-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="text-xs">
              <p className="font-bold leading-tight font-mono uppercase">SUPERVISOR ACCEPTED</p>
              <p className="text-[10px] text-emerald-400/90 leading-tight">Projected relationship via outbox/CDC pipeline</p>
            </div>
          </div>
        ) : (
          <div className="p-2.5 rounded bg-cyan-950/80 border border-cyan-800/60 flex items-center gap-2 text-cyan-300">
            <Scale className="w-4 h-4 text-cyan-400 shrink-0" />
            <div className="text-xs">
              <p className="font-bold leading-tight font-mono uppercase">AUTHORITATIVE GRAPH RECORD</p>
              <p className="text-[10px] text-cyan-400/90 leading-tight">PostgreSQL / Neo4j network relationship</p>
            </div>
          </div>
        )}
      </div>

      {/* Inspector Body Details */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs font-sans">
        {/* Connected Endpoints */}
        <div className="space-y-2">
          <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
            CONNECTED ENDPOINTS
          </h3>
          <div className="p-3 rounded bg-[#131b2e]/80 border border-[#1e2d4a] space-y-3">
            <button
              onClick={() => sourceNode && onSelectNode(sourceNode)}
              className="w-full text-left group hover:text-cyan-300 transition-colors"
            >
              <span className="text-[9px] font-mono text-slate-400 uppercase block">SUBJECT (SOURCE)</span>
              <span className="font-bold text-white text-xs truncate block group-hover:text-cyan-400">
                {sourceName}
              </span>
            </button>

            <div className="flex items-center justify-center gap-2 text-cyan-400 font-mono text-xs border-y border-[#162035] py-1.5">
              <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
              <span className="font-bold uppercase tracking-wider">{predicateName}</span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
            </div>

            <button
              onClick={() => targetNode && onSelectNode(targetNode)}
              className="w-full text-left group hover:text-cyan-300 transition-colors"
            >
              <span className="text-[9px] font-mono text-slate-400 uppercase block">OBJECT (TARGET)</span>
              <span className="font-bold text-white text-xs truncate block group-hover:text-cyan-400">
                {targetName}
              </span>
            </button>
          </div>
        </div>

        {/* Relationship Attributes */}
        <div className="space-y-2">
          <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
            EPISTEMIC & METADATA ATTRIBUTES
          </h3>
          <div className="bg-[#131b2e]/60 border border-[#1e2d4a] rounded divide-y divide-[#1e2d4a]">
            <div className="p-2 flex items-center justify-between">
              <span className="text-slate-400">Relationship ID</span>
              <span className="font-mono text-slate-300 text-[10px]">{relationship.id}</span>
            </div>
            <div className="p-2 flex items-center justify-between">
              <span className="text-slate-400">Epistemic Status</span>
              <span className="font-mono font-bold text-cyan-400">{String(epistemicStatus)}</span>
            </div>
            {confidence !== null && (
              <div className="p-2 flex items-center justify-between">
                <span className="text-slate-400">System Confidence</span>
                <span className="font-mono font-bold text-emerald-400">{(confidence * 100).toFixed(0)}%</span>
              </div>
            )}
          </div>
        </div>

        {/* Investigator Rationale / Basis */}
        {justification && (
          <div className="space-y-1.5">
            <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              JUSTIFICATION / ROLE BASIS
            </h3>
            <div className="p-3 rounded bg-[#131b2e]/80 border border-[#1e2d4a] text-slate-300 text-xs leading-relaxed font-mono">
              {String(justification)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
