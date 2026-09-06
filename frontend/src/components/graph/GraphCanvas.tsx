import React, { useEffect, useRef, useCallback } from 'react';
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape';
import type { GraphNode, GraphRelationship } from '../../types/api';

interface GraphCanvasProps {
  nodes: GraphNode[];
  relationships: GraphRelationship[];
  selectedNodeId?: string | null;
  selectedEdgeId?: string | null;
  onSelectNode: (node: GraphNode | null) => void;
  onSelectEdge: (relId: string | null) => void;
  reLayoutTrigger: number; // Incrementing counter to trigger explicit user re-layout
  hiddenEntityTypes?: Set<string>;
  hiddenRelTypes?: Set<string>;
  focusTrigger?: { nodeId: string; timestamp: number } | null;
  activePathSourceId?: string | null;
  activePathTargetId?: string | null;
  isPathFiltered?: boolean;
  activeThreadNodeId?: string | null;
  onPathFound?: (nodes: GraphNode[], rels: GraphRelationship[]) => void;
}

// ── Institutional Node Color & Icon Configuration (NO PURPLE) ──
const NODE_TYPE_STYLES: Record<string, { bg: string; border: string; text: string }> = {
  Person: { bg: '#0f172a', border: '#3b82f6', text: '#93c5fd' },
  Organization: { bg: '#0f172a', border: '#d97706', text: '#fcd34d' },
  Device: { bg: '#0f172a', border: '#0284c7', text: '#7dd3fc' },
  PhoneNumber: { bg: '#0f172a', border: '#10b981', text: '#6ee7b7' },
  Vehicle: { bg: '#0f172a', border: '#ef4444', text: '#fca5a5' },
  FinancialAccount: { bg: '#0f172a', border: '#f59e0b', text: '#fde047' },
  Location: { bg: '#0f172a', border: '#059669', text: '#6ee7b7' },
  Evidence: { bg: '#0f172a', border: '#38bdf8', text: '#7dd3fc' }, // Compact cyan/blue, NO purple
  Case: { bg: '#0f172a', border: '#0284c7', text: '#7dd3fc' },
  Lead: { bg: '#0f172a', border: '#f43f5e', text: '#fda4af' },
};

const DEFAULT_NODE_STYLE = { bg: '#0f172a', border: '#64748b', text: '#cbd5e1' };

function getPrimaryLabel(labels: string[] = []): string {
  const priority = [
    'Person', 'Organization', 'Device', 'PhoneNumber',
    'Vehicle', 'FinancialAccount', 'Location', 'Evidence',
    'Case', 'Lead', 'Assertion', 'Event'
  ];
  for (const p of priority) {
    if (labels.includes(p)) return p;
  }
  return labels[0] || 'Entity';
}

function deriveNodeDisplayName(node: GraphNode): string {
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
  const cleaned = String(raw).replace(/_[0-9a-f]{8}$/i, '');
  return cleaned.length > 20 ? `${cleaned.slice(0, 18)}…` : cleaned;
}

// ── Cytoscape Stylesheet with Visual Lock ──
const CY_STYLESHEET: cytoscape.StylesheetStyle[] = [
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
      'color': '#f1f5f9',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': 6,
      'width': 36,
      'height': 36,
      'text-max-width': '110px',
      'text-wrap': 'wrap',
      'text-overflow-wrap': 'whitespace',
      'transition-property': 'border-width, border-color, background-color, opacity',
      'transition-duration': '150ms',
    } as any,
  },
  {
    selector: 'node[nodeType = "Evidence"]',
    style: {
      'shape': 'rectangle',
      'width': 34,
      'height': 34,
      'font-size': 9,
      'border-color': '#38bdf8',
    } as any,
  },
  {
    selector: 'node[nodeType = "Case"]',
    style: {
      'shape': 'round-rectangle',
      'width': 48,
      'height': 32,
      'font-size': 9,
    } as any,
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 3.5,
      'border-color': '#f59e0b', // Amber selection outline
      'background-color': '#1e293b',
      'z-index': 999,
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
      'text-background-color': '#0b0f19',
      'text-background-opacity': 0.9,
      'text-background-padding': '2px',
      'text-max-width': '120px',
      'text-wrap': 'ellipsis',
      'transition-property': 'width, line-color, opacity',
      'transition-duration': '150ms',
    } as any,
  },
  // Proposed Investigator Link (Dashed Amber)
  {
    selector: 'edge[proposalStatus = "PROPOSED"]',
    style: {
      'line-style': 'dashed',
      'line-dash-pattern': [6, 4],
      'line-color': '#f59e0b',
      'target-arrow-color': '#f59e0b',
      'color': '#fcd34d',
    } as any,
  },
  {
    selector: 'edge:selected',
    style: {
      'width': 3,
      'line-color': '#f59e0b',
      'target-arrow-color': '#f59e0b',
      'z-index': 999,
    } as any,
  },
  // ── Path & Thread Highlighting Rules (Zero Layout Reflow) ──
  {
    selector: '.de-emphasized',
    style: {
      'opacity': 0.15,
    } as any,
  },
  {
    selector: 'node.path-highlighted',
    style: {
      'border-width': 4,
      'border-color': '#38bdf8',
      'background-color': '#0369a1',
      'z-index': 9999,
      'opacity': 1.0,
    } as any,
  },
  {
    selector: 'edge.path-highlighted',
    style: {
      'width': 3.5,
      'line-color': '#38bdf8',
      'target-arrow-color': '#38bdf8',
      'z-index': 9999,
      'opacity': 1.0,
    } as any,
  },
  {
    selector: 'node.thread-highlighted',
    style: {
      'border-width': 3.5,
      'border-color': '#22d3ee',
      'z-index': 999,
      'opacity': 1.0,
    } as any,
  },
  {
    selector: 'edge.thread-highlighted',
    style: {
      'width': 2.5,
      'line-color': '#22d3ee',
      'target-arrow-color': '#22d3ee',
      'z-index': 999,
      'opacity': 1.0,
    } as any,
  },
];

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  nodes,
  relationships,
  selectedNodeId,
  selectedEdgeId,
  onSelectNode,
  onSelectEdge,
  reLayoutTrigger,
  hiddenEntityTypes,
  hiddenRelTypes,
  focusTrigger,
  activePathSourceId,
  activePathTargetId,
  isPathFiltered,
  activeThreadNodeId,
  onPathFound,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  // Initialize Cytoscape core instance persistent reference
  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      style: CY_STYLESHEET,
      boxSelectionEnabled: false,
      autounselectify: false,
      wheelSensitivity: 0.25,
      minZoom: 0.2,
      maxZoom: 3.0,
    });

    cyRef.current = cy;

    // Node selection handler
    cy.on('tap', 'node', (evt) => {
      const nodeData = evt.target.data();
      const rawNode = nodeData.rawNode as GraphNode;
      onSelectNode(rawNode || null);
    });

    // Edge selection handler
    cy.on('tap', 'edge', (evt) => {
      const edgeData = evt.target.data();
      onSelectEdge(edgeData.id || null);
    });

    // Tap background clears selection
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        onSelectNode(null);
        onSelectEdge(null);
      }
    });

    // ResizeObserver for dynamic container size changes (e.g. inspector drawer collapse/expand)
    const container = containerRef.current;
    let observer: ResizeObserver | null = null;
    if (container && typeof ResizeObserver !== 'undefined') {
      observer = new ResizeObserver(() => {
        if (cyRef.current) {
          cyRef.current.resize();
        }
      });
      observer.observe(container);
    }

    return () => {
      if (observer) {
        observer.disconnect();
      }
      cy.destroy();
      cyRef.current = null;
    };
  }, []);

  // Update Cytoscape Elements (Differential update without re-creating instance)
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    const cyElements: ElementDefinition[] = [];

    // Filter infrastructure nodes (Assertion/Event nodes handled as edges or compact nodes)
    for (const node of nodes) {
      const primaryType = getPrimaryLabel(node.labels);
      const name = deriveNodeDisplayName(node);
      const style = NODE_TYPE_STYLES[primaryType] || DEFAULT_NODE_STYLE;

      // Compact evidence formatting: e.g. "◉ CCTV-07\nEVIDENCE"
      const label = primaryType === 'Evidence'
        ? `◉ ${name}\nEVIDENCE`
        : name;

      cyElements.push({
        group: 'nodes',
        data: {
          id: node.id,
          label,
          name,
          nodeType: primaryType,
          bgColor: style.bg,
          borderColor: style.border,
          textColor: style.text,
          rawNode: node,
        },
      });
    }

    for (const rel of relationships) {
      cyElements.push({
        group: 'edges',
        data: {
          id: rel.id,
          source: rel.start_node,
          target: rel.end_node,
          label: rel.type.replace(/_/g, ' '),
          proposalStatus: rel.properties?.proposal_status || 'CONFIRMED',
          rawRel: rel,
        },
      });
    }

    cy.batch(() => {
      cy.elements().remove();
      cy.add(cyElements);
    });

    // Detect multi-case graph status
    const caseCount = cy.nodes('[nodeType = "Case"]').length;
    const hasMultipleCases = caseCount >= 2;

    // Run COSE layout on ALL elements so every node receives pre-computed coordinates.
    // Expands edge length and node repulsion to naturally fill the full canvas space.
    const layout = cy.elements().layout({
      name: 'cose',
      animate: false,
      randomize: false,
      componentSpacing: hasMultipleCases ? 260 : 160,
      nodeRepulsion: (node: any) => {
        const type = node.data('nodeType');
        if (type === 'Case') return hasMultipleCases ? 50000 : 20000;
        if (type === 'Lead') return 22000;
        return 16000;
      },
      idealEdgeLength: (edge: any) => {
        const srcType = edge.source().data('nodeType');
        const tgtType = edge.target().data('nodeType');
        if (srcType === 'Case' || tgtType === 'Case') {
          return hasMultipleCases ? 280 : 180;
        }
        return 140;
      },
      gravity: hasMultipleCases ? 0.05 : 0.12,
      edgeElasticity: (edge: any) => {
        const srcType = edge.source().data('nodeType');
        const tgtType = edge.target().data('nodeType');
        if (srcType === 'Case' || tgtType === 'Case') return 20;
        return 80;
      },
      numIter: 1800,
    });
    layout.run();

    // Apply visibility filter after layout calculation
    cy.batch(() => {
      cy.nodes().forEach((nodeEle) => {
        const type = nodeEle.data('nodeType');
        if (hiddenEntityTypes && hiddenEntityTypes.has(type)) {
          nodeEle.style('display', 'none');
        } else {
          nodeEle.style('display', 'element');
        }
      });
      cy.edges().forEach((edgeEle) => {
        const relType = edgeEle.data('rawRel')?.type;
        if (hiddenRelTypes && hiddenRelTypes.has(relType)) {
          edgeEle.style('display', 'none');
        } else {
          edgeEle.style('display', 'element');
        }
      });
    });

    cy.resize();
    const visibleElements = cy.elements(':visible');
    cy.fit(visibleElements.length > 0 ? visibleElements : undefined, 30);
  }, [nodes, relationships]);

  // Handle Selection Highlights without triggering layout reflow
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.batch(() => {
      cy.elements().removeClass('selected');
      if (selectedNodeId) {
        cy.getElementById(selectedNodeId).select();
      }
      if (selectedEdgeId) {
        cy.getElementById(selectedEdgeId).select();
      }
    });
  }, [selectedNodeId, selectedEdgeId]);

  // Handle Visual Filter Toggles (Zero-Layout-Reflow Element Hiding/Showing with Fit)
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.batch(() => {
      cy.nodes().forEach((nodeEle) => {
        const type = nodeEle.data('nodeType');
        if (hiddenEntityTypes && hiddenEntityTypes.has(type)) {
          nodeEle.style('display', 'none');
        } else {
          nodeEle.style('display', 'element');
        }
      });

      cy.edges().forEach((edgeEle) => {
        const relType = edgeEle.data('rawRel')?.type;
        if (hiddenRelTypes && hiddenRelTypes.has(relType)) {
          edgeEle.style('display', 'none');
        } else {
          edgeEle.style('display', 'element');
        }
      });
    });

    const visibleElements = cy.elements(':visible');
    if (visibleElements.length > 0) {
      cy.fit(visibleElements, 35);
    }
  }, [hiddenEntityTypes, hiddenRelTypes]);

  // Handle Focus on Node (Pan & Zoom Animation without layout reflow)
  useEffect(() => {
    if (!focusTrigger?.nodeId) return;
    const cy = cyRef.current;
    if (!cy) return;

    const ele = cy.getElementById(focusTrigger.nodeId);
    if (ele && ele.length > 0) {
      cy.animate({
        center: { eles: ele },
        zoom: 1.2,
        duration: 350,
      });
    }
  }, [focusTrigger]);

  // Handle Pathfinding and Thread Highlighting (Zero Layout Reflow)
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.batch(() => {
      cy.elements().removeClass('path-highlighted thread-highlighted de-emphasized');

      if (activePathSourceId && activePathTargetId) {
        const sourceEle = cy.getElementById(activePathSourceId);
        const targetEle = cy.getElementById(activePathTargetId);

        if (sourceEle.length > 0 && targetEle.length > 0) {
          const dijkstra = cy.elements().dijkstra({
            root: sourceEle,
            directed: false,
          });

          const path = dijkstra.pathTo(targetEle);

          if (path && path.length > 0) {
            if (isPathFiltered) {
              // Hide all elements not in path
              cy.elements().forEach((ele) => {
                if (path.contains(ele)) {
                  ele.style('display', 'element');
                  ele.addClass('path-highlighted');
                } else {
                  ele.style('display', 'none');
                }
              });
              cy.fit(path, 60);
            } else {
              // Reset element display based on entity filter & highlight path
              cy.nodes().forEach((nodeEle) => {
                const type = nodeEle.data('nodeType');
                if (hiddenEntityTypes && hiddenEntityTypes.has(type)) {
                  nodeEle.style('display', 'none');
                } else {
                  nodeEle.style('display', 'element');
                }
              });
              cy.edges().forEach((edgeEle) => {
                const relType = edgeEle.data('rawRel')?.type;
                if (hiddenRelTypes && hiddenRelTypes.has(relType)) {
                  edgeEle.style('display', 'none');
                } else {
                  edgeEle.style('display', 'element');
                }
              });
              cy.elements().addClass('de-emphasized');
              path.removeClass('de-emphasized').addClass('path-highlighted');
            }

            if (onPathFound) {
              const nodesOnPath: GraphNode[] = [];
              const relsOnPath: GraphRelationship[] = [];

              path.forEach((ele) => {
                if (ele.isNode()) {
                  const nodeData = ele.data('rawNode');
                  if (nodeData) nodesOnPath.push(nodeData);
                } else if (ele.isEdge()) {
                  const relData = ele.data('rawRel');
                  if (relData) relsOnPath.push(relData);
                }
              });

              onPathFound(nodesOnPath, relsOnPath);
            }
          } else {
            if (onPathFound) onPathFound([], []);
          }
        }
      } else if (activeThreadNodeId) {
        const rootEle = cy.getElementById(activeThreadNodeId);
        if (rootEle.length > 0) {
          const neighborhood = rootEle.neighborhood().union(rootEle);
          const extendedNeighborhood = neighborhood.neighborhood().union(neighborhood);

          cy.elements().addClass('de-emphasized');
          extendedNeighborhood.removeClass('de-emphasized').addClass('thread-highlighted');
        }
      } else {
        // Reset display to normal when not in pathfinding mode
        cy.nodes().forEach((nodeEle) => {
          const type = nodeEle.data('nodeType');
          if (hiddenEntityTypes && hiddenEntityTypes.has(type)) {
            nodeEle.style('display', 'none');
          } else {
            nodeEle.style('display', 'element');
          }
        });
        cy.edges().forEach((edgeEle) => {
          const relType = edgeEle.data('rawRel')?.type;
          if (hiddenRelTypes && hiddenRelTypes.has(relType)) {
            edgeEle.style('display', 'none');
          } else {
            edgeEle.style('display', 'element');
          }
        });
      }
    });
  }, [activePathSourceId, activePathTargetId, activeThreadNodeId, isPathFiltered, hiddenEntityTypes, hiddenRelTypes, onPathFound]);

  // Explicit User-Controlled RE-LAYOUT Trigger
  useEffect(() => {
    if (reLayoutTrigger === 0) return;
    const cy = cyRef.current;
    if (!cy) return;

    const caseCount = cy.nodes('[nodeType = "Case"]').length;
    const hasMultipleCases = caseCount >= 2;

    const layout = cy.layout({
      name: 'cose',
      animate: true,
      animationDuration: 450,
      randomize: true,
      componentSpacing: hasMultipleCases ? 260 : 160,
      nodeRepulsion: (node: any) => {
        const type = node.data('nodeType');
        if (type === 'Case') return hasMultipleCases ? 50000 : 20000;
        if (type === 'Lead') return 22000;
        return 16000;
      },
      idealEdgeLength: (edge: any) => {
        const srcType = edge.source().data('nodeType');
        const tgtType = edge.target().data('nodeType');
        if (srcType === 'Case' || tgtType === 'Case') {
          return hasMultipleCases ? 280 : 180;
        }
        return 140;
      },
      gravity: hasMultipleCases ? 0.05 : 0.12,
      numIter: 1800,
    });
    layout.run();
  }, [reLayoutTrigger]);

  return (
    <div className="relative w-full h-full bg-graph-grid overflow-hidden">
      {/* ── Blank Dark Canvas with Low-Contrast Graph Grid Container ── */}
      <div ref={containerRef} className="w-full h-full civix-graph-canvas" />
    </div>
  );
};
