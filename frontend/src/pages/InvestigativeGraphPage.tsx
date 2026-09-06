import React, { useState, useCallback, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { GitFork } from 'lucide-react';
import { graphApi } from '../api/graph';
import { casesApi } from '../api/cases';
import type { GraphNode, GraphRelationship } from '../types/api';
import type { WorkspaceMode, AssertionProposalResponse, InvestigationTrailItem } from '../types/graph';

import { GraphWorkspaceShell } from '../components/graph/GraphWorkspaceShell';
import { GraphHeader } from '../components/graph/GraphHeader';
import { GraphToolbar } from '../components/graph/GraphToolbar';
import { GraphCanvas } from '../components/graph/GraphCanvas';
import { GraphExplorer } from '../components/graph/GraphExplorer';
import { EntityDossier } from '../components/graph/EntityDossier';
import { RelationshipInspector } from '../components/graph/RelationshipInspector';
import { EpistemicLegend } from '../components/graph/EpistemicLegend';
import { InvestigationTrail } from '../components/graph/InvestigationTrail';
import { CaseContextView } from '../components/graph/CaseContextView';
import { IntelligenceContextView } from '../components/graph/IntelligenceContextView';
import { ReportsContextView } from '../components/graph/ReportsContextView';
import { ProvenanceUniverseView } from '../components/graph/ProvenanceUniverseView';
import { ProposalDrawer } from '../components/graph/ProposalDrawer';
import { PathAnalysisPanel } from '../components/graph/PathAnalysisPanel';

const DEFAULT_DEPTH = 2;
const DEFAULT_NODE_LIMIT = 150;
const DEFAULT_REL_LIMIT = 300;

interface InvestigativeGraphPageProps {
  caseIdProp?: string;
  embedded?: boolean;
}

export const InvestigativeGraphPage: React.FC<InvestigativeGraphPageProps> = ({
  caseIdProp,
}) => {
  const queryClient = useQueryClient();
  const { caseId: paramCaseId } = useParams<{ caseId: string }>();
  const caseId = caseIdProp || paramCaseId;

  // Workspace Mode & Tab State
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>('EXPLORE');
  const [activeTab, setActiveTab] = useState<'GRAPH' | 'CASE_CONTEXT' | 'INTELLIGENCE' | 'REPORTS'>('GRAPH');
  const [explorerTab, setExplorerTab] = useState<'SEARCH' | 'FILTERS' | 'PATH'>('SEARCH');
  const [depth, setDepth] = useState<number>(DEFAULT_DEPTH);
  const [reLayoutCounter, setReLayoutCounter] = useState<number>(0);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // Selection States
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  // Investigation Trail Navigation Stack
  const [trail, setTrail] = useState<InvestigationTrailItem[]>([]);

  // Pathfinding States
  const [pathSourceNode, setPathSourceNode] = useState<GraphNode | null>(null);
  const [pathTargetNode, setPathTargetNode] = useState<GraphNode | null>(null);
  const [pathNodes, setPathNodes] = useState<GraphNode[]>([]);
  const [pathRelationships, setPathRelationships] = useState<GraphRelationship[]>([]);
  const [isPathFiltered, setIsPathFiltered] = useState<boolean>(false);

  // Proposal Drawer State
  const [isProposalDrawerOpen, setIsProposalDrawerOpen] = useState<boolean>(false);
  const [proposalTargetNode, setProposalTargetNode] = useState<GraphNode | null>(null);

  // Zero-Layout-Reflow Filtering States (Evidence hidden by default on first load for clean cluster)
  const [hiddenEntityTypes, setHiddenEntityTypes] = useState<Set<string>>(new Set(['Evidence']));
  const [hiddenRelTypes, setHiddenRelTypes] = useState<Set<string>>(new Set());

  // Focus Trigger State
  const [focusTrigger, setFocusTrigger] = useState<{ nodeId: string; timestamp: number } | null>(null);

  // ── Fetch Case Metadata ──
  const { data: caseData } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => (caseId ? casesApi.getCase(caseId) : Promise.reject(new Error('No case ID'))),
    enabled: !!caseId,
    staleTime: 60_000,
  });

  // ── Fetch Authoritative Graph Network Data (1H..5H Depth Supported) ──
  const { data: graphData, isLoading: graphLoading, error: graphError } = useQuery({
    queryKey: ['graph', caseId, depth],
    queryFn: () =>
      caseId
        ? graphApi.getCaseGraph(caseId, depth)
        : Promise.reject(new Error('No case ID')),
    enabled: !!caseId,
    staleTime: 30_000,
  });

  // Dynamic Intelligence Counts
  const counts = useMemo(() => {
    const nodes = graphData?.nodes || [];
    const rels = graphData?.relationships || [];
    const entities = nodes.filter((n) => !n.labels.includes('Case') && !n.labels.includes('Evidence') && !n.labels.includes('Event')).length;
    const evidence = nodes.filter((n) => n.labels.includes('Evidence')).length;
    const events = nodes.filter((n) => n.labels.includes('Event')).length;
    const cases = nodes.filter((n) => n.labels.includes('Case')).length;
    return {
      entities,
      relationships: rels.length,
      cases: cases || 1,
      events,
      evidence,
      leads: 0,
    };
  }, [graphData]);

  // Mode Change Handler
  const handleModeChange = useCallback((newMode: WorkspaceMode) => {
    setWorkspaceMode(newMode);
    if (newMode === 'CONNECT_ENTITY') {
      setIsProposalDrawerOpen(true);
    } else if (newMode === 'FIND_PATH') {
      setIsPathFiltered(false);
      setExplorerTab('PATH');
      if (selectedNode) {
        setPathSourceNode(selectedNode);
      }
    } else if (newMode === 'EXPLORE') {
      setPathSourceNode(null);
      setPathTargetNode(null);
      setPathNodes([]);
      setPathRelationships([]);
      setIsPathFiltered(false);
      setExplorerTab('SEARCH');
    }
  }, [selectedNode]);

  // Handlers
  const handleReLayout = useCallback(() => {
    setReLayoutCounter((prev) => prev + 1);
  }, []);

  const handleReset = useCallback(() => {
    setReLayoutCounter((prev) => prev + 1);
    setHiddenEntityTypes(new Set());
    setHiddenRelTypes(new Set());
    setSelectedNode(null);
    setSelectedEdgeId(null);
    setWorkspaceMode('EXPLORE');
    setPathSourceNode(null);
    setPathTargetNode(null);
    setPathNodes([]);
    setPathRelationships([]);
    setIsPathFiltered(false);
    setIsProposalDrawerOpen(false);
  }, []);

  const handleToggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
        setIsFullscreen(false);
      }
    }
  }, []);

  const handleToggleEntityType = useCallback((type: string) => {
    setHiddenEntityTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  }, []);

  const handleToggleRelType = useCallback((type: string) => {
    setHiddenRelTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  }, []);

  const handleResetFilters = useCallback(() => {
    setHiddenEntityTypes(new Set());
    setHiddenRelTypes(new Set());
  }, []);

  // Node Selection Handler + Trail Update
  const handleSelectNode = useCallback((node: GraphNode | null) => {
    setSelectedNode(node);
    if (!node) return;

    setSelectedEdgeId(null); // Clear edge selection when node is selected
    const p = node.properties || {};
    const rawLabel = p.display_name || p.name || p.legal_name || p.msisdn || p.registration_number || node.id;
    const cleanLabel = String(rawLabel).replace(/_[0-9a-f]{8}$/i, '');

    setTrail((prev) => {
      if (prev.some((t) => t.id === node.id)) return prev;
      return [...prev, { id: node.id, label: cleanLabel, type: 'ENTITY' }];
    });

    if (workspaceMode === 'FIND_PATH') {
      if (!pathSourceNode) {
        setPathSourceNode(node);
      } else if (pathSourceNode.id !== node.id) {
        setPathTargetNode(node);
      } else {
        setPathSourceNode(node);
        setPathTargetNode(null);
      }
    } else if (workspaceMode === 'CONNECT_ENTITY') {
      if (selectedNode && selectedNode.id !== node.id) {
        setProposalTargetNode(node);
        setIsProposalDrawerOpen(true);
      }
    } else {
      setFocusTrigger({ nodeId: node.id, timestamp: Date.now() });
    }
  }, [workspaceMode, pathSourceNode, selectedNode]);

  // Edge Selection Handler + Trail Update
  const handleSelectEdge = useCallback((edgeId: string | null) => {
    setSelectedEdgeId(edgeId);
    if (!edgeId) return;

    setSelectedNode(null); // Clear node selection when edge is selected
    const rel = graphData?.relationships.find((r) => r.id === edgeId);
    if (rel) {
      setTrail((prev) => {
        if (prev.some((t) => t.id === edgeId)) return prev;
        return [...prev, { id: edgeId, label: rel.type.replace(/_/g, ' '), type: 'RELATIONSHIP' }];
      });
    }
  }, [graphData]);

  const handleSelectTrailItem = useCallback((item: InvestigationTrailItem) => {
    if (item.type === 'ENTITY') {
      const node = graphData?.nodes.find((n) => n.id === item.id);
      if (node) {
        setSelectedNode(node);
        setSelectedEdgeId(null);
        setFocusTrigger({ nodeId: node.id, timestamp: Date.now() });
        setActiveTab('GRAPH');
      }
    } else if (item.type === 'RELATIONSHIP') {
      setSelectedEdgeId(item.id);
      setSelectedNode(null);
      setActiveTab('GRAPH');
    }
  }, [graphData]);

  const handleClearTrail = useCallback(() => {
    setTrail([]);
  }, []);

  const handleFocusNode = useCallback((nodeId: string) => {
    setWorkspaceMode('FOCUS');
    setFocusTrigger({ nodeId, timestamp: Date.now() });
  }, []);

  const handleSeeThread = useCallback((nodeId: string) => {
    setWorkspaceMode('SEE_THREAD');
    setFocusTrigger({ nodeId, timestamp: Date.now() });
  }, []);

  const handlePathFound = useCallback((pNodes: GraphNode[], pRels: GraphRelationship[]) => {
    setPathNodes(pNodes);
    setPathRelationships(pRels);
  }, []);

  const handleToggleShowPath = useCallback(() => {
    setIsPathFiltered((prev) => !prev);
  }, []);

  const handleClearPath = useCallback(() => {
    setPathSourceNode(null);
    setPathTargetNode(null);
    setPathNodes([]);
    setPathRelationships([]);
    setIsPathFiltered(false);
    setWorkspaceMode('EXPLORE');
    setExplorerTab('SEARCH');
  }, []);

  const handleProposalSubmitted = useCallback((_resp: AssertionProposalResponse) => {
    if (caseId) {
      queryClient.invalidateQueries({ queryKey: ['graph', caseId] });
    }
  }, [caseId, queryClient]);

  const selectedEdgeRelationship = useMemo(() => {
    if (!selectedEdgeId || !graphData?.relationships) return null;
    return graphData.relationships.find((r) => r.id === selectedEdgeId) || null;
  }, [selectedEdgeId, graphData]);

  return (
    <GraphWorkspaceShell
      header={
        <GraphHeader
          caseData={caseData}
          counts={counts}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          isEvidenceVisible={!hiddenEntityTypes.has('Evidence')}
          onToggleEvidence={() => handleToggleEntityType('Evidence')}
        />
      }
      leftExplorer={
        activeTab === 'GRAPH' ? (
          <GraphExplorer
            nodes={graphData?.nodes || []}
            relationships={graphData?.relationships || []}
            selectedNodeId={selectedNode?.id || null}
            onSelectNode={handleSelectNode}
            hiddenEntityTypes={hiddenEntityTypes}
            onToggleEntityType={handleToggleEntityType}
            hiddenRelTypes={hiddenRelTypes}
            onToggleRelType={handleToggleRelType}
            onResetFilters={handleResetFilters}
            activeTabProp={explorerTab}
            onTabChangeProp={setExplorerTab}
            pathSourceNode={pathSourceNode}
            pathTargetNode={pathTargetNode}
            pathNodes={pathNodes}
            pathRelationships={pathRelationships}
            isPathFiltered={isPathFiltered}
            onSetSourceNode={setPathSourceNode}
            onSetTargetNode={setPathTargetNode}
            onToggleShowPath={handleToggleShowPath}
            onClearPath={handleClearPath}
          />
        ) : undefined
      }
      centerCanvas={
        <div className="flex flex-col h-full w-full relative overflow-hidden bg-graph-grid">
          {/* Action Ribbon Toolbar (GRAPH tab only) */}
          {activeTab === 'GRAPH' && (
            <GraphToolbar
              mode={workspaceMode}
              onModeChange={handleModeChange}
              hopDepth={depth}
              onHopDepthChange={setDepth}
              onReLayout={handleReLayout}
              onReset={handleReset}
              isFullscreen={isFullscreen}
              onToggleFullscreen={handleToggleFullscreen}
              isNeo4jLive={true}
              isEvidenceVisible={!hiddenEntityTypes.has('Evidence')}
              evidenceCount={counts.evidence}
              onToggleEvidence={() => handleToggleEntityType('Evidence')}
            />
          )}

          {/* Tab 1: GRAPH (Persistent Cytoscape Canvas container) */}
          <div className={`flex-1 relative w-full h-full ${activeTab === 'GRAPH' ? 'block' : 'hidden'}`}>
            {graphLoading && (
              <div className="absolute inset-0 z-30 flex items-center justify-center bg-[#0b0f19]/80 backdrop-blur-xs text-slate-300">
                <div className="flex items-center gap-2 font-mono text-xs">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                  LOADING INVESTIGATIVE GRAPH NETWORK...
                </div>
              </div>
            )}

            {graphError && (
              <div className="absolute inset-0 z-30 flex items-center justify-center bg-[#0b0f19]/90 text-rose-400">
                <div className="font-mono text-xs border border-rose-800/60 bg-rose-950/40 p-4 rounded max-w-md text-center">
                  FAILED TO LOAD GRAPH NETWORK DATA
                </div>
              </div>
            )}

            {/* Canvas Legend */}
            <EpistemicLegend />

            <GraphCanvas
              nodes={graphData?.nodes || []}
              relationships={graphData?.relationships || []}
              selectedNodeId={selectedNode?.id || null}
              selectedEdgeId={selectedEdgeId}
              onSelectNode={handleSelectNode}
              onSelectEdge={handleSelectEdge}
              reLayoutTrigger={reLayoutCounter}
              hiddenEntityTypes={hiddenEntityTypes}
              hiddenRelTypes={hiddenRelTypes}
              focusTrigger={focusTrigger}
              activePathSourceId={pathSourceNode?.id || null}
              activePathTargetId={pathTargetNode?.id || null}
              isPathFiltered={isPathFiltered}
              activeThreadNodeId={workspaceMode === 'SEE_THREAD' ? selectedNode?.id || null : null}
              onPathFound={handlePathFound}
            />
          </div>

          {/* Tab 2: CASE CONTEXT */}
          {activeTab === 'CASE_CONTEXT' && (
            <CaseContextView caseId={caseId || ''} caseData={caseData} />
          )}

          {/* Tab 3: INTELLIGENCE */}
          {activeTab === 'INTELLIGENCE' && (
            <IntelligenceContextView
              caseId={caseId || ''}
              caseData={caseData}
              graphNodes={graphData?.nodes || []}
              graphRelationships={graphData?.relationships || []}
              onSelectNode={handleSelectNode}
              onShowPathOnGraph={(sourceId, targetId) => {
                const srcNode = graphData?.nodes.find((n) => n.id === sourceId || n.properties?.entity_id === sourceId);
                const tgtNode = targetId ? graphData?.nodes.find((n) => n.id === targetId || n.properties?.entity_id === targetId) : undefined;

                if (srcNode && tgtNode) {
                  setPathSourceNode(srcNode);
                  setPathTargetNode(tgtNode);
                  setIsPathFiltered(true);
                  setWorkspaceMode('FIND_PATH');
                  setExplorerTab('PATH');
                } else if (srcNode) {
                  setSelectedNode(srcNode);
                  setFocusTrigger({ nodeId: srcNode.id, timestamp: Date.now() });
                }
                setActiveTab('GRAPH');
              }}
            />
          )}

          {/* Tab 5: REPORTS */}
          {activeTab === 'REPORTS' && (
            <ReportsContextView
              caseId={caseId || ''}
              caseData={caseData}
              graphNodes={graphData?.nodes || []}
              graphRelationships={graphData?.relationships || []}
            />
          )}

          {/* Proposal Drawer (Connect Entity Workflow) */}
          {caseId && (
            <ProposalDrawer
              isOpen={isProposalDrawerOpen}
              caseId={caseId}
              sourceNode={selectedNode}
              targetNode={proposalTargetNode}
              allNodes={graphData?.nodes || []}
              onClose={() => setIsProposalDrawerOpen(false)}
              onProposalSubmitted={handleProposalSubmitted}
            />
          )}
        </div>
      }
      rightDossier={
        selectedEdgeRelationship ? (
          <RelationshipInspector
            relationship={selectedEdgeRelationship}
            allNodes={graphData?.nodes || []}
            onClose={() => setSelectedEdgeId(null)}
            onSelectNode={(node) => {
              setSelectedNode(node);
              setSelectedEdgeId(null);
            }}
          />
        ) : selectedNode ? (
          <EntityDossier
            node={selectedNode}
            relationships={graphData?.relationships || []}
            allNodes={graphData?.nodes || []}
            caseData={caseData}
            onClose={() => setSelectedNode(null)}
            onSeeThread={handleSeeThread}
            onFocusNode={handleFocusNode}
            onSelectNode={(node) => {
              setSelectedNode(node);
              setSelectedEdgeId(null);
            }}
          />
        ) : undefined
      }
      bottomBar={
        <InvestigationTrail
          trail={trail}
          onSelectTrailItem={handleSelectTrailItem}
          onClearTrail={handleClearTrail}
        />
      }
    />
  );
};

export default InvestigativeGraphPage;

