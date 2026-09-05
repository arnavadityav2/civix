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

// Dark institutional node colors — NO PURPLE
// Device was #7c3aed (purple) — now uses blue (technical/analytical context)
const NODE_COLORS: Record<string, { bg: string; border: string }> = {
  Person:           { bg: '#0d2a4a', border: '#2d7dd2' },  // Blue — investigative subject
  Organization:     { bg: '#1e1600', border: '#c8a84b' },  // Gold — entity/institution
  Vehicle:          { bg: '#2d0a0a', border: '#c0392b' },  // Red — high attention
  PhoneNumber:      { bg: '#001a0d', border: '#1e8449' },  // Green — verified contact
  Device:           { bg: '#0d2a4a', border: '#2d7dd2' },  // Blue — technical
  FinancialAccount: { bg: '#1e1600', border: '#c8a84b' },  // Gold — financial entity
  Location:         { bg: '#001a0d', border: '#1e8449' },  // Green — geographic
  Evidence:         { bg: '#2a163d', border: '#8b5cf6' },  // Purple — evidence
  Lead:             { bg: '#3d162a', border: '#ec4899' },  // Pink — lead
};
const FALLBACK_COLOR = { bg: '#141c2e', border: '#2a3d62' };

function getPrimaryLabel(labels: string[]): string {
  const priority = ['Person', 'Organization', 'Vehicle', 'PhoneNumber', 'Device', 'FinancialAccount', 'Location', 'Evidence', 'Lead', 'SourceIdentity', 'Assertion', 'Event', 'Case', 'FIR'];
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



function buildMiniGraph(nodes: GraphNode[], rels: GraphRelationship[]): cytoscape.ElementDefinition[] {
  const elements: cytoscape.ElementDefinition[] = [];
  const nodeIds = new Set(nodes.map((n) => n.id));

  for (const node of nodes) {
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

  for (const rel of rels) {
    if (!nodeIds.has(rel.start_node) || !nodeIds.has(rel.end_node)) continue;
    elements.push({
      data: {
        id: rel.id,
        source: rel.start_node,
        target: rel.end_node,
        label: (rel.properties?.role as string) || rel.type,
        edgeType: rel.type === 'CANDIDATE_FOR' ? 'candidate' : 'investigative',
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
            'border-width': 2,
            'label': 'data(label)',
            // Light label text — legible on dark node backgrounds
            'color': '#e8edf5',
            'font-size': '9px',
            'font-family': '"IBM Plex Mono", Consolas, monospace',
            'font-weight': '600',
            'text-wrap': 'ellipsis',
            'text-max-width': '80px',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'width': '30px',
            'height': '30px',
          } as any,
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            // Blue = normal analytical relationship
            'line-color': '#2d7dd2',
            'target-arrow-color': '#2d7dd2',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '7px',
            'font-family': '"IBM Plex Mono", Consolas, monospace',
            'font-weight': '600',
            'color': '#4a9ee8',
            // Dark background for edge labels — not white
            'text-background-color': '#0f1623',
            'text-background-opacity': 0.9,
            'text-background-padding': '2px',
            'text-rotation': 'autorotate',
            'text-max-width': '80px',
            'text-wrap': 'ellipsis',
          } as any,
        },
        {
          // Gold/dashed = candidate / ML-inferred relationship (not confirmed)
          selector: 'edge[edgeType = "candidate"]',
          style: {
            'line-color': '#c8a84b',
            'target-arrow-color': '#c8a84b',
            'line-style': 'dashed',
            'line-dash-pattern': [5, 3],
            'color': '#e8c860',
            'text-background-color': '#0f1623',
            'text-background-opacity': 0.9,
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
            className="p-1 text-civix-text-muted hover:text-civix-text-primary rounded hover:bg-civix-surface-3 transition-colors"
            title="Refresh graph"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          {selectedCaseId && (
            <button
              onClick={() => navigate(`/cases/${selectedCaseId}/graph`)}
              className="flex items-center space-x-1 text-xs font-semibold text-civix-blue-light hover:text-civix-text-primary transition-colors font-mono"
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
        <div className="py-12 text-center text-xs text-civix-text-muted font-mono">
          Select an active case to view the investigative entity network.
        </div>
      ) : isLoading ? (
        <div className="py-12 flex items-center justify-center text-civix-text-muted space-x-2 text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-civix-blue-light" />
          <span>Loading entity graph…</span>
        </div>
      ) : error || !graphData || graphData.nodes.length === 0 ? (
        <div className="py-12 text-center text-xs text-civix-text-muted font-mono space-y-2">
          <div>No investigative graph projected for this case.</div>
          <div className="text-[11px] text-civix-text-muted font-sans">
            Open the full graph workstation to diagnose or link entities.
          </div>
        </div>
      ) : domainNodeCount === 0 ? (
        <div className="py-12 text-center text-xs text-civix-text-muted font-mono space-y-2">
          <div>No domain entities returned at 2-hop depth.</div>
          <div className="text-[11px] text-civix-text-muted">All nodes are infrastructure (Case/Assertion/Event).</div>
        </div>
      ) : (
        <div className="relative flex flex-col">
          <div className="relative w-full h-[280px] bg-civix-bg border border-civix-border rounded-sm overflow-hidden">
            <div ref={containerRef} className="w-full h-full civix-graph-canvas" />
            {/* Entity / link counter — dark surface */}
            <div className="absolute bottom-2 right-2 bg-civix-surface-2/95 border border-civix-border px-2 py-1 rounded-sm text-[9px] font-mono text-civix-text-muted">
              {domainNodeCount} entities · {invEdgeCount} inv. links
            </div>
            {/* Graph type label — blue institutional badge */}
            <div className="absolute top-2 left-2 text-[9px] font-mono font-bold bg-civix-blue-subtle border border-civix-blue-muted text-civix-blue-light px-1.5 py-0.5 rounded-sm uppercase tracking-widest">
              INVESTIGATIVE
            </div>
          </div>
          <p className="text-[9px] font-mono text-civix-text-muted mt-1.5 text-center">
            Case membership (HAS_ROLE) suppressed · Assertion nodes collapsed to edge labels
          </p>
        </div>
      )}
    </Panel>
  );
};
