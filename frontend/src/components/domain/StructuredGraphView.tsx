import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { graphApi } from '../../api/graph';
import { useCaseSelection } from '../../context/CaseSelectionContext';
import type { GraphNode, GraphRelationship } from '../../types/api';
import { User, Car, Building2, UserCheck, ArrowRight, ShieldCheck, Loader2 } from 'lucide-react';
import { casesApi } from '../../api/cases';

export const StructuredGraphView: React.FC = () => {
  const { selectedCaseId } = useCaseSelection();

  const { data: cases = [] } = useQuery({
    queryKey: ['cases'],
    queryFn: casesApi.listCases,
  });

  const activeCaseId = selectedCaseId || (cases.length > 0 ? cases[0].case_id : null);

  const { data: graphData, isLoading, error } = useQuery({
    queryKey: ['caseGraphStructured', activeCaseId],
    queryFn: () => (activeCaseId ? graphApi.getCaseGraph(activeCaseId) : Promise.resolve(null)),
    enabled: !!activeCaseId,
  });

  // Entity icons — dark-appropriate colors
  const getIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'VEHICLE':
        return <Car className="w-4 h-4 text-civix-red-light" />;
      case 'ORGANIZATION':
        return <Building2 className="w-4 h-4 text-civix-gold" />;
      case 'PERSON':
        return <UserCheck className="w-4 h-4 text-civix-blue-light" />;
      default:
        return <ShieldCheck className="w-4 h-4 text-civix-text-secondary" />;
    }
  };

  if (!activeCaseId) {
    return (
      <div className="py-10 text-center text-xs text-civix-text-muted font-mono">
        Select an active case to view relationship intelligence.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="py-10 flex items-center justify-center text-civix-text-muted space-x-2 text-xs font-mono">
        <Loader2 className="w-4 h-4 animate-spin text-civix-blue-light" />
        <span>Loading case relationship canvas...</span>
      </div>
    );
  }

  if (error || !graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="py-10 text-center text-xs text-civix-text-muted font-mono space-y-1.5">
        <div className="font-semibold text-civix-text-secondary">No graph relationships projected for this case yet.</div>
        <div className="text-[11px] text-civix-text-muted font-sans">
          Link entities to this case or execute C3 analysis to populate graph relationships.
        </div>
      </div>
    );
  }

  // Derive primary subject
  const caseNode = graphData.nodes.find((n: GraphNode) => n.labels?.includes('Case'));
  const primarySubjectNode = caseNode || graphData.nodes.find((n: GraphNode) => n.labels?.includes('PERSON')) || graphData.nodes[0];
  const primarySubjectName = primarySubjectNode
    ? (primarySubjectNode.properties?.title || primarySubjectNode.properties?.display_name || primarySubjectNode.properties?.name || primarySubjectNode.id)
    : 'Selected Case';

  const relationships = (graphData.relationships || []).map((rel: GraphRelationship) => {
    const targetNode = graphData.nodes.find((n: GraphNode) => n.id === (rel.start_node === primarySubjectNode?.id ? rel.end_node : rel.start_node))
      || graphData.nodes.find((n: GraphNode) => n.id === rel.end_node);

    const targetName = targetNode
      ? (targetNode.properties?.display_name || targetNode.properties?.name || targetNode.properties?.legal_name || targetNode.properties?.registration_number || targetNode.id)
      : rel.end_node;
    const targetType = targetNode && targetNode.labels ? targetNode.labels[0] : 'UNKNOWN';
    const roleName = (rel.properties?.role || rel.type).replace(/_/g, ' ');

    return {
      relationType: roleName,
      targetName: targetName,
      targetType: targetType,
      provenance: rel.properties?.role_basis || rel.properties?.provenance || rel.properties?.source || 'Verified Case Entity',
    };
  });

  return (
    <div className="bg-civix-bg border border-civix-border rounded-sm p-3">
      <div className="flex flex-col gap-3">
        {/* Primary Subject Node */}
        <div className="flex items-center space-x-3 pb-3 border-b border-civix-border-subtle">
          <div className="w-8 h-8 rounded-sm bg-civix-blue text-white flex items-center justify-center flex-shrink-0">
            <User className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-civix-text-primary font-sans">{primarySubjectName}</div>
            <div className="text-[9px] font-mono text-civix-text-muted uppercase tracking-widest mt-0.5">
              Primary Subject
            </div>
          </div>
        </div>

        {/* Relationships */}
        <div className="space-y-1.5">
          {relationships.length === 0 ? (
            <div className="text-center py-4 text-xs text-civix-text-muted font-mono">
              Subject identified with 0 connected edges.
            </div>
          ) : (
            relationships.map((rel, index: number) => (
              <div
                key={index}
                className="flex items-center justify-between bg-civix-surface-2 border border-civix-border rounded-sm px-3 py-2 text-xs hover:border-civix-border-strong hover:bg-civix-surface-3 transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <span className="text-[9px] font-mono font-bold bg-civix-surface-3 text-civix-blue-light px-2 py-0.5 rounded-sm border border-civix-border-strong uppercase tracking-wider">
                    {rel.relationType}
                  </span>
                  <ArrowRight className="w-3 h-3 text-civix-text-muted" />
                </div>

                <div className="flex items-center space-x-2 text-right">
                  <div className="p-1 bg-civix-surface-3 rounded-sm border border-civix-border">
                    {getIcon(rel.targetType)}
                  </div>
                  <div>
                    <div className="font-bold text-civix-text-primary text-xs leading-tight">{rel.targetName}</div>
                    <div className="text-[9px] font-mono text-civix-text-muted">{rel.provenance}</div>
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
