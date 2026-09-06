import React from 'react';
import { FileText, Download, AlertCircle, CheckCircle2, Shield } from 'lucide-react';
import type { GraphNode, GraphRelationship } from '../../types/api';

interface ReportsContextViewProps {
  caseId: string;
  caseData?: any;
  nodes?: GraphNode[];
  graphNodes?: GraphNode[];
  relationships?: GraphRelationship[];
  graphRelationships?: GraphRelationship[];
}

export const ReportsContextView: React.FC<ReportsContextViewProps> = ({
  caseId,
  caseData,
  nodes: nodesProp,
  graphNodes,
  relationships: relsProp,
  graphRelationships,
}) => {
  const nodes = nodesProp || graphNodes || [];
  const relationships = relsProp || graphRelationships || [];

  const handleExportGraphSummary = () => {
    const summary = {
      case_id: caseId,
      exported_at: new Date().toISOString(),
      nodes_count: nodes.length,
      relationships_count: relationships.length,
      entity_types_summary: nodes.reduce((acc: Record<string, number>, n) => {
        const label = n.labels[0] || 'Entity';
        acc[label] = (acc[label] || 0) + 1;
        return acc;
      }, {}),
      relationship_types_summary: relationships.reduce((acc: Record<string, number>, r) => {
        acc[r.type] = (acc[r.type] || 0) + 1;
        return acc;
      }, {}),
    };

    const blob = new Blob([JSON.stringify(summary, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CIVIX_Graph_Network_Summary_${caseId.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full w-full bg-[#0b0f19] overflow-y-auto p-6 text-slate-200 font-sans select-none antialiased space-y-6">
      {/* Header */}
      <div className="p-4 rounded bg-[#0d1322] border border-[#1e2d4a] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-cyan-950 border border-cyan-500/60 flex items-center justify-center text-cyan-400 font-bold shrink-0">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                INVESTIGATIVE REPORTS & EXPORTS
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 font-bold">
                NETWORK SUMMARY EXPORT READY
              </span>
            </div>
            <h1 className="text-base font-bold text-white leading-tight mt-0.5">
              Case Intelligence Reports & Graph Network Exports
            </h1>
          </div>
        </div>

        <button
          onClick={handleExportGraphSummary}
          className="flex items-center gap-2 px-3 py-1.5 bg-cyan-950 border border-cyan-500/60 hover:bg-cyan-900 text-cyan-300 text-xs font-bold font-mono rounded transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          <span>EXPORT GRAPH SUMMARY (JSON)</span>
        </button>
      </div>

      {/* Truthful Backend Notice */}
      <div className="p-4 rounded bg-[#0d1322] border border-[#1e2d4a] space-y-3">
        <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs font-bold">
          <Shield className="w-4 h-4 shrink-0" />
          <span>INVESTIGATIVE REPORT GENERATION CONTRACT</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed font-sans">
          Automated PDF court report generation module is currently reserved for Phase 6. You can export the current loaded graph network summary, entity roles, and relationship counts for official investigative documentation.
        </p>
      </div>

      {/* Loaded Graph Network Metrics Summary */}
      <div className="grid grid-cols-2 gap-4 text-xs font-mono">
        <div className="p-4 rounded bg-[#0d1322] border border-[#1e2d4a] space-y-2">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">LOADED GRAPH NODES</span>
          <span className="text-2xl font-bold text-cyan-400 block">{nodes.length}</span>
          <p className="text-[11px] text-slate-400">Total authorized entities loaded in workstation context.</p>
        </div>

        <div className="p-4 rounded bg-[#0d1322] border border-[#1e2d4a] space-y-2">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">LOADED RELATIONSHIP EDGES</span>
          <span className="text-2xl font-bold text-emerald-400 block">{relationships.length}</span>
          <p className="text-[11px] text-slate-400">Total authoritative relationships & investigator proposals.</p>
        </div>
      </div>
    </div>
  );
};
