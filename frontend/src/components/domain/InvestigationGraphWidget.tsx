/**
 * InvestigationGraphWidget — Command Center mini graph preview.
 *
 * Uses the same semantic presentation layer as InvestigativeGraphPage:
 * - Only domain entities (Person, Org, Vehicle, etc.) are shown as nodes
 * - HAS_ROLE / Case nodes are suppressed
 * - Assertion nodes are collapsed into predicate-labelled edges where possible
 * - No UUIDs, internal IDs, or raw Neo4j labels in the primary visual
 */
import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import cytoscape, { type Core } from 'cytoscape';
import { graphApi } from '../../api/graph';
import { useCaseSelection } from '../../context/CaseSelectionContext';
import { Panel } from '../ui/Panel';
import { Loader2, RefreshCw, ExternalLink } from 'lucide-react';
import type { GraphNode, GraphRelationship } from '../../types/api';

// ── Types ─────────────────────────────────────────────────────────────────────
const INFRASTRUCTURE_LABELS = new Set(['Assertion', 'Event', 'Case', 'FIR', 'SourceIdentity']);

const NODE_COLORS: Record<string, { bg: string; border: string }> = {
  Person:           { bg: '#dbeafe', border: '#1d4ed8' },
  Organization:     { bg: '#fef3c7', border: '#d97706' },
  Vehicle:          { bg: '#fee2e2', border: '#dc2626' },
  PhoneNumber:      { bg: '#d1fae5', border: '#059669' },
  Device:           { bg: '#ede9fe', border: '#7c3aed' },
  FinancialAccount: { bg: '#fef9c3', border: '#ca8a04' },
  Location:         { bg: '#ecfdf5', border: '#059669' },
};
const FALLBACK_COLOR = { bg: '#f1f5f9', border: '#94a3b8' };

function getPrimaryLabel(labels: string[]): string {
  const priority = ['Person', 'Organization', 'Vehicle', 'PhoneNumber', 'Device', 'FinancialAccount', 'Location', 'SourceIdentity', 'Assertion', 'Event', 'Case', 'FIR'];
  for (const p of priority) {
    if (labels.includes(p)) return p;
  }
  return labels[0] ?? 'Unknown';
}

function isDomainEntity(labels: string[]): boolean {
  return !INFRASTRUCTURE_LABELS.has(getPrimaryLabel(labels));
}

function cleanSyntheticSuffix(value: string): string {
  return value.replace(/_[0-9a-f]{8}$/i, '');
}

function getDisplayName(node: GraphNode): string {
  const p = node.properties;
  const raw = p.display_name ?? p.legal_name ?? p.registration_number ?? p.msisdn ?? p.case_number ?? null;
  if (raw) return cleanSyntheticSuffix(String(raw));
  return `…${node.id.slice(-6)}`;
}

function formatPredicate(pred: string): string {
  return pred.split('_').map((w) => w.charAt(0) + w.slice(1).toLowerCase()).join(' ');
}

function buildMiniGraph(nodes: GraphNode[], rels: GraphRelationship[]): cytoscape.ElementDefinition[] {
  const elements: cytoscape.ElementDefinition[] = [];

  // Only domain nodes
  const domainNodes = nodes.filter((n) => isDomainEntity(n.labels));
  const domainIds = new Set(domainNodes.map((n) => n.id));
  const assertionNodes = nodes.filter((n) => getPrimaryLabel(n.labels) === 'Assertion');

  for (const node of domainNodes) {
    const primary = getPrimaryLabel(node.labels);
    const colors = NODE_COLORS[primary] ?? FALLBACK_COLOR;
    const name = getDisplayName(node);
    elements.push({
      data: {
        id: node.id,
        label: name,
        bgColor: colors.bg,
        borderColor: colors.border,
        nodeType: primary,
      },
    });
  }

  // Collapse Assertion nodes into predicate edges
  for (const assertion of assertionNodes) {
    const p = assertion.properties;
    const subjectId = p.subject_entity_id as string | undefined;
    const objectId = p.object_entity_id as string | undefined;
    const predicate = p.predicate as string | undefined;
    if (!subjectId || !objectId || !predicate) continue;
    if (!domainIds.has(subjectId) || !domainIds.has(objectId)) continue;
    if (subjectId === objectId) continue;
    elements.push({
      data: {
        id: `a_${assertion.id}`,
        source: subjectId,
        target: objectId,
        label: formatPredicate(predicate),
        edgeType: 'investigative',
      },
    });
  }

  // CANDIDATE_FOR edges
  for (const rel of rels) {
    if (rel.type !== 'CANDIDATE_FOR') continue;
    if (!domainIds.has(rel.start_node) || !domainIds.has(rel.end_node)) continue;
    if (rel.start_node === rel.end_node) continue;
    elements.push({
      data: {
        id: rel.id,
        source: rel.start_node,
        target: rel.end_node,
        label: 'Candidate',
        edgeType: 'candidate',
      },
    });
  }

  return elements;
}

// ── Component ─────────────────────────────────────────────────────────────────
export const InvestigationGraphWidget: React.FC = () => {
  const { selectedCaseId } = useCaseSelection();
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const navigate = useNavigate();

  const { data: graphData, isLoading, error, refetch } = useQuery({
    queryKey: ['caseGraph_mini', selectedCaseId],
    queryFn: () => (selectedCaseId ? graphApi.getCaseGraph(selectedCaseId, 2, 80, 150) : Promise.resolve(null)),
    enabled: !!selectedCaseId,
    staleTime: 60_000,
  });

  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    const elements = buildMiniGraph(graphData.nodes, graphData.relationships);

    if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null; }

    if (elements.filter((e) => e.data && !e.data.source).length === 0) return;

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(bgColor)',
            'border-color': 'data(borderColor)',
            'border-width': 1.5,
            'label': 'data(label)',
            'color': '#1e293b',
            'font-size': '9px',
            'font-family': 'Inter, sans-serif',
            'font-weight': '600',
            'text-wrap': 'ellipsis',
            'text-max-width': '80px',
            'text-valign': 'bottom',
            'text-margin-y': 3,
            'width': '28px',
            'height': '28px',
          } as any,
        },
        {
          selector: 'edge',
          style: {
            'width': 1.2,
            'line-color': '#1d4ed8',
            'target-arrow-color': '#1d4ed8',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '7px',
            'font-family': 'Inter, sans-serif',
            'font-weight': '600',
            'color': '#1e40af',
            'text-background-color': '#ffffff',
            'text-background-opacity': 0.85,
            'text-background-padding': '1px',
            'text-rotation': 'autorotate',
            'text-max-width': '80px',
            'text-wrap': 'ellipsis',
          } as any,
        },
        {
          selector: 'edge[edgeType = "candidate"]',
          style: {
            'line-color': '#f59e0b',
            'target-arrow-color': '#f59e0b',
            'line-style': 'dashed',
            'line-dash-pattern': [4, 3],
            'color': '#d97706',
          } as any,
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        randomize: false,
        nodeRepulsion: () => 6000,
        idealEdgeLength: () => 80,
        numIter: 800,
        padding: 20,
        fit: true,
      } as any,
      wheelSensitivity: 0.3,
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
      minZoom: 0.2,
      maxZoom: 3,
    });

    return () => {
      if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null; }
    };
  }, [graphData]);

  // Count visible entities
  const domainNodeCount = graphData
    ? graphData.nodes.filter((n) => isDomainEntity(n.labels)).length
    : 0;
  const invEdgeCount = graphData
    ? graphData.nodes.filter((n) => getPrimaryLabel(n.labels) === 'Assertion' &&
        n.properties.subject_entity_id && n.properties.object_entity_id && n.properties.predicate).length
    : 0;

  return (
    <Panel
      title="INVESTIGATIVE ENTITY NETWORK"
      subtitle="Evidence-backed relationships · domain entities only"
      headerAction={
        <div className="flex items-center space-x-2">
          <button
            onClick={() => refetch()}
            className="p-1 text-slate-500 hover:text-slate-900 rounded hover:bg-slate-200 transition-colors"
            title="Refresh graph"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          {selectedCaseId && (
            <button
              onClick={() => navigate(`/cases/${selectedCaseId}/graph`)}
              className="flex items-center space-x-1 text-xs font-semibold text-blue-700 hover:text-blue-900 transition-colors"
              title="Open full graph workstation"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Full Graph</span>
            </button>
          )}
        </div>
      }
      className="h-full flex flex-col"
    >
      {!selectedCaseId ? (
        <div className="py-12 text-center text-xs text-slate-500 font-mono">
          Select an active case to view the investigative entity network.
        </div>
      ) : isLoading ? (
        <div className="py-12 flex items-center justify-center text-slate-400 space-x-2 text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-amber-600" />
          <span>Loading entity graph…</span>
        </div>
      ) : error || !graphData || graphData.nodes.length === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500 font-mono space-y-2">
          <div>No investigative graph projected for this case.</div>
          <div className="text-[11px] text-slate-400 font-sans">
            Open the full graph workstation to diagnose or link entities.
          </div>
        </div>
      ) : domainNodeCount === 0 ? (
        <div className="py-12 text-center text-xs text-slate-500 font-mono space-y-2">
          <div>No domain entities returned at 2-hop depth.</div>
          <div className="text-[11px] text-slate-400">All nodes are infrastructure (Case/Assertion/Event).</div>
        </div>
      ) : (
        <div className="relative flex flex-col">
          <div className="relative w-full h-[280px] bg-slate-50 border border-slate-200 rounded overflow-hidden">
            <div ref={containerRef} className="w-full h-full" />
            <div className="absolute bottom-2 right-2 bg-white/90 border border-slate-200 px-2 py-1 rounded text-[9px] font-mono text-slate-600 shadow-2xs">
              {domainNodeCount} entities · {invEdgeCount} inv. links
            </div>
            <div className="absolute top-2 left-2 text-[9px] font-mono font-bold bg-blue-50 border border-blue-200 text-blue-700 px-1.5 py-0.5 rounded">
              INVESTIGATIVE
            </div>
          </div>
          <p className="text-[9px] font-mono text-slate-400 mt-1.5 text-center">
            Case membership (HAS_ROLE) suppressed · Assertion nodes collapsed to edge labels
          </p>
        </div>
      )}
    </Panel>
  );
};
