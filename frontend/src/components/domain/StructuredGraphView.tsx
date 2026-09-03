import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { graphApi } from '../../api/graph';
import { useCaseSelection } from '../../context/CaseSelectionContext';
import type { GraphNode, GraphRelationship } from '../../types/api';
import { User, Car, Building2, UserCheck, ArrowRight, ShieldCheck, Loader2 } from 'lucide-react';

export const StructuredGraphView: React.FC = () => {
  const { selectedCaseId } = useCaseSelection();

  const { data: graphData, isLoading, error } = useQuery({
    queryKey: ['caseGraphStructured', selectedCaseId],
    queryFn: () => (selectedCaseId ? graphApi.getCaseGraph(selectedCaseId) : Promise.resolve(null)),
    enabled: !!selectedCaseId,
  });

  const getIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'VEHICLE':
        return <Car className="w-4 h-4 text-red-600" />;
      case 'ORGANIZATION':
        return <Building2 className="w-4 h-4 text-amber-600" />;
      case 'PERSON':
        return <UserCheck className="w-4 h-4 text-blue-600" />;
      default:
        return <ShieldCheck className="w-4 h-4 text-slate-600" />;
    }
  };

  if (!selectedCaseId) {
    return (
      <div className="py-12 text-center text-xs text-slate-500 font-mono">
        Select an active case to view relationship intelligence.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="py-12 flex items-center justify-center text-slate-400 space-x-2 text-xs font-mono">
        <Loader2 className="w-4 h-4 animate-spin text-amber-600" />
        <span>Loading case relationship canvas...</span>
      </div>
    );
  }

  if (error || !graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="py-12 text-center text-xs text-slate-500 font-mono space-y-1.5">
        <div className="font-semibold text-slate-600">No graph relationships projected for this case yet.</div>
        <div className="text-[11px] text-slate-400 font-sans">
          Link entities to this case or execute C3 analysis to populate graph relationships.
        </div>
      </div>
    );
  }

  // Derive primary subject (first PERSON node or first node)
  const primarySubjectNode = graphData.nodes.find((n: GraphNode) => n.labels?.includes('PERSON')) || graphData.nodes[0];
  const primarySubjectName = primarySubjectNode
    ? (primarySubjectNode.properties?.display_name || primarySubjectNode.properties?.name || primarySubjectNode.id)
    : 'Subject Entity';

  // Map relationships
  const relationships = (graphData.relationships || []).map((rel: GraphRelationship) => {
    const targetNode = graphData.nodes.find((n: GraphNode) => n.id === rel.end_node);
    const targetName = targetNode
      ? (targetNode.properties?.display_name || targetNode.properties?.name || targetNode.id)
      : rel.end_node;
    const targetType = targetNode && targetNode.labels ? targetNode.labels[0] : 'UNKNOWN';

    return {
      relationType: rel.type,
      targetName: targetName,
      targetType: targetType,
      provenance: rel.properties?.provenance || rel.properties?.source || 'Graph Relationship',
    };
  });

  return (
    <div className="bg-slate-50 border border-slate-200 rounded p-4">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Left: Primary Subject Node */}
        <div className="bg-white border-2 border-slate-900 rounded p-4 shadow-sm flex flex-col items-center justify-center min-w-[140px] text-center">
          <div className="w-10 h-10 rounded-full bg-slate-900 text-white flex items-center justify-center mb-2 shadow-2xs">
            <User className="w-5 h-5" />
          </div>
          <span className="text-xs font-bold text-slate-900 font-sans">{primarySubjectName}</span>
          <span className="text-[10px] font-mono font-semibold text-slate-500 uppercase tracking-wider mt-0.5">
            Target Subject
          </span>
        </div>

        {/* Center: Relationship Edges & Target Cards */}
        <div className="flex-1 space-y-2.5 w-full">
          {relationships.length === 0 ? (
            <div className="text-center py-6 text-xs text-slate-500 font-mono">
              Subject identified with 0 connected edges.
            </div>
          ) : (
            relationships.map((rel, index: number) => (
              <div
                key={index}
                className="flex items-center justify-between bg-white border border-slate-200 rounded px-3 py-2 text-xs shadow-2xs hover:border-slate-300 transition-colors"
              >
                {/* Relation Type Badge */}
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-300">
                    {rel.relationType}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                </div>

                {/* Target Entity Card */}
                <div className="flex items-center space-x-2.5 text-right">
                  <div className="p-1.5 bg-slate-100 rounded border border-slate-200">
                    {getIcon(rel.targetType)}
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 leading-tight">{rel.targetName}</div>
                    <div className="text-[10px] font-mono text-slate-500">{rel.provenance}</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
