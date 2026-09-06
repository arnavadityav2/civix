import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  GitFork, 
  RotateCcw, 
  Briefcase, 
  Network,
  Share2,
  Maximize2,
  RefreshCw,
  Info,
  Layers,
  FileText
} from 'lucide-react';
import { graphApi } from '../../api/graph';
import type { GraphNode, GraphRelationship } from '../../types/api';
import { GraphCanvas } from './GraphCanvas';
import { EpistemicLegend } from './EpistemicLegend';
import { EntityDossier } from './EntityDossier';
import { RelationshipInspector } from './RelationshipInspector';

interface ProvenanceUniverseViewProps {
  caseId: string;
  caseData?: any;
  onSelectNode: (node: GraphNode | null) => void;
  onSelectEdge: (edgeId: string | null) => void;
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  onReturnToGraph: () => void;
}

export const ProvenanceUniverseView: React.FC<ProvenanceUniverseViewProps> = ({
  caseId,
  caseData,
  onSelectNode,
  onSelectEdge,
  selectedNodeId,
  selectedEdgeId,
  onReturnToGraph,
}) => {
  const [universeDepth, setUniverseDepth] = useState<number>(3);
  const [reLayoutTrigger, setReLayoutTrigger] = useState<number>(0);
  const [hiddenTypes, setHiddenTypes] = useState<Set<string>>(new Set());

  // ── Fetch Case-Anchored Expansive Universe Network Data ──
  const { data: universeData, isLoading, error, refetch } = useQuery({
    queryKey: ['case-universe', caseId, universeDepth],
    queryFn: () => graphApi.getCaseUniverse(caseId, universeDepth),
    enabled: !!caseId,
    staleTime: 30_000,
  });

  const nodes = universeData?.nodes || [];
  const relationships = universeData?.relationships || [];

  // Currently selected node object
  const selectedNode = useMemo(() => {
    return nodes.find((n) => n.id === selectedNodeId) || null;
  }, [nodes, selectedNodeId]);

  // Currently selected relationship object
  const selectedRelationship = useMemo(() => {
    return relationships.find((r) => r.id === selectedEdgeId) || null;
  }, [relationships, selectedEdgeId]);

  // Calculate Data-Derived Topology Metrics
  const metrics = useMemo(() => {
    const caseClusters = nodes.filter((n) => n.labels.includes('Case') || n.properties?.node_class === 'CASE_CLUSTER').length;
    const bridgeHubs = nodes.filter((n) => n.labels.includes('BridgeEntityNode') || n.properties?.node_class === 'BRIDGE_HUB' || (n.properties?.authorized_case_ids && n.properties.authorized_case_ids.length > 1)).length;
    const entities = nodes.filter((n) => !n.labels.includes('Case') && !n.labels.includes('Event') && !n.labels.includes('Evidence')).length;
    const invLinks = relationships.filter((r) => r.type === 'SHARED_IN_CASE' || r.properties?.role || r.type === 'ASSOCIATED_WITH').length;
    const assertions = relationships.filter((r) => r.properties?.epistemic_status || r.type !== 'SHARED_IN_CASE').length;
    const events = nodes.filter((n) => n.labels.includes('Event') || n.properties?.entity_type === 'EVENT').length;

    return {
      caseClusters: caseClusters || 1,
      bridgeHubs,
      entities,
      invLinks,
      assertions,
      events,
      relationships: relationships.length,
      truncated: universeData?.metadata?.truncated || false,
    };
  }, [nodes, relationships, universeData]);

  const handleReLayout = useCallback(() => {
    setReLayoutTrigger((prev) => prev + 1);
  }, []);

  const toggleEntityType = (type: string) => {
    setHiddenTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  return (
    <div className="flex flex-col h-full w-full relative overflow-hidden bg-[#0b0f19] text-slate-200 font-sans select-none antialiased">
      {/* ── Top Navigation Header Banner ── */}
      <div className="px-4 py-2.5 bg-[#0d1322] border-b border-[#1e2d4a] flex items-center justify-between shadow-md shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-cyan-950/90 border border-cyan-500/60 flex items-center justify-center text-cyan-400 shrink-0">
            <GitFork className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                FULL INVESTIGATIVE UNIVERSE
              </span>
              <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/60 text-cyan-300 uppercase">
                SCOPE: ACTIVE CASE + AUTHORIZED CONNECTED NETWORK
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans mt-0.5">
              Case anchor: <span className="text-white font-mono font-bold">{caseData?.case_number || caseId}</span>
            </p>
          </div>
        </div>

        {/* Header Controls: 1 HOP to 5 HOPS Depth Selector */}
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-[#131b2e] p-1 rounded border border-[#1e2d4a] text-xs font-mono">
            <span className="text-[10px] text-slate-400 font-bold px-2 uppercase tracking-wider">HOPS:</span>
            {[1, 2, 3, 4, 5].map((h) => (
              <button
                key={h}
                onClick={() => setUniverseDepth(h)}
                className={`px-2.5 py-1 rounded transition-colors font-bold ${
                  universeDepth === h
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/60 shadow-xs'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                {h} {h === 1 ? 'HOP' : 'HOPS'}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1.5 border-l border-[#1e2d4a] pl-3">
            <button
              onClick={() => refetch()}
              className="px-2.5 py-1 bg-[#131b2e] border border-[#1e2d4a] hover:border-cyan-500/60 text-slate-300 hover:text-white text-xs font-mono font-bold rounded flex items-center gap-1 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
              <span>REFRESH</span>
            </button>
            <button
              onClick={handleReLayout}
              className="px-2.5 py-1 bg-[#131b2e] border border-[#1e2d4a] hover:border-cyan-500/60 text-slate-300 hover:text-white text-xs font-mono font-bold rounded flex items-center gap-1 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
              <span>RE-LAYOUT</span>
            </button>
            <button
              onClick={onReturnToGraph}
              className="px-3 py-1 bg-cyan-950 border border-cyan-500/60 hover:bg-cyan-900 text-cyan-300 text-xs font-mono font-bold rounded transition-colors"
            >
              SINGLE CASE GRAPH ▶
            </button>
          </div>
        </div>
      </div>

      {/* ── Main Workspace Body (Canvas + Right Inspector Panel) ── */}
      <div className="flex-1 flex w-full h-full relative overflow-hidden">
        {/* Left: Cytoscape Graph Canvas Area */}
        <div className="flex-1 relative w-full h-full bg-graph-grid overflow-hidden">
          {isLoading && (
            <div className="absolute inset-0 z-30 flex items-center justify-center bg-[#0b0f19]/85 backdrop-blur-xs text-slate-300">
              <div className="flex items-center gap-2 font-mono text-xs">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
                EXPANDING CASE-ANCHORED INVESTIGATIVE UNIVERSE ({universeDepth} {universeDepth === 1 ? 'HOP' : 'HOPS'})...
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 z-30 flex items-center justify-center bg-[#0b0f19]/90 text-rose-400 font-mono text-xs">
              <div className="border border-rose-800/60 bg-rose-950/40 p-4 rounded max-w-md text-center">
                FAILED TO LOAD AUTHORIZED UNIVERSE TOPOLOGY
              </div>
            </div>
          )}

          {/* Top-Left Overlay Badge: PROVENANCE VIEW */}
          <div className="absolute top-4 left-4 z-20 pointer-events-none">
            <div className="px-3 py-1.5 rounded bg-[#0d1322]/90 border border-cyan-500/40 shadow-lg backdrop-blur-xs flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              <span className="text-[11px] font-mono font-bold text-cyan-300 uppercase tracking-wider">
                PROVENANCE VIEW ({universeDepth} {universeDepth === 1 ? 'HOP' : 'HOPS'})
              </span>
            </div>
          </div>

          {/* Bottom-Left Overlay Box: ENTITY TYPES Legend */}
          <div className="absolute bottom-12 left-4 z-20 bg-[#0d1322]/95 border border-[#1e2d4a] rounded p-3 shadow-2xl backdrop-blur-xs w-52 font-mono text-[11px]">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 border-b border-[#1e2d4a] pb-1 flex items-center justify-between">
              <span>ENTITY TYPES</span>
              <Layers className="w-3 h-3 text-cyan-400" />
            </div>
            <div className="grid grid-cols-2 gap-x-2 gap-y-1.5 text-[10px]">
              {[
                { type: 'Person', color: 'border-blue-500 bg-blue-950/60 text-blue-300' },
                { type: 'Organization', color: 'border-amber-500 bg-amber-950/60 text-amber-300' },
                { type: 'Vehicle', color: 'border-rose-500 bg-rose-950/60 text-rose-300' },
                { type: 'Phone', color: 'border-emerald-500 bg-emerald-950/60 text-emerald-300' },
                { type: 'Device', color: 'border-cyan-500 bg-cyan-950/60 text-cyan-300' },
                { type: 'Account', color: 'border-teal-500 bg-teal-950/60 text-teal-300' },
                { type: 'Evidence', color: 'border-slate-500 bg-slate-800/60 text-slate-300' },
                { type: 'Lead', color: 'border-pink-500 bg-pink-950/60 text-pink-300' },
              ].map(({ type, color }) => (
                <label key={type} className="flex items-center gap-1.5 cursor-pointer hover:text-white select-none">
                  <input
                    type="checkbox"
                    checked={!hiddenTypes.has(type)}
                    onChange={() => toggleEntityType(type)}
                    className="w-3 h-3 rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0"
                  />
                  <span className={`px-1 py-0.2 rounded border text-[9px] font-bold ${color}`}>
                    {type}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Epistemic Legend */}
          <EpistemicLegend />

          {/* Persistent Cytoscape Graph Canvas */}
          <GraphCanvas
            nodes={nodes}
            relationships={relationships}
            selectedNodeId={selectedNodeId}
            selectedEdgeId={selectedEdgeId}
            onSelectNode={onSelectNode}
            onSelectEdge={onSelectEdge}
            reLayoutTrigger={reLayoutTrigger}
            hiddenEntityTypes={hiddenTypes}
            hiddenRelTypes={new Set()}
            focusTrigger={null}
            activePathSourceId={null}
            activePathTargetId={null}
            activeThreadNodeId={null}
            onPathFound={() => {}}
          />

          {/* Bottom Canvas Status Bar */}
          <div className="absolute bottom-0 inset-x-0 h-8 bg-[#0d1322] border-t border-[#1e2d4a] px-4 flex items-center justify-between text-[11px] font-mono text-slate-400 z-20">
            <div className="flex items-center gap-4">
              <span><strong className="text-white">{nodes.length}</strong> entities</span>
              <span><strong className="text-white">{relationships.length}</strong> relationships</span>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-cyan-400/90">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              <span>ACL-enforced • bounded traversal • Neo4j / PostgreSQL</span>
            </div>
          </div>
        </div>

        {/* Right: Dedicated INSPECTOR Panel matching Reference Workstation */}
        <div className="w-80 bg-[#0d1322] border-l border-[#1e2d4a] flex flex-col shrink-0 h-full overflow-y-auto">
          <div className="p-3 border-b border-[#1e2d4a] bg-[#131b2e] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-cyan-400" />
              <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                INSPECTOR
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              {selectedNode ? 'ENTITY SELECTED' : selectedRelationship ? 'RELATIONSHIP SELECTED' : 'PROVENANCE UNIVERSE'}
            </span>
          </div>

          <div className="p-3 space-y-4">
            {/* PROVENANCE VIEW Info Card */}
            <div className="p-3 rounded border border-cyan-500/40 bg-cyan-950/20 space-y-1.5">
              <div className="flex items-center gap-1.5 text-cyan-400 font-mono font-bold text-xs uppercase">
                <FileText className="w-3.5 h-3.5" />
                <span>PROVENANCE VIEW</span>
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed font-sans">
                Shows the authorized connected investigative graph surrounding the active case, including available entity, evidence, assertion and event nodes for forensic review and provenance inspection.
              </p>
            </div>

            {/* GRAPH SUMMARY 4-Box Grid */}
            <div className="space-y-1.5">
              <div className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                GRAPH SUMMARY ({universeDepth} {universeDepth === 1 ? 'HOP' : 'HOPS'})
              </div>
              <div className="grid grid-cols-2 gap-2 font-mono">
                <div className="p-2.5 rounded bg-[#131b2e] border border-[#1e2d4a] text-center">
                  <div className="text-base font-bold text-white">{metrics.entities}</div>
                  <div className="text-[9px] text-slate-400 uppercase mt-0.5">Entities</div>
                </div>
                <div className="p-2.5 rounded bg-[#131b2e] border border-[#1e2d4a] text-center">
                  <div className="text-base font-bold text-cyan-400">{metrics.invLinks}</div>
                  <div className="text-[9px] text-slate-400 uppercase mt-0.5">Inv. Links</div>
                </div>
                <div className="p-2.5 rounded bg-[#131b2e] border border-[#1e2d4a] text-center">
                  <div className="text-base font-bold text-amber-400">{metrics.assertions}</div>
                  <div className="text-[9px] text-slate-400 uppercase mt-0.5">Assertions</div>
                </div>
                <div className="p-2.5 rounded bg-[#131b2e] border border-[#1e2d4a] text-center">
                  <div className="text-base font-bold text-emerald-400">{metrics.events}</div>
                  <div className="text-[9px] text-slate-400 uppercase mt-0.5">Events</div>
                </div>
              </div>
              <p className="text-[10px] text-slate-400 italic font-sans mt-1">
                Data-derived counts dynamically loaded for depth {universeDepth}.
              </p>
            </div>

            {/* Context Inspector Details */}
            {selectedNode && (
              <div className="border-t border-[#1e2d4a] pt-3">
                <EntityDossier
                  entityNode={selectedNode}
                  caseId={caseId}
                  onClose={() => onSelectNode(null)}
                />
              </div>
            )}

            {selectedRelationship && !selectedNode && (
              <div className="border-t border-[#1e2d4a] pt-3">
                <RelationshipInspector
                  relationship={selectedRelationship}
                  onClose={() => onSelectEdge(null)}
                />
              </div>
            )}

            {!selectedNode && !selectedRelationship && (
              <div className="border-t border-[#1e2d4a] pt-3 text-center p-4 font-mono text-[11px] text-slate-400 space-y-2">
                <Network className="w-8 h-8 text-cyan-500/40 mx-auto" />
                <p>Click any entity or relationship node in the graph canvas to inspect its full dossier, provenance, and connected evidence.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
