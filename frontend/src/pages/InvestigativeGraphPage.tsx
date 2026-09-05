import React, {
  useEffect,
  useRef,
  useCallback,
  useState,
  useMemo,
} from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape';
import { graphApi } from '../api/graph';
import { casesApi } from '../api/cases';
import type { GraphNode, GraphRelationship } from '../types/api';
import {
  ArrowLeft,
  Loader2,
  AlertTriangle,
  RefreshCw,
  Maximize2,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  GitFork,
  User,
  Building2,
  Smartphone,
  Phone,
  Car,
  CreditCard,
  Fingerprint,
  Briefcase,
  Info,
  X,
  ChevronRight,
  Search,
  Eye,
  Layers,
  Shield,
  FileText,
  Clock,
  MapPin,
} from 'lucide-react';

// ── View Modes ────────────────────────────────────────────────────────────────
type ViewMode = 'investigative' | 'case_context' | 'provenance';

// ── Node type config ──────────────────────────────────────────────────────────
interface NodeTypeConfig {
  color: string;
  borderColor: string;
  textColor: string;
  icon: React.ElementType;
  iconClass: string;
  badgeClass: string;
  displayLabel: string;
}

const NODE_TYPE_CONFIG: Record<string, NodeTypeConfig> = {
  Person: {
    color: '#111318',
    borderColor: '#3b82f6',
    textColor: '#93c5fd',
    icon: User,
    iconClass: 'text-civix-blue-400',
    badgeClass: 'bg-civix-blue-950 border-civix-blue-600/50 text-civix-blue-400',
    displayLabel: 'PERSON',
  },
  Organization: {
    color: '#111318',
    borderColor: '#d97706',
    textColor: '#fcd34d',
    icon: Building2,
    iconClass: 'text-civix-gold-400',
    badgeClass: 'bg-civix-gold-950 border-civix-gold-600/50 text-civix-gold-400',
    displayLabel: 'ORGANIZATION',
  },
  Device: {
    color: '#111318',
    borderColor: '#2563eb',
    textColor: '#93c5fd',
    icon: Smartphone,
    iconClass: 'text-civix-blue-300',
    badgeClass: 'bg-civix-blue-950 border-civix-blue-500/40 text-civix-blue-300',
    displayLabel: 'DEVICE',
  },
  PhoneNumber: {
    color: '#111318',
    borderColor: '#059669',
    textColor: '#6ee7b7',
    icon: Phone,
    iconClass: 'text-civix-green-400',
    badgeClass: 'bg-civix-green-950 border-civix-green-600/50 text-civix-green-400',
    displayLabel: 'PHONE NUMBER',
  },
  Vehicle: {
    color: '#111318',
    borderColor: '#dc2626',
    textColor: '#fca5a5',
    icon: Car,
    iconClass: 'text-civix-red-400',
    badgeClass: 'bg-civix-red-950 border-civix-red-600/50 text-civix-red-400',
    displayLabel: 'VEHICLE',
  },
  FinancialAccount: {
    color: '#111318',
    borderColor: '#ca8a04',
    textColor: '#fde047',
    icon: CreditCard,
    iconClass: 'text-civix-gold-400',
    badgeClass: 'bg-civix-gold-950 border-civix-gold-600/50 text-civix-gold-400',
    displayLabel: 'FINANCIAL ACCOUNT',
  },
  SourceIdentity: {
    color: '#111318',
    borderColor: '#475569',
    textColor: '#cbd5e1',
    icon: Fingerprint,
    iconClass: 'text-civix-text-secondary',
    badgeClass: 'bg-civix-surface-2 border-civix-border text-civix-text-secondary',
    displayLabel: 'SOURCE IDENTITY',
  },
  Case: {
    color: '#111318',
    borderColor: '#0284c7',
    textColor: '#7dd3fc',
    icon: Briefcase,
    iconClass: 'text-civix-blue-400',
    badgeClass: 'bg-civix-blue-950 border-civix-blue-600/50 text-civix-blue-400',
    displayLabel: 'CASE',
  },
  Event: {
    color: '#111318',
    borderColor: '#16a34a',
    textColor: '#86efac',
    icon: Clock,
    iconClass: 'text-civix-green-400',
    badgeClass: 'bg-civix-green-950 border-civix-green-600/50 text-civix-green-400',
    displayLabel: 'EVENT',
  },
  Assertion: {
    color: '#111318',
    borderColor: '#3b82f6',
    textColor: '#93c5fd',
    icon: Shield,
    iconClass: 'text-civix-blue-400',
    badgeClass: 'bg-civix-blue-950 border-civix-blue-600/50 text-civix-blue-400',
    displayLabel: 'ASSERTION',
  },
  Location: {
    color: '#111318',
    borderColor: '#059669',
    textColor: '#6ee7b7',
    icon: MapPin,
    iconClass: 'text-civix-green-400',
    badgeClass: 'bg-civix-green-950 border-civix-green-600/50 text-civix-green-400',
    displayLabel: 'LOCATION',
  },
  Evidence: {
    color: '#111318',
    borderColor: '#8b5cf6',
    textColor: '#c4b5fd',
    icon: FileText,
    iconClass: 'text-civix-purple-400',
    badgeClass: 'bg-civix-purple-950 border-civix-purple-600/50 text-civix-purple-400',
    displayLabel: 'EVIDENCE',
  },
  Lead: {
    color: '#111318',
    borderColor: '#ec4899',
    textColor: '#f9a8d4',
    icon: Shield,
    iconClass: 'text-civix-pink-400',
    badgeClass: 'bg-civix-pink-950 border-civix-pink-600/50 text-civix-pink-400',
    displayLabel: 'LEAD',
  },
};

const FALLBACK_NODE_CONFIG: NodeTypeConfig = {
  color: '#111318',
  borderColor: '#64748b',
  textColor: '#cbd5e1',
  icon: GitFork,
  iconClass: 'text-civix-text-muted',
  badgeClass: 'bg-civix-surface-2 border-civix-border text-civix-text-secondary',
  displayLabel: 'ENTITY',
};

// Internal / infrastructure labels — never shown as primary visual nodes in INVESTIGATIVE mode
const INFRASTRUCTURE_LABELS = new Set([
  'Assertion', 'Event', 'Case', 'FIR', 'SourceIdentity',
]);

// Internal properties — never shown in inspector panels
const HIDDEN_PROPS = new Set([
  '_lock', 'last_seq_no', 'authorized_case_ids',
  'subject_entity_id', 'object_entity_id',
  'subject_entity_type', 'object_entity_type',
]);

// ── Helpers ───────────────────────────────────────────────────────────────────

function getPrimaryLabel(labels: string[]): string {
  const priority = [
    'Person', 'Organization', 'Device', 'PhoneNumber',
    'Vehicle', 'FinancialAccount', 'Location',
    'Evidence', 'Lead',
    'SourceIdentity', 'Assertion', 'Event', 'Case', 'FIR',
  ];
  for (const p of priority) {
    if (labels.includes(p)) return p;
  }
  return labels[0] || 'Unknown';
}

function getNodeConfig(labels: string[]): NodeTypeConfig {
  const label = getPrimaryLabel(labels);
  return NODE_TYPE_CONFIG[label] ?? FALLBACK_NODE_CONFIG;
}

function isDomainEntity(node: GraphNode): boolean {
  const primary = getPrimaryLabel(node.labels);
  return !INFRASTRUCTURE_LABELS.has(primary);
}

/**
 * Strip synthetic data artifact suffix from values like `RJ14-CB-2847_b058a8f4`.
 */
function cleanSyntheticSuffix(value: string): string {
  return value.replace(/_[0-9a-f]{8}$/i, '');
}

/** Derive a human-readable display name from node properties — no invention. */
function deriveDisplayName(node: GraphNode): string {
  const p = node.properties;
  const raw = (
    p.display_name ||
    p.name ||
    p.legal_name ||
    p.primary_name ||
    p.msisdn ||
    p.imei ||
    p.mac_address ||
    p.registration_number ||
    p.raw_identifier ||
    p.case_number ||
    p.fir_number ||
    p.account_identifier ||
    p.description ||
    null
  );
  if (raw) return cleanSyntheticSuffix(String(raw));
  // Graceful fallback — shortened ID, never raw UUID blob
  const id = node.id || '';
  return id.length > 8 ? `…${id.slice(-8)}` : id;
}

/** Derive a short secondary subtitle for node (e.g. SUSPECT, vehicle type) */
function deriveNodeSubtitle(node: GraphNode): string | null {
  const p = node.properties;
  if (p.role) return String(p.role);
  if (p.vehicle_type) return String(p.vehicle_type);
  if (p.org_type) return String(p.org_type);
  if (p.event_type) return String(p.event_type);
  if (p.gender) return String(p.gender);
  return null;
}

/** Format predicate string for human display. REGISTERED_TO → Registered To */
function formatPredicate(predicate: string): string {
  return predicate
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

// ── Presentation Graph Builder ────────────────────────────────────────────────

interface PresentationEdge {
  id: string;
  source: string;
  target: string;
  predicate: string;       // human-readable
  rawPredicate: string;    // backend value (e.g. REGISTERED_TO)
  epistemicStatus?: string;
  assertionId?: string;
  assertionNode?: GraphNode;
  sourceEntityId?: string;
  objectEntityId?: string;
  edgeClass: 'investigative' | 'case_context' | 'candidate';
}

interface PresentationGraph {
  domainNodes: GraphNode[];
  caseNodes: GraphNode[];
  assertionNodes: GraphNode[];
  eventNodes: GraphNode[];
  investigativeEdges: PresentationEdge[];
  caseContextEdges: PresentationEdge[];
}

function buildPresentationGraph(
  nodes: GraphNode[],
  relationships: GraphRelationship[]
): PresentationGraph {
  const nodeMap = new Map<string, GraphNode>(nodes.map((n) => [n.id, n]));
  const domainNodes: GraphNode[] = [];
  const caseNodes: GraphNode[] = [];
  const assertionNodes: GraphNode[] = [];
  const eventNodes: GraphNode[] = [];

  for (const n of nodes) {
    const primary = getPrimaryLabel(n.labels);
    if (primary === 'Assertion') assertionNodes.push(n);
    else if (primary === 'Event') eventNodes.push(n);
    else if (primary === 'Case' || primary === 'FIR') caseNodes.push(n);
    else domainNodes.push(n);
  }

  const investigativeEdges: PresentationEdge[] = [];
  const caseContextEdges: PresentationEdge[] = [];

  // HAS_ROLE edges → Case Context layer only
  const hasRoleRels = relationships.filter((r) => r.type === 'HAS_ROLE');
  for (const r of hasRoleRels) {
    const src = nodeMap.get(r.start_node);
    const tgt = nodeMap.get(r.end_node);
    if (!src || !tgt) continue;
    caseContextEdges.push({
      id: r.id,
      source: r.start_node,
      target: r.end_node,
      predicate: 'Case Role',
      rawPredicate: 'HAS_ROLE',
      epistemicStatus: r.properties?.role || undefined,
      edgeClass: 'case_context',
    });
  }

  // ASSERTS edges: Entity→Assertion or Assertion→Entity
  const assertsRels = relationships.filter((r) => r.type === 'ASSERTS');
  const assertionId2AssertionNode = new Map<string, GraphNode>(
    assertionNodes.map((a) => [a.id, a])
  );
  const assertionConnections = new Map<string, { subjects: string[]; objects: string[] }>();
  for (const r of assertsRels) {
    const srcLabel = getPrimaryLabel(nodeMap.get(r.start_node)?.labels ?? []);
    const tgtLabel = getPrimaryLabel(nodeMap.get(r.end_node)?.labels ?? []);

    if (srcLabel !== 'Assertion' && tgtLabel === 'Assertion') {
      if (!assertionConnections.has(r.end_node)) {
        assertionConnections.set(r.end_node, { subjects: [], objects: [] });
      }
      assertionConnections.get(r.end_node)!.subjects.push(r.start_node);
    }
    if (srcLabel === 'Assertion' && tgtLabel !== 'Assertion') {
      if (!assertionConnections.has(r.start_node)) {
        assertionConnections.set(r.start_node, { subjects: [], objects: [] });
      }
      assertionConnections.get(r.start_node)!.objects.push(r.end_node);
    }
  }

  for (const assertionNode of assertionNodes) {
    const p = assertionNode.properties;
    const predicate = p.predicate as string | undefined;
    const subjectId = p.subject_entity_id as string | undefined;
    const objectId = p.object_entity_id as string | undefined;
    const epistemicStatus = p.epistemic_status as string | undefined;
    const assertionId = p.assertion_id as string | undefined;

    if (!predicate || !subjectId || !objectId) continue;

    const subjectNode = nodeMap.get(subjectId);
    const objectNode = nodeMap.get(objectId);
    if (!subjectNode || !objectNode) continue;
    if (!isDomainEntity(subjectNode) || !isDomainEntity(objectNode)) continue;

    const edgeId = `assertion_${assertionNode.id}`;
    investigativeEdges.push({
      id: edgeId,
      source: subjectId,
      target: objectId,
      predicate: formatPredicate(predicate),
      rawPredicate: predicate,
      epistemicStatus,
      assertionId,
      assertionNode,
      sourceEntityId: subjectId,
      objectEntityId: objectId,
      edgeClass: 'investigative',
    });
  }

  for (const [assertNodeId, { subjects, objects }] of assertionConnections) {
    const assertionNode = assertionId2AssertionNode.get(assertNodeId);
    const p = assertionNode?.properties ?? {};
    const predicate = p.predicate as string | undefined;
    const epistemicStatus = p.epistemic_status as string | undefined;
    const assertionId = p.assertion_id as string | undefined;

    for (const subjectId of subjects) {
      for (const objectId of objects) {
        if (subjectId === objectId) continue;
        const subjectNode = nodeMap.get(subjectId);
        const objectNode = nodeMap.get(objectId);
        if (!subjectNode || !objectNode) continue;
        if (!isDomainEntity(subjectNode) || !isDomainEntity(objectNode)) continue;

        const edgeId = `asserts_${assertNodeId}_${subjectId}_${objectId}`;
        const alreadyAdded = investigativeEdges.some(
          (e) => e.source === subjectId && e.target === objectId && e.assertionNode?.id === assertNodeId
        );
        if (alreadyAdded) continue;

        investigativeEdges.push({
          id: edgeId,
          source: subjectId,
          target: objectId,
          predicate: predicate ? formatPredicate(predicate) : 'Related To',
          rawPredicate: predicate ?? 'ASSERTS',
          epistemicStatus,
          assertionId,
          assertionNode,
          sourceEntityId: subjectId,
          objectEntityId: objectId,
          edgeClass: 'investigative',
        });
      }
    }
  }

  // PARTICIPATED_AS edges: derive co-participation investigative links
  const participatedRels = relationships.filter((r) => r.type === 'PARTICIPATED_AS');
  const eventParticipants = new Map<string, string[]>();
  const eventNodesById = new Map<string, GraphNode>(eventNodes.map((e) => [e.id, e]));
  const domainNodeIds = new Set<string>(domainNodes.map((n) => n.id));

  for (const r of participatedRels) {
    let eventId: string | null = null;
    let entityId: string | null = null;

    const srcLabel = getPrimaryLabel(nodeMap.get(r.start_node)?.labels ?? []);
    const tgtLabel = getPrimaryLabel(nodeMap.get(r.end_node)?.labels ?? []);

    if (srcLabel === 'Event' && domainNodeIds.has(r.end_node)) {
      eventId = r.start_node;
      entityId = r.end_node;
    } else if (tgtLabel === 'Event' && domainNodeIds.has(r.start_node)) {
      eventId = r.end_node;
      entityId = r.start_node;
    } else if (domainNodeIds.has(r.start_node) && domainNodeIds.has(r.end_node)) {
      investigativeEdges.push({
        id: r.id,
        source: r.start_node,
        target: r.end_node,
        predicate: 'Co-participants',
        rawPredicate: 'PARTICIPATED_AS',
        edgeClass: 'investigative',
      });
      continue;
    }

    if (!eventId || !entityId) continue;
    if (!eventParticipants.has(eventId)) eventParticipants.set(eventId, []);
    eventParticipants.get(eventId)!.push(entityId);
  }

  const addedCoPairs = new Set<string>();
  for (const [eventId, participants] of eventParticipants) {
    if (participants.length < 2) continue;
    const eventNode = eventNodesById.get(eventId);

    for (let i = 0; i < participants.length; i++) {
      for (let j = i + 1; j < participants.length; j++) {
        const a = participants[i];
        const b = participants[j];
        if (a === b) continue;
        const pairKey = [a, b].sort().join('|');
        if (addedCoPairs.has(pairKey)) continue;
        addedCoPairs.add(pairKey);

        investigativeEdges.push({
          id: `copart_${eventId}_${a}_${b}`,
          source: a,
          target: b,
          predicate: 'Co-participant',
          rawPredicate: 'PARTICIPATED_AS',
          assertionNode: eventNode,
          edgeClass: 'investigative',
        });
      }
    }
  }

  // CANDIDATE_FOR → investigative candidate edges
  const candidateRels = relationships.filter((r) => r.type === 'CANDIDATE_FOR');
  for (const r of candidateRels) {
    const src = nodeMap.get(r.start_node);
    const tgt = nodeMap.get(r.end_node);
    if (!src || !tgt) continue;
    if (!isDomainEntity(src) || !isDomainEntity(tgt)) continue;
    investigativeEdges.push({
      id: r.id,
      source: r.start_node,
      target: r.end_node,
      predicate: 'Identity Candidate',
      rawPredicate: 'CANDIDATE_FOR',
      edgeClass: 'candidate',
    });
  }

  return {
    domainNodes,
    caseNodes,
    assertionNodes,
    eventNodes,
    investigativeEdges,
    caseContextEdges,
  };
}

// ── Cytoscape element builder ─────────────────────────────────────────────────

function buildCytoscapeElements(
  pg: PresentationGraph,
  viewMode: ViewMode,
  allNodes: GraphNode[]
): ElementDefinition[] {
  const elements: ElementDefinition[] = [];

  if (viewMode === 'investigative') {
    const edgesToRender = pg.investigativeEdges.length > 0 ? pg.investigativeEdges : pg.caseContextEdges;

    if (pg.investigativeEdges.length === 0 && pg.caseNodes.length > 0) {
      for (const caseNode of pg.caseNodes) {
        const cfg = getNodeConfig(caseNode.labels);
        elements.push({
          group: 'nodes',
          data: {
            id: caseNode.id,
            label: caseNode.properties.case_number ?? 'Case',
            name: caseNode.properties.case_number ?? 'Case',
            nodeType: 'Case',
            labels: caseNode.labels,
            properties: caseNode.properties,
            bgColor: cfg.color,
            borderColor: cfg.borderColor,
            textColor: cfg.textColor,
            entityId: caseNode.id,
          },
        });
      }
    }

    for (const node of pg.domainNodes) {
      const cfg = getNodeConfig(node.labels);
      const name = deriveDisplayName(node);
      const subtitle = deriveNodeSubtitle(node);
      const label = subtitle ? `${name}\n${subtitle}` : name;
      elements.push({
        group: 'nodes',
        data: {
          id: node.id,
          label,
          name,
          subtitle: subtitle ?? '',
          nodeType: getPrimaryLabel(node.labels),
          labels: node.labels,
          properties: node.properties,
          bgColor: cfg.color,
          borderColor: cfg.borderColor,
          textColor: cfg.textColor,
          entityId: node.properties.entity_id ?? node.id,
        },
      });
    }

    for (const edge of edgesToRender) {
      elements.push({
        group: 'edges',
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: edge.predicate,
          rawPredicate: edge.rawPredicate,
          epistemicStatus: edge.epistemicStatus ?? '',
          assertionId: edge.assertionId ?? '',
          edgeClass: edge.edgeClass,
          assertionProps: edge.assertionNode?.properties ?? {},
          presentationEdge: edge,
        },
      });
    }
  } else if (viewMode === 'case_context') {
    const caseNodeId = pg.caseNodes[0]?.id;
    if (caseNodeId) {
      const caseNode = pg.caseNodes[0];
      const cfg = getNodeConfig(caseNode.labels);
      elements.push({
        group: 'nodes',
        data: {
          id: caseNode.id,
          label: caseNode.properties.case_number ?? 'Case',
          name: caseNode.properties.case_number ?? 'Case',
          nodeType: 'Case',
          labels: caseNode.labels,
          properties: caseNode.properties,
          bgColor: cfg.color,
          borderColor: cfg.borderColor,
          textColor: cfg.textColor,
          entityId: caseNode.id,
        },
      });
    }

    for (const node of pg.domainNodes) {
      const cfg = getNodeConfig(node.labels);
      const name = deriveDisplayName(node);
      elements.push({
        group: 'nodes',
        data: {
          id: node.id,
          label: name,
          name,
          nodeType: getPrimaryLabel(node.labels),
          labels: node.labels,
          properties: node.properties,
          bgColor: cfg.color,
          borderColor: cfg.borderColor,
          textColor: cfg.textColor,
          entityId: node.properties.entity_id ?? node.id,
        },
      });
    }

    for (const edge of pg.caseContextEdges) {
      elements.push({
        group: 'edges',
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: edge.epistemicStatus ?? 'ROLE',
          rawPredicate: 'HAS_ROLE',
          edgeClass: 'case_context',
          presentationEdge: edge,
        },
      });
    }
  } else {
    for (const node of allNodes) {
      const cfg = getNodeConfig(node.labels);
      const primary = getPrimaryLabel(node.labels);
      const name = deriveDisplayName(node);
      const label = primary === 'Assertion'
        ? (node.properties.predicate ? `${node.properties.predicate}` : name)
        : name;
      elements.push({
        group: 'nodes',
        data: {
          id: node.id,
          label,
          name,
          nodeType: primary,
          labels: node.labels,
          properties: node.properties,
          bgColor: cfg.color,
          borderColor: cfg.borderColor,
          textColor: cfg.textColor,
          entityId: node.properties.entity_id ?? node.id,
        },
      });
    }
  }

  return elements;
}

function buildProvenanceElements(
  nodes: GraphNode[],
  relationships: GraphRelationship[]
): ElementDefinition[] {
  const elements: ElementDefinition[] = [];
  const nodeIds = new Set(nodes.map((n) => n.id));

  for (const node of nodes) {
    const cfg = getNodeConfig(node.labels);
    const primary = getPrimaryLabel(node.labels);
    const name = deriveDisplayName(node);
    const label = primary === 'Assertion'
      ? (node.properties.predicate ? `[${node.properties.predicate}]` : name)
      : primary === 'Event'
        ? `EVENT\n${(node.properties.description as string ?? '').slice(0, 30)}…`
        : name;
    elements.push({
      group: 'nodes',
      data: {
        id: node.id,
        label,
        name,
        nodeType: primary,
        labels: node.labels,
        properties: node.properties,
        bgColor: cfg.color,
        borderColor: cfg.borderColor,
        textColor: cfg.textColor,
        entityId: node.properties.entity_id ?? node.id,
      },
    });
  }

  for (const rel of relationships) {
    if (!nodeIds.has(rel.start_node) || !nodeIds.has(rel.end_node)) continue;
    if (rel.start_node === rel.end_node) continue;
    elements.push({
      group: 'edges',
      data: {
        id: rel.id,
        source: rel.start_node,
        target: rel.end_node,
        label: rel.type,
        rawPredicate: rel.type,
        edgeClass: rel.type === 'HAS_ROLE' ? 'case_context' : rel.type === 'CANDIDATE_FOR' ? 'candidate' : 'investigative',
        properties: rel.properties,
      },
    });
  }
  return elements;
}

// ── Cytoscape stylesheet ──────────────────────────────────────────────────────

const CY_STYLE: cytoscape.StylesheetStyle[] = [
  {
    selector: 'node',
    style: {
      'background-color': 'data(bgColor)',
      'border-color': 'data(borderColor)',
      'border-width': 2,
      'label': 'data(label)',
      'font-family': 'IBM Plex Mono, monospace',
      'font-size': 10,
      'font-weight': '600',
      'color': '#f3f4f6',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': 5,
      'width': 40,
      'height': 40,
      'text-max-width': '100px',
      'text-wrap': 'wrap',
      'text-overflow-wrap': 'whitespace',
      'transition-property': 'background-color, border-width, border-color',
      'transition-duration': '120ms',
    } as any,
  },
  {
    selector: 'node[nodeType = "Case"]',
    style: {
      'shape': 'rectangle',
      'width': 56,
      'height': 40,
      'font-size': 9,
    } as any,
  },
  {
    selector: 'node[nodeType = "Assertion"]',
    style: {
      'shape': 'diamond',
      'width': 28,
      'height': 28,
      'border-width': 1,
      'border-style': 'dashed',
      'font-size': 8,
    } as any,
  },
  {
    selector: 'node[nodeType = "Event"]',
    style: {
      'shape': 'round-rectangle',
      'width': 44,
      'height': 28,
      'font-size': 8,
    } as any,
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 3,
      'border-color': '#ffb703',
      'background-color': '#1e293b',
    } as any,
  },
  {
    selector: 'node.highlighted',
    style: {
      'border-width': 3,
      'border-color': '#f59e0b',
      'background-color': '#1e293b',
    } as any,
  },
  {
    selector: 'edge',
    style: {
      'width': 1.5,
      'line-color': '#3b82f6',
      'target-arrow-color': '#3b82f6',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'label': 'data(label)',
      'font-family': 'IBM Plex Mono, monospace',
      'font-size': 9,
      'font-weight': '600',
      'color': '#94a3b8',
      'text-rotation': 'autorotate',
      'text-background-color': '#111318',
      'text-background-opacity': 0.9,
      'text-background-padding': '2px',
      'text-max-width': '120px',
      'text-wrap': 'ellipsis',
      'transition-property': 'line-color, width, target-arrow-color',
      'transition-duration': '120ms',
    } as any,
  },
  {
    selector: 'edge[edgeClass = "investigative"]',
    style: {
      'line-color': '#3b82f6',
      'target-arrow-color': '#3b82f6',
      'width': 2,
      'color': '#93c5fd',
    } as any,
  },
  {
    selector: 'edge[edgeClass = "case_context"]',
    style: {
      'line-color': '#64748b',
      'target-arrow-color': '#64748b',
      'width': 1,
      'color': '#94a3b8',
      'line-style': 'dashed',
      'line-dash-pattern': [4, 4],
    } as any,
  },
  {
    selector: 'edge[edgeClass = "candidate"]',
    style: {
      'line-style': 'dashed',
      'line-dash-pattern': [6, 3],
      'line-color': '#f59e0b',
      'target-arrow-color': '#f59e0b',
      'color': '#fcd34d',
    } as any,
  },
  {
    selector: 'edge:selected',
    style: {
      'width': 3,
      'line-color': '#ffb703',
      'target-arrow-color': '#ffb703',
    } as any,
  },
];

// ── Selected Item Types ───────────────────────────────────────────────────────
type SelectedItem =
  | { kind: 'node'; node: GraphNode; displayName: string; primaryLabel: string }
  | { kind: 'edge'; edge: PresentationEdge; sourceNode?: GraphNode; targetNode?: GraphNode }
  | { kind: 'raw_edge'; rel: GraphRelationship; sourceNode?: GraphNode; targetNode?: GraphNode };

// ── Epistemic badge ───────────────────────────────────────────────────────────
const EpistemicBadge: React.FC<{ status?: string }> = ({ status }) => {
  if (!status) return null;
  const cls = status === 'CONFIRMED'
    ? 'bg-civix-green-950 border-civix-green-600/50 text-civix-green-400'
    : status === 'POSSIBLE'
      ? 'bg-civix-gold-950 border-civix-gold-600/50 text-civix-gold-400'
      : status === 'SUSPECTED'
        ? 'bg-civix-red-950 border-civix-red-600/50 text-civix-red-400'
        : 'bg-civix-surface-2 border-civix-border text-civix-text-secondary';
  return (
    <span className={`inline-flex items-center text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm border ${cls}`}>
      {status}
    </span>
  );
};

// ── Node Inspector Panel ──────────────────────────────────────────────────────
interface NodeInspectorProps {
  node: GraphNode;
  displayName: string;
  primaryLabel: string;
  onClose: () => void;
  onOpenDossier: (entityId: string) => void;
}

const NodeInspector: React.FC<NodeInspectorProps> = ({
  node, displayName, primaryLabel, onClose, onOpenDossier,
}) => {
  const cfg = getNodeConfig(node.labels);
  const Icon = cfg.icon;
  const p = node.properties;
  const entityId = p.entity_id || null;

  // Only surface investigator-relevant properties
  const identifiers: { label: string; value: string }[] = [];
  if (p.display_name && primaryLabel === 'Person') identifiers.push({ label: 'Full Name', value: String(p.display_name) });
  if (p.legal_name) identifiers.push({ label: 'Registered Name', value: String(p.legal_name) });
  if (p.registration_number) identifiers.push({ label: 'Registration', value: cleanSyntheticSuffix(String(p.registration_number)) });
  if (p.msisdn) identifiers.push({ label: 'Phone Number', value: String(p.msisdn) });
  if (p.imei) identifiers.push({ label: 'IMEI', value: String(p.imei) });
  if (p.mac_address) identifiers.push({ label: 'MAC Address', value: String(p.mac_address) });
  if (p.account_identifier) identifiers.push({ label: 'Account', value: String(p.account_identifier) });
  if (p.date_of_birth) identifiers.push({ label: 'Date of Birth', value: String(p.date_of_birth) });
  if (p.nationality) identifiers.push({ label: 'Nationality', value: String(p.nationality) });
  if (p.gender) identifiers.push({ label: 'Gender', value: String(p.gender) });
  if (p.vehicle_type) identifiers.push({ label: 'Vehicle Type', value: String(p.vehicle_type) });
  if (p.org_type) identifiers.push({ label: 'Organisation Type', value: String(p.org_type) });

  return (
    <div className="flex flex-col h-full bg-civix-surface text-civix-text-main">
      {/* Header */}
      <div className="px-4 py-3 bg-civix-surface-2 border-b border-civix-border flex items-start justify-between flex-shrink-0">
        <div className="flex items-start space-x-2 min-w-0">
          <div className={`w-7 h-7 rounded-sm border flex items-center justify-center flex-shrink-0 mt-0.5 ${cfg.badgeClass}`}>
            <Icon className={`w-3.5 h-3.5 ${cfg.iconClass}`} />
          </div>
          <div className="min-w-0">
            <p className={`text-[10px] font-bold uppercase tracking-wider mb-0.5 ${cfg.iconClass}`}>
              {cfg.displayLabel}
            </p>
            <p className="text-sm font-bold text-civix-text-main leading-tight break-words">
              {displayName}
            </p>
          </div>
        </div>
        <button onClick={onClose} className="p-1 text-civix-text-muted hover:text-civix-text-main rounded-sm transition-colors flex-shrink-0">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-5">

        {/* Case Role — if available */}
        {p.role && (
          <div>
            <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-2">Case Role</p>
            <span className="inline-flex items-center text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-red-950 border-civix-red-600/50 text-civix-red-400">
              {String(p.role)}
            </span>
            {p.role_basis && (
              <p className="text-[10px] text-civix-text-muted mt-1">{String(p.role_basis)}</p>
            )}
          </div>
        )}

        {/* Identifiers */}
        {identifiers.length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-2">Identifiers</p>
            <div className="space-y-2">
              {identifiers.map(({ label, value }) => (
                <div key={label}>
                  <p className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider">{label}</p>
                  <p className="text-xs font-mono text-civix-text-main mt-0.5 break-all">{value}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Internal Reference */}
        {entityId && (
          <div>
            <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-1">Internal Reference</p>
            <p className="text-[9px] font-mono text-civix-text-muted break-all">{entityId}</p>
          </div>
        )}

        {/* C2 Identity Resolution note */}
        {node.labels.some(l => ['Person', 'Organization', 'SourceIdentity'].includes(l)) && (
          <div className="bg-civix-gold-950/40 border border-civix-gold-600/40 rounded-sm p-2.5 space-y-1">
            <div className="flex items-center space-x-1.5">
              <Info className="w-3 h-3 text-civix-gold-500 flex-shrink-0" />
              <p className="text-[9px] font-bold text-civix-gold-400 uppercase tracking-wider">C2 Identity Resolution</p>
            </div>
            <p className="text-[9px] text-civix-text-secondary leading-relaxed">
              Identity candidate relationships are shown as dashed amber edges. They are not confirmed resolutions.
            </p>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="px-4 py-3 border-t border-civix-border flex-shrink-0 space-y-2">
        {entityId && !['Case', 'FIR', 'Assertion', 'Event'].includes(primaryLabel) && (
          <button
            onClick={() => onOpenDossier(entityId)}
            className="w-full civix-btn-secondary justify-between text-xs py-2"
          >
            <div className="flex items-center space-x-2">
              <FileText className="w-3.5 h-3.5 text-civix-blue-400" />
              <span>Open Entity Dossier</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-civix-text-muted" />
          </button>
        )}
      </div>
    </div>
  );
};

// ── Edge Inspector Panel ──────────────────────────────────────────────────────
interface EdgeInspectorProps {
  edge: PresentationEdge;
  sourceNode?: GraphNode;
  targetNode?: GraphNode;
  onClose: () => void;
}

const EdgeInspector: React.FC<EdgeInspectorProps> = ({ edge, sourceNode, targetNode, onClose }) => {
  const ap = edge.assertionNode?.properties ?? {};
  const isCandidate = edge.edgeClass === 'candidate';
  const isCaseContext = edge.edgeClass === 'case_context';

  return (
    <div className="flex flex-col h-full bg-civix-surface text-civix-text-main">
      {/* Header */}
      <div className={`px-4 py-3 border-b border-civix-border flex items-start justify-between flex-shrink-0 ${
        isCandidate ? 'bg-civix-gold-950/60' : isCaseContext ? 'bg-civix-surface-2' : 'bg-civix-blue-950/60'
      }`}>
        <div>
          <p className={`text-[10px] font-bold uppercase tracking-wider mb-0.5 ${
            isCandidate ? 'text-civix-gold-400' : isCaseContext ? 'text-civix-text-secondary' : 'text-civix-blue-400'
          }`}>
            {isCandidate ? 'IDENTITY CANDIDATE' : isCaseContext ? 'CASE CONTEXT' : 'INVESTIGATIVE RELATIONSHIP'}
          </p>
          <p className="text-sm font-bold text-civix-text-main leading-tight">{edge.predicate}</p>
        </div>
        <button onClick={onClose} className="p-1 text-civix-text-muted hover:text-civix-text-main rounded-sm transition-colors">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">

        {/* Candidate Warning */}
        {isCandidate && (
          <div className="bg-civix-gold-950/40 border border-civix-gold-600/40 rounded-sm p-2.5">
            <div className="flex items-center space-x-1.5">
              <Info className="w-3 h-3 text-civix-gold-500 flex-shrink-0" />
              <p className="text-[9px] font-bold text-civix-gold-400 uppercase tracking-wider">C2 Identity Candidate — Not Confirmed</p>
            </div>
            <p className="text-[9px] text-civix-text-secondary mt-1 leading-relaxed">
              This is a deterministic identity candidate link. It has <strong>NOT</strong> been confirmed as a SAME_AS resolution. Do not treat it as a confirmed identity merge.
            </p>
          </div>
        )}

        {/* Case Context note */}
        {isCaseContext && (
          <div className="bg-civix-surface-2 border border-civix-border rounded-sm p-2.5">
            <div className="flex items-center space-x-1.5">
              <Info className="w-3 h-3 text-civix-blue-400 flex-shrink-0" />
              <p className="text-[9px] font-bold text-civix-text-secondary uppercase tracking-wider">Case Role — Not an Investigative Link</p>
            </div>
            <p className="text-[9px] text-civix-text-muted mt-1 leading-relaxed">
              This entity is assigned to this case with the role shown. Shared case membership does not imply a direct investigative association between entities.
            </p>
          </div>
        )}

        {/* Source → Target */}
        <div>
          <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-2">Relationship</p>
          <div className="space-y-1">
            <div className="bg-civix-surface-2 border border-civix-border rounded-sm p-2">
              <p className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider mb-0.5">Source</p>
              <p className="text-xs font-semibold text-civix-text-main">
                {sourceNode ? deriveDisplayName(sourceNode) : edge.source.slice(0, 12) + '…'}
              </p>
              {sourceNode && (
                <p className="text-[9px] text-civix-text-muted font-mono mt-0.5">
                  {getPrimaryLabel(sourceNode.labels)}
                </p>
              )}
            </div>
            <div className="flex justify-center">
              <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded-sm border ${
                isCandidate
                  ? 'bg-civix-gold-950 border-civix-gold-600/50 text-civix-gold-400'
                  : isCaseContext
                    ? 'bg-civix-surface-2 border-civix-border text-civix-text-secondary'
                    : 'bg-civix-blue-950 border-civix-blue-600/50 text-civix-blue-400'
              }`}>
                {edge.rawPredicate}
              </span>
            </div>
            <div className="bg-civix-surface-2 border border-civix-border rounded-sm p-2">
              <p className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider mb-0.5">Target</p>
              <p className="text-xs font-semibold text-civix-text-main">
                {targetNode ? deriveDisplayName(targetNode) : edge.target.slice(0, 12) + '…'}
              </p>
              {targetNode && (
                <p className="text-[9px] text-civix-text-muted font-mono mt-0.5">
                  {getPrimaryLabel(targetNode.labels)}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Epistemic Status */}
        {edge.epistemicStatus && (
          <div>
            <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-1">Epistemic Status</p>
            <EpistemicBadge status={edge.epistemicStatus} />
          </div>
        )}

        {/* Assertion Provenance */}
        {edge.assertionId && (
          <div>
            <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-2">Supporting Assertion</p>
            <div className="bg-civix-blue-950/40 border border-civix-blue-600/40 rounded-sm p-2 space-y-1">
              <p className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider">Assertion ID</p>
              <p className="text-[9px] font-mono text-civix-text-secondary break-all">{edge.assertionId}</p>
              {ap.predicate && (
                <>
                  <p className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider mt-1">Predicate</p>
                  <p className="text-[9px] font-mono text-civix-blue-400 font-bold">{ap.predicate}</p>
                </>
              )}
            </div>
          </div>
        )}

        {/* Event Provenance */}
        {edge.rawPredicate === 'PARTICIPATED_AS' && edge.assertionNode && (
          <div>
            <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-2">Shared Event</p>
            <div className="bg-civix-green-950/40 border border-civix-green-600/40 rounded-sm p-2 space-y-1">
              {edge.assertionNode.properties?.description && (
                <p className="text-[10px] text-civix-green-400 leading-relaxed">
                  {String(edge.assertionNode.properties.description)}
                </p>
              )}
              {edge.assertionNode.properties?.event_type && (
                <p className="text-[9px] font-mono font-bold text-civix-green-400 mt-1">
                  {String(edge.assertionNode.properties.event_type)}
                </p>
              )}
              {edge.assertionNode.properties?.occurred_at_lower && (
                <p className="text-[9px] text-civix-text-muted mt-0.5">
                  {new Date(String(edge.assertionNode.properties.occurred_at_lower)).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' })}
                </p>
              )}
            </div>
          </div>
        )}

        {/* No provenance note */}
        {!edge.assertionId && !isCaseContext && edge.rawPredicate !== 'PARTICIPATED_AS' && (
          <div className="flex items-start space-x-2 text-xs text-civix-text-muted">
            <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
            <span>No assertion provenance available for this relationship in the current graph depth.</span>
          </div>
        )}
      </div>
    </div>
  );
};

// ── Raw Edge Inspector (for Provenance mode) ──────────────────────────────────
const RawEdgeInspector: React.FC<{
  rel: GraphRelationship;
  sourceNode?: GraphNode;
  targetNode?: GraphNode;
  onClose: () => void;
}> = ({ rel, sourceNode, targetNode, onClose }) => {
  const propEntries = Object.entries(rel.properties ?? {})
    .filter(([k, v]) => !HIDDEN_PROPS.has(k) && v != null && v !== '');

  return (
    <div className="flex flex-col h-full bg-civix-surface text-civix-text-main">
      <div className="px-4 py-3 bg-civix-surface-2 border-b border-civix-border flex items-start justify-between flex-shrink-0">
        <div>
          <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-0.5">RELATIONSHIP (PROVENANCE)</p>
          <p className="text-sm font-bold font-mono text-civix-text-main">{rel.type}</p>
        </div>
        <button onClick={onClose} className="p-1 text-civix-text-muted hover:text-civix-text-main rounded-sm transition-colors">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        <div>
          <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-2">Connected Nodes</p>
          <div className="space-y-1">
            <div className="bg-civix-surface-2 border border-civix-border rounded-sm p-2">
              <p className="text-[9px] font-bold text-civix-text-muted uppercase">Source</p>
              <p className="text-xs font-semibold text-civix-text-main">{sourceNode ? deriveDisplayName(sourceNode) : rel.start_node.slice(0, 12) + '…'}</p>
            </div>
            <div className="flex justify-center">
              <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-surface border-civix-border text-civix-text-secondary">{rel.type}</span>
            </div>
            <div className="bg-civix-surface-2 border border-civix-border rounded-sm p-2">
              <p className="text-[9px] font-bold text-civix-text-muted uppercase">Target</p>
              <p className="text-xs font-semibold text-civix-text-main">{targetNode ? deriveDisplayName(targetNode) : rel.end_node.slice(0, 12) + '…'}</p>
            </div>
          </div>
        </div>
        {propEntries.length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider mb-2">Properties</p>
            <div className="space-y-1.5">
              {propEntries.map(([key, value]) => (
                <div key={key}>
                  <p className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider">{key}</p>
                  <p className="text-[10px] font-mono text-civix-text-secondary break-all mt-0.5">{String(value)}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ── Graph Stats Bar ───────────────────────────────────────────────────────────
const GraphStatsBar: React.FC<{
  pg: PresentationGraph;
  viewMode: ViewMode;
  rawNodes: number;
  rawRels: number;
  metadata?: any;
}> = ({ pg, viewMode, rawNodes, rawRels, metadata }) => {
  const visibleNodes = viewMode === 'investigative'
    ? pg.domainNodes.length
    : viewMode === 'case_context'
      ? pg.domainNodes.length + pg.caseNodes.length
      : rawNodes;
  const visibleEdges = viewMode === 'investigative'
    ? pg.investigativeEdges.length
    : viewMode === 'case_context'
      ? pg.caseContextEdges.length
      : rawRels;

  return (
    <div className="bg-civix-surface border border-t-0 border-civix-border rounded-b-sm px-4 py-1.5 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center space-x-4 text-[10px] font-mono text-civix-text-muted">
        <span><span className="font-bold text-civix-text-main">{visibleNodes}</span> entities</span>
        <span><span className="font-bold text-civix-text-main">{visibleEdges}</span> relationships</span>
        {viewMode !== 'provenance' && (
          <span>
            raw graph: <span className="font-bold text-civix-text-secondary">{rawNodes}n / {rawRels}r</span>
          </span>
        )}
      </div>
      <div className="flex items-center space-x-3 text-[9px] font-mono text-civix-text-muted">
        {metadata?.truncated && (
          <span className="flex items-center text-civix-gold-400 font-bold bg-civix-gold-900/30 px-1.5 py-0.5 rounded-xs border border-civix-gold-500/30">
            <AlertTriangle className="w-3 h-3 mr-1" />
            TRUNCATED (LIMIT REACHED)
          </span>
        )}
        <span>ACL-enforced · bounded traversal · Neo4j</span>
      </div>
    </div>
  );
};

// ── Graph Legend ──────────────────────────────────────────────────────────────
const GraphLegend: React.FC<{ viewMode: ViewMode }> = ({ viewMode }) => {
  const investigativeItems = [
    { label: 'Person', cfg: NODE_TYPE_CONFIG.Person },
    { label: 'Organization', cfg: NODE_TYPE_CONFIG.Organization },
    { label: 'Vehicle', cfg: NODE_TYPE_CONFIG.Vehicle },
    { label: 'Phone', cfg: NODE_TYPE_CONFIG.PhoneNumber },
    { label: 'Device', cfg: NODE_TYPE_CONFIG.Device },
    { label: 'Account', cfg: NODE_TYPE_CONFIG.FinancialAccount },
    { label: 'Evidence', cfg: NODE_TYPE_CONFIG.Evidence },
    { label: 'Lead', cfg: NODE_TYPE_CONFIG.Lead },
  ];

  return (
    <div className="absolute bottom-3 left-3 bg-civix-surface/95 border border-civix-border rounded-sm shadow-sm p-2 z-10 max-w-[200px]">
      <p className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider mb-1.5">Entity Types</p>
      <div className="grid grid-cols-2 gap-x-3 gap-y-1">
        {investigativeItems.map(({ label, cfg }) => (
          <div key={label} className="flex items-center space-x-1.5">
            <div className="w-3.5 h-3.5 rounded-xs border flex-shrink-0" style={{ backgroundColor: cfg.color, borderColor: cfg.borderColor }} />
            <span className="text-[9px] text-civix-text-secondary font-medium">{label}</span>
          </div>
        ))}
      </div>
      <div className="mt-2 pt-2 border-t border-civix-border/40 space-y-1">
        {viewMode === 'investigative' && (
          <div className="flex items-center space-x-1.5">
            <div className="w-8 h-0 border-t-2 border-civix-blue-500 flex-shrink-0" />
            <span className="text-[9px] text-civix-blue-400">Evidence-backed</span>
          </div>
        )}
        {viewMode === 'case_context' && (
          <div className="flex items-center space-x-1.5">
            <div className="w-8 h-0 border-t border-dashed border-civix-text-muted flex-shrink-0" />
            <span className="text-[9px] text-civix-text-secondary">Case role</span>
          </div>
        )}
        <div className="flex items-center space-x-1.5">
          <div className="w-8 h-0 border-t-2 border-dashed border-civix-gold-500 flex-shrink-0" />
          <span className="text-[9px] text-civix-gold-400">Candidate (C2)</span>
        </div>
      </div>
    </div>
  );
};

// ── Constants ─────────────────────────────────────────────────────────────────
const DEFAULT_DEPTH = 1;
const DEFAULT_NODE_LIMIT = 200;
const DEFAULT_REL_LIMIT = 500;

interface InvestigativeGraphPageProps {
  caseIdProp?: string;
  embedded?: boolean;
}

export const InvestigativeGraphPage: React.FC<InvestigativeGraphPageProps> = ({ caseIdProp, embedded = false }) => {
  const { caseId: paramCaseId } = useParams<{ caseId: string }>();
  const caseId = caseIdProp || paramCaseId;
  const navigate = useNavigate();

  const [depth, setDepth] = useState<number>(DEFAULT_DEPTH);
  const [viewMode, setViewMode] = useState<ViewMode>('investigative');
  const [selectedItem, setSelectedItem] = useState<SelectedItem | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const cyContainerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  // ── Case fetch ──────────────────────────────────────────────────────────
  const { data: caseData, isLoading: caseLoading, error: caseError } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => (caseId ? casesApi.getCase(caseId) : Promise.reject(new Error('No case ID'))),
    enabled: !!caseId,
    retry: 1,
    staleTime: 60_000,
  });

  // ── Graph fetch ─────────────────────────────────────────────────────────
  const {
    data: graphData,
    isLoading: graphLoading,
    error: graphError,
    refetch: refetchGraph,
    isFetching: graphFetching,
  } = useQuery({
    queryKey: ['graph', caseId, depth],
    queryFn: () =>
      caseId
        ? graphApi.getCaseGraph(caseId, depth, DEFAULT_NODE_LIMIT, DEFAULT_REL_LIMIT)
        : Promise.reject(new Error('No case ID')),
    enabled: !!caseId && !caseError,
    staleTime: 30_000,
  });

  // ── Build presentation graph ─────────────────────────────────────────────
  const presentationGraph = useMemo<PresentationGraph | null>(() => {
    if (!graphData) return null;
    return buildPresentationGraph(graphData.nodes, graphData.relationships);
  }, [graphData]);

  // ── Build Cytoscape elements ─────────────────────────────────────────────
  const cytoscapeElements = useMemo<ElementDefinition[]>(() => {
    if (!graphData || !presentationGraph) return [];
    if (viewMode === 'provenance') {
      return buildProvenanceElements(graphData.nodes, graphData.relationships);
    }
    return buildCytoscapeElements(presentationGraph, viewMode, graphData.nodes);
  }, [graphData, presentationGraph, viewMode]);

  // ── Initialize / update Cytoscape ───────────────────────────────────────
  useEffect(() => {
    if (!cyContainerRef.current) return;
    if (cytoscapeElements.length === 0) {
      if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null; }
      return;
    }
    if (cyRef.current) { cyRef.current.destroy(); cyRef.current = null; }

    // Layout configuration by view mode
    const layoutConfig: any = viewMode === 'investigative'
      ? {
          name: 'cose',
          animate: true,
          animationDuration: 600,
          randomize: false,
          nodeRepulsion: () => 12000,
          idealEdgeLength: () => 140,
          edgeElasticity: () => 0.6,
          nestingFactor: 1.5,
          gravity: 0.4,
          numIter: 1500,
          padding: 50,
          fit: true,
        }
      : viewMode === 'case_context'
        ? {
            name: 'breadthfirst',
            directed: true,
            animate: true,
            animationDuration: 400,
            padding: 40,
            spacingFactor: 1.4,
            fit: true,
          }
        : {
            name: 'cose',
            animate: false,
            randomize: false,
            nodeRepulsion: () => 5000,
            idealEdgeLength: () => 90,
            numIter: 800,
            padding: 30,
            fit: true,
          };

    const cy = cytoscape({
      container: cyContainerRef.current,
      elements: cytoscapeElements,
      style: CY_STYLE,
      layout: layoutConfig,
      wheelSensitivity: 0.3,
      minZoom: 0.15,
      maxZoom: 4,
      boxSelectionEnabled: false,
    });

    // Node click
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const graphNode = graphData?.nodes.find((n) => n.id === node.id());
      if (graphNode) {
        setSelectedItem({
          kind: 'node',
          node: graphNode,
          displayName: node.data('name') || node.data('label'),
          primaryLabel: node.data('nodeType'),
        });
      }
    });

    // Edge click
    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      const pe: PresentationEdge | undefined = edge.data('presentationEdge');

      if (viewMode === 'provenance') {
        const relId = edge.id();
        const rawRel = graphData?.relationships.find((r) => r.id === relId);
        if (rawRel) {
          const srcNode = graphData?.nodes.find((n) => n.id === rawRel.start_node);
          const tgtNode = graphData?.nodes.find((n) => n.id === rawRel.end_node);
          setSelectedItem({ kind: 'raw_edge', rel: rawRel, sourceNode: srcNode, targetNode: tgtNode });
        }
      } else if (pe) {
        const srcNode = graphData?.nodes.find((n) => n.id === pe.source);
        const tgtNode = graphData?.nodes.find((n) => n.id === pe.target);
        setSelectedItem({ kind: 'edge', edge: pe, sourceNode: srcNode, targetNode: tgtNode });
      }
    });

    // Background tap → deselect
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedItem(null);
        cy.elements().removeClass('highlighted');
      }
    });

    cyRef.current = cy;
    return () => { cy.destroy(); cyRef.current = null; };
  }, [cytoscapeElements, viewMode]);

  // ── Controls ─────────────────────────────────────────────────────────────
  const handleFit = useCallback(() => cyRef.current?.fit(undefined, 40), []);
  const handleZoomIn = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.zoom(cy.zoom() * 1.25);
    cy.center();
  }, []);
  const handleZoomOut = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.zoom(cy.zoom() / 1.25);
    cy.center();
  }, []);
  const handleReset = useCallback(() => cyRef.current?.reset(), []);

  // ── Search highlight ──────────────────────────────────────────────────────
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().removeClass('highlighted');
    if (!searchTerm.trim() || searchTerm.length < 2) return;
    const q = searchTerm.toLowerCase();
    cy.nodes().forEach((node) => {
      const label = (node.data('label') as string || '').toLowerCase();
      if (label.includes(q)) node.addClass('highlighted');
    });
  }, [searchTerm]);

  // ── Dossier navigation ────────────────────────────────────────────────────
  const handleOpenDossier = useCallback((entityId: string) => navigate(`/entities/${entityId}`), [navigate]);

  // ── Derived states ────────────────────────────────────────────────────────
  const isLoading = caseLoading || graphLoading;
  const hasError = caseError || graphError;
  const hasGraph = graphData && graphData.nodes.length > 0;
  const isEmptyGraph = graphData && graphData.nodes.length === 0;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col h-full min-h-0 space-y-4 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b border-civix-border gap-3 flex-shrink-0">
        <div>
          {!embedded && (
            <div className="flex items-center space-x-2 mb-1.5">
              <button
                onClick={() => navigate(caseId ? `/cases/${caseId}` : '/cases')}
                className="flex items-center space-x-1.5 text-xs font-semibold text-civix-text-muted hover:text-civix-text-main transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Case</span>
              </button>
              <span className="text-civix-border">/</span>
              <span className="text-xs text-civix-text-main font-bold">Investigative Graph</span>
            </div>
          )}
          <div className="flex items-center space-x-3">
            <GitFork className="w-5 h-5 text-civix-gold" />
            <h1 className="text-xl font-extrabold text-civix-text-main tracking-tight uppercase">
              Investigative Graph
            </h1>
            {caseData && (
              <span className="civix-id">
                {caseData.case_number}
              </span>
            )}
            {caseLoading && <Loader2 className="w-4 h-4 animate-spin text-civix-gold" />}
          </div>
          {caseData && (
            <p className="text-xs text-civix-text-muted mt-0.5 font-medium">{caseData.title}</p>
          )}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* View Mode */}
          <div className="flex items-center border border-civix-border rounded-sm overflow-hidden bg-civix-surface shadow-2xs">
            {([
              { mode: 'investigative' as ViewMode, label: 'INVESTIGATIVE', icon: Eye },
              { mode: 'case_context' as ViewMode, label: 'CASE CONTEXT', icon: Layers },
              { mode: 'provenance' as ViewMode, label: 'PROVENANCE', icon: Shield },
            ] as const).map(({ mode, label, icon: Icon }) => (
              <button
                key={mode}
                id={`view-${mode}`}
                onClick={() => { setViewMode(mode); setSelectedItem(null); }}
                className={`flex items-center space-x-1.5 px-3 py-1.5 text-[10px] font-bold transition-colors border-r border-civix-border last:border-r-0 ${
                  viewMode === mode
                    ? 'bg-civix-blue-600 text-white'
                    : 'text-civix-text-secondary hover:bg-civix-surface-2'
                }`}
              >
                <Icon className="w-3 h-3" />
                <span>{label}</span>
              </button>
            ))}
          </div>

          {/* Depth control */}
          <div className="flex items-center border border-civix-border rounded-sm overflow-hidden bg-civix-surface shadow-2xs">
            {[1, 2, 3, 4, 5].map((d) => (
              <button
                key={d}
                id={`depth-${d}-btn`}
                onClick={() => { setDepth(d); setSelectedItem(null); }}
                className={`px-3 py-1.5 text-xs font-bold transition-colors ${d > 1 ? 'border-l border-civix-border' : ''} ${depth === d ? 'bg-civix-blue-600 text-white' : 'text-civix-text-secondary hover:bg-civix-surface-2'}`}
              >
                {d} HOP{d > 1 ? 'S' : ''}
              </button>
            ))}
          </div>

          {/* Fit / Reset / Refresh / Zoom */}
          <button id="graph-fit-btn" onClick={handleFit} disabled={!hasGraph} className="civix-btn-secondary py-1 text-xs">
            <Maximize2 className="w-3.5 h-3.5" />
            <span>Fit</span>
          </button>
          <button id="graph-reset-btn" onClick={handleReset} disabled={!hasGraph} className="civix-btn-secondary py-1 text-xs">
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
          <button id="graph-refresh-btn" onClick={() => refetchGraph()} disabled={graphFetching} className="civix-btn-secondary py-1 text-xs">
            <RefreshCw className={`w-3.5 h-3.5 ${graphFetching ? 'animate-spin text-civix-gold' : ''}`} />
            <span>Refresh</span>
          </button>
          <div className="flex items-center border border-civix-border rounded-sm overflow-hidden bg-civix-surface shadow-2xs">
            <button id="graph-zoom-in" onClick={handleZoomIn} disabled={!hasGraph}
              className="px-2.5 py-1.5 text-civix-text-secondary hover:bg-civix-surface-2 transition-colors disabled:opacity-40">
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button id="graph-zoom-out" onClick={handleZoomOut} disabled={!hasGraph}
              className="px-2.5 py-1.5 text-civix-text-secondary hover:bg-civix-surface-2 border-l border-civix-border transition-colors disabled:opacity-40">
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* View Mode info banner */}
      {viewMode === 'investigative' && presentationGraph && depth === 1 && presentationGraph.investigativeEdges.length === 0 && presentationGraph.domainNodes.length > 0 && (
        <div className="flex items-start space-x-2 bg-civix-blue-950/60 border border-civix-blue-600/40 rounded-sm px-3 py-2 text-xs flex-shrink-0">
          <Info className="w-3.5 h-3.5 text-civix-blue-400 flex-shrink-0 mt-0.5" />
          <span className="text-civix-text-main">
            <strong>Investigative view at 1-hop:</strong> {presentationGraph.domainNodes.length} entities are assigned to this case. Switch to <strong>2 HOPS</strong> to load evidence-backed relationship edges (REGISTERED_TO, DRIVER_OF, OWNS, etc.), or switch to <strong>CASE CONTEXT</strong> to see case membership structure.
          </span>
        </div>
      )}

      {/* Main workspace */}
      <div className="flex gap-4 flex-1 min-h-0" style={{ height: 'calc(100vh - 300px)', minHeight: '480px' }}>
        {/* Graph Canvas */}
        <div className="flex flex-col flex-1 min-w-0 min-h-0">
          <div className="flex-1 relative bg-civix-bg border border-civix-border rounded-t-sm overflow-hidden min-h-0">

            {/* Loading overlay */}
            {isLoading && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-civix-bg/90 z-20 space-y-3">
                <Loader2 className="w-8 h-8 animate-spin text-civix-gold" />
                <div className="text-center">
                  <p className="text-sm font-bold text-civix-text-main uppercase tracking-wider">Loading Graph</p>
                  <p className="text-xs text-civix-text-muted font-mono mt-0.5">
                    Bounded traversal · depth {depth} · ACL enforced
                  </p>
                  {depth > 2 && (
                    <p className="text-[10px] text-civix-gold-400 mt-2 font-mono">
                      Deep traversals may take longer to compute.
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Error */}
            {!isLoading && hasError && (
              <div className="absolute inset-0 flex flex-col items-center justify-center z-20 space-y-4">
                <AlertTriangle className="w-10 h-10 text-civix-red" />
                <div className="text-center">
                  <p className="text-sm font-bold text-civix-text-main uppercase tracking-wider">Graph Unavailable</p>
                  <p className="text-xs text-civix-text-muted mt-1 max-w-sm">
                    {graphError instanceof Error ? graphError.message : 'Unable to retrieve the case graph.'}
                  </p>
                </div>
                <div className="flex items-center space-x-3">
                  <button onClick={() => refetchGraph()} className="civix-btn-primary">
                    <RefreshCw className="w-3.5 h-3.5" /><span>Retry</span>
                  </button>
                  <button onClick={() => navigate('/cases')} className="civix-btn-secondary">
                    <ArrowLeft className="w-3.5 h-3.5" /><span>Return to Cases</span>
                  </button>
                </div>
              </div>
            )}

            {/* Empty graph */}
            {!isLoading && !hasError && isEmptyGraph && (
              <div className="absolute inset-0 flex flex-col items-center justify-center z-20 space-y-4">
                <GitFork className="w-12 h-12 text-civix-text-muted opacity-50" />
                <div className="text-center">
                  <p className="text-sm font-bold text-civix-text-main uppercase tracking-wider">No Graph Data</p>
                  <p className="text-xs text-civix-text-muted mt-1 max-w-sm">
                    No relationships are projected for this case at depth {depth}.
                    Entities may not yet be linked to the case, or the Neo4j projection is pending.
                  </p>
                </div>
                <div className="flex items-center space-x-3">
                  {depth === 1 && (
                    <button onClick={() => setDepth(2)} className="civix-btn-secondary">
                      Try 2 HOPS
                    </button>
                  )}
                  <button onClick={() => navigate('/cases')} className="civix-btn-secondary">
                    <ArrowLeft className="w-3.5 h-3.5" /><span>Return to Cases</span>
                  </button>
                </div>
              </div>
            )}

            {/* Cytoscape canvas */}
            <div ref={cyContainerRef} className="w-full h-full civix-graph-canvas" style={{ visibility: hasGraph ? 'visible' : 'hidden' }} />

            {/* Graph Legend */}
            {hasGraph && <GraphLegend viewMode={viewMode} />}

            {/* In-graph search */}
            {hasGraph && (
              <div className="absolute top-3 right-3 z-10">
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-civix-text-muted" />
                  <input
                    id="graph-search-input"
                    type="text"
                    placeholder="Highlight entities..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="civix-input w-48 pl-7 pr-3 py-1.5 text-xs"
                  />
                  {searchTerm && (
                    <button onClick={() => setSearchTerm('')}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-civix-text-muted hover:text-civix-text-main">
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* View mode badge */}
            {hasGraph && (
              <div className="absolute top-3 left-3 z-10">
                <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded-sm border uppercase ${
                  viewMode === 'investigative' ? 'bg-civix-blue-950 border-civix-blue-600/50 text-civix-blue-400' :
                  viewMode === 'case_context' ? 'bg-civix-surface-2 border-civix-border text-civix-text-secondary' :
                  'bg-civix-gold-950 border-civix-gold-600/50 text-civix-gold-400'
                }`}>
                  {viewMode === 'investigative' ? 'INVESTIGATIVE VIEW' :
                   viewMode === 'case_context' ? 'CASE CONTEXT VIEW' : 'PROVENANCE VIEW'}
                </span>
              </div>
            )}
          </div>

          {/* Status Bar */}
          {!isLoading && !hasError && graphData && presentationGraph && (
            <GraphStatsBar
              pg={presentationGraph}
              viewMode={viewMode}
              rawNodes={graphData.nodes.length}
              rawRels={graphData.relationships.length}
              metadata={graphData.metadata}
            />
          )}
        </div>

        {/* Inspector Panel */}
        <div className="w-72 flex-shrink-0 civix-panel rounded-sm overflow-hidden flex flex-col">
          {selectedItem ? (
            selectedItem.kind === 'node' ? (
              <NodeInspector
                node={selectedItem.node}
                displayName={selectedItem.displayName}
                primaryLabel={selectedItem.primaryLabel}
                onClose={() => setSelectedItem(null)}
                onOpenDossier={handleOpenDossier}
              />
            ) : selectedItem.kind === 'edge' ? (
              <EdgeInspector
                edge={selectedItem.edge}
                sourceNode={selectedItem.sourceNode}
                targetNode={selectedItem.targetNode}
                onClose={() => setSelectedItem(null)}
              />
            ) : (
              <RawEdgeInspector
                rel={selectedItem.rel}
                sourceNode={selectedItem.sourceNode}
                targetNode={selectedItem.targetNode}
                onClose={() => setSelectedItem(null)}
              />
            )
          ) : (
            <div className="p-4 flex flex-col h-full">
              <div>
                <h3 className="civix-panel-title mb-1">Inspector</h3>
                <p className="text-[10px] text-civix-text-muted mb-4">Click a node or relationship to inspect it.</p>
              </div>

              {/* View mode help */}
              <div className="space-y-3">
                <div className="bg-civix-surface-2 rounded-sm p-2.5 border border-civix-border space-y-1">
                  <p className="text-[9px] font-bold uppercase tracking-wider text-civix-gold-400">
                    {viewMode === 'investigative' ? 'INVESTIGATIVE VIEW' : viewMode === 'case_context' ? 'CASE CONTEXT VIEW' : 'PROVENANCE VIEW'}
                  </p>
                  <p className="text-[9px] text-civix-text-secondary leading-relaxed font-sans">
                    {viewMode === 'investigative'
                      ? 'Shows only domain entities (Persons, Orgs, Vehicles, etc.) connected by evidence-backed predicates (REGISTERED_TO, DRIVER_OF, OWNS, etc.). Case infrastructure and internal nodes are hidden.'
                      : viewMode === 'case_context'
                        ? 'Shows entities assigned to this case and their case roles. Dashed lines indicate case membership — not investigative associations.'
                        : 'Shows the full raw Neo4j graph including Assertion and Event nodes. For forensic review and provenance inspection.'}
                  </p>
                </div>

                {presentationGraph && (
                  <div className="border border-civix-border rounded-sm p-2.5 space-y-2">
                    <p className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider">Graph Summary</p>
                    <div className="grid grid-cols-2 gap-1.5 text-[10px]">
                      <div className="bg-civix-surface-2 rounded-sm p-1.5 text-center border border-civix-border">
                        <p className="font-bold text-civix-text-main">{presentationGraph.domainNodes.length}</p>
                        <p className="text-civix-text-muted text-[8px]">Entities</p>
                      </div>
                      <div className="bg-civix-blue-950/60 rounded-sm p-1.5 text-center border border-civix-blue-600/40">
                        <p className="font-bold text-civix-blue-400">{presentationGraph.investigativeEdges.length}</p>
                        <p className="text-civix-blue-300 text-[8px]">Inv. Links</p>
                      </div>
                      <div className="bg-civix-gold-950/60 rounded-sm p-1.5 text-center border border-civix-gold-600/40">
                        <p className="font-bold text-civix-gold-400">{presentationGraph.assertionNodes.length}</p>
                        <p className="text-civix-gold-400 text-[8px]">Assertions</p>
                      </div>
                      <div className="bg-civix-green-950/60 rounded-sm p-1.5 text-center border border-civix-green-600/40">
                        <p className="font-bold text-civix-green-400">{presentationGraph.eventNodes.length}</p>
                        <p className="text-civix-green-400 text-[8px]">Events</p>
                      </div>
                    </div>
                    <p className="text-[9px] text-civix-text-muted leading-relaxed">
                      Switch to <strong>PROVENANCE</strong> view to inspect {presentationGraph.assertionNodes.length} raw assertion nodes and {presentationGraph.eventNodes.length} event nodes.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
