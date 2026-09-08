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
  isFocusMode?: boolean;
  focusNodeId?: string | null;
  focusHopDepth?: number;
  activePathSourceId?: string | null;
  activePathTargetId?: string | null;
  isPathFiltered?: boolean;
  activeThreadNodeId?: string | null;
  onPathFound?: (nodes: GraphNode[], rels: GraphRelationship[]) => void;
}

// ── Institutional Solid Color Node & Shape Configuration ──
const NODE_TYPE_STYLES: Record<string, { bg: string; border: string; text: string; shape: string }> = {
  Person: { bg: '#2563eb', border: '#93c5fd', text: '#ffffff', shape: 'ellipse' },           // Solid Vibrant Royal Blue (Circle)
  Case: { bg: '#d97706', border: '#fef08a', text: '#ffffff', shape: 'rectangle' },            // Solid Amber Gold (Square)
  Vehicle: { bg: '#dc2626', border: '#fca5a5', text: '#ffffff', shape: 'round-rectangle' },   // Solid Crimson Red (Capsule)
  Evidence: { bg: '#0284c7', border: '#bae6fd', text: '#ffffff', shape: 'rectangle' },        // Solid Sky Blue (Document Sheet)
  Location: { bg: '#059669', border: '#a7f3d0', text: '#ffffff', shape: 'pentagon' },         // Solid Emerald Green (Map Pin Pentagon)
  Organization: { bg: '#ea580c', border: '#ffedd5', text: '#ffffff', shape: 'diamond' },     // Solid Dark Orange (Building Diamond)
  Device: { bg: '#0d9488', border: '#99f6e4', text: '#ffffff', shape: 'rhomboid' },           // Solid Teal (Rhomboid)
  PhoneNumber: { bg: '#0d9488', border: '#99f6e4', text: '#ffffff', shape: 'rhomboid' },      // Solid Teal (Rhomboid)
  FinancialAccount: { bg: '#ca8a04', border: '#fef9c3', text: '#ffffff', shape: 'round-rectangle' },
  Lead: { bg: '#e11d48', border: '#fecdd3', text: '#ffffff', shape: 'hexagon' },
};

const DEFAULT_NODE_STYLE = { bg: '#475569', border: '#cbd5e1', text: '#ffffff', shape: 'ellipse' };

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

function getSymbolicIcon(type: string): string {
  switch (type) {
    case 'Person': return '👤 ';
    case 'Case': return '📁 ';
    case 'Vehicle': return '🚗 ';
    case 'Evidence': return '📄 ';
    case 'Location': return '📍 ';
    case 'Organization': return '🏢 ';
    case 'PhoneNumber':
    case 'Device': return '📱 ';
    case 'FinancialAccount': return '💳 ';
    default: return '◈ ';
  }
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

// ── Cytoscape Stylesheet with Solid Color Entity Palettes ──
const CY_STYLESHEET: cytoscape.StylesheetStyle[] = [
  {
    selector: 'node',
    style: {
      'shape': 'data(shape)',
      'background-color': 'data(bgColor)',
      'border-color': 'data(borderColor)',
      'border-width': 2.5,
      'label': 'data(label)',
      'font-family': 'IBM Plex Mono, monospace',
      'font-size': 10,
      'font-weight': '700',
      'color': '#ffffff',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': 6,
      'width': 38,
      'height': 38,
      'text-max-width': '120px',
      'text-wrap': 'wrap',
      'text-overflow-wrap': 'whitespace',
      'transition-property': 'border-width, border-color, background-color, opacity',
      'transition-duration': '150ms',
    } as any,
  },
  // Person → Circular Node (Solid Royal Blue)
  {
    selector: 'node[nodeType = "Person"]',
    style: {
      'shape': 'ellipse',
      'width': 40,
      'height': 40,
      'background-color': '#2563eb',
      'border-color': '#93c5fd',
      'border-width': 3.0,
      'color': '#ffffff',
    } as any,
  },
  // Case → Square Node (Solid Amber Gold)
  {
    selector: 'node[nodeType = "Case"]',
    style: {
      'shape': 'rectangle',
      'width': 48,
      'height': 48,
      'background-color': '#d97706',
      'border-color': '#fef08a',
      'border-width': 3.5,
      'color': '#ffffff',
      'font-size': 10,
    } as any,
  },
  // Vehicle → Capsule Node (Solid Crimson Red)
  {
    selector: 'node[nodeType = "Vehicle"]',
    style: {
      'shape': 'round-rectangle',
      'width': 54,
      'height': 34,
      'background-color': '#dc2626',
      'border-color': '#fca5a5',
      'border-width': 3.0,
      'color': '#ffffff',
    } as any,
  },
  // Evidence → Document Sheet Node (Solid Sky Blue)
  {
    selector: 'node[nodeType = "Evidence"]',
    style: {
      'shape': 'rectangle',
      'width': 34,
      'height': 46,
      'background-color': '#0284c7',
      'border-color': '#bae6fd',
      'border-width': 3.0,
      'color': '#ffffff',
      'font-size': 9,
    } as any,
  },
  // Location → Map Pentagon Pin (Solid Emerald Green)
  {
    selector: 'node[nodeType = "Location"]',
    style: {
      'shape': 'pentagon',
      'width': 44,
      'height': 44,
      'background-color': '#059669',
      'border-color': '#a7f3d0',
      'border-width': 3.0,
      'color': '#ffffff',
    } as any,
  },
  // Organization → Building Diamond (Solid Dark Orange)
  {
    selector: 'node[nodeType = "Organization"]',
    style: {
      'shape': 'diamond',
      'width': 46,
      'height': 46,
      'background-color': '#ea580c',
      'border-color': '#ffedd5',
      'border-width': 3.0,
      'color': '#ffffff',
    } as any,
  },
  // Phone / Device → Rhomboid Node (Solid Teal)
  {
    selector: 'node[nodeType = "PhoneNumber"], node[nodeType = "Device"]',
    style: {
      'shape': 'rhomboid',
      'width': 44,
      'height': 36,
      'background-color': '#0d9488',
      'border-color': '#99f6e4',
      'border-width': 3.0,
      'color': '#ffffff',
    } as any,
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 4,
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
  // Vehicle / Operation Edges (Crimson Red Solid)
  {
    selector: 'edge[category = "VEHICLE"]',
    style: {
      'line-color': '#ef4444',
      'target-arrow-color': '#ef4444',
      'line-style': 'solid',
      'width': 2.2,
    } as any,
  },
  // Spatial / Location Edges (Emerald Green Solid with Vee arrow)
  {
    selector: 'edge[category = "LOCATION"]',
    style: {
      'line-color': '#10b981',
      'target-arrow-color': '#10b981',
      'target-arrow-shape': 'vee',
      'line-style': 'solid',
      'width': 2.2,
    } as any,
  },
  // Case Association Edges (Amber Gold Solid)
  {
    selector: 'edge[category = "CASE"]',
    style: {
      'line-color': '#f59e0b',
      'target-arrow-color': '#f59e0b',
      'target-arrow-shape': 'triangle',
      'line-style': 'solid',
      'width': 2.5,
    } as any,
  },
  // Evidence Edges (Sky Blue Dotted with Diamond arrow)
  {
    selector: 'edge[category = "EVIDENCE"]',
    style: {
      'line-color': '#38bdf8',
      'target-arrow-color': '#38bdf8',
      'target-arrow-shape': 'diamond',
      'line-style': 'dotted',
      'width': 2.2,
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
      'width': 3.5,
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
  {
    selector: 'node.focus-anchor',
    style: {
      'border-width': 5,
      'border-color': '#00F0FF',
      'background-color': '#0c2a47',
      'width': 44,
      'height': 44,
      'font-size': 11,
      'font-weight': '800',
      'z-index': 99999,
      'color': '#00F0FF',
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
  isFocusMode,
  focusNodeId,
  focusHopDepth = 1,
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
  // Update Cytoscape Elements (Differential update without re-creating instance)
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    const cyElements: ElementDefinition[] = [];

    // 1. Build undirected adjacency map for graph connectivity traversal
    const adjMap = new Map<string, Set<string>>();
    for (const rel of relationships) {
      if (!adjMap.has(rel.start_node)) adjMap.set(rel.start_node, new Set());
      if (!adjMap.has(rel.end_node)) adjMap.set(rel.end_node, new Set());
      adjMap.get(rel.start_node)!.add(rel.end_node);
      adjMap.get(rel.end_node)!.add(rel.start_node);
    }

    // 2. Identify Case root anchor node(s)
    const caseNodeIds = nodes
      .filter((n) => getPrimaryLabel(n.labels) === 'Case')
      .map((n) => n.id);

    let connectedNodeIds = new Set<string>();

    if (caseNodeIds.length > 0) {
      // Run BFS starting from Case root nodes to find all connected entities in main network
      const queue = [...caseNodeIds];
      caseNodeIds.forEach((id) => connectedNodeIds.add(id));

      while (queue.length > 0) {
        const curr = queue.shift()!;
        const neighbors = adjMap.get(curr);
        if (neighbors) {
          for (const neighbor of neighbors) {
            if (!connectedNodeIds.has(neighbor)) {
              connectedNodeIds.add(neighbor);
              queue.push(neighbor);
            }
          }
        }
      }
    } else {
      // Fallback: If no Case node is present, retain the largest connected component
      const visited = new Set<string>();
      let largestComponent = new Set<string>();

      for (const node of nodes) {
        if (!visited.has(node.id)) {
          const component = new Set<string>();
          const queue = [node.id];
          component.add(node.id);
          visited.add(node.id);

          while (queue.length > 0) {
            const curr = queue.shift()!;
            const neighbors = adjMap.get(curr);
            if (neighbors) {
              for (const neighbor of neighbors) {
                if (!visited.has(neighbor)) {
                  visited.add(neighbor);
                  component.add(neighbor);
                  queue.push(neighbor);
                }
              }
            }
          }

          if (component.size > largestComponent.size) {
            largestComponent = component;
          }
        }
      }
      connectedNodeIds = largestComponent;
    }

    // 3. Filter nodes: Exclude disconnected entities & isolated sub-graph clusters
    for (const node of nodes) {
      if (!connectedNodeIds.has(node.id)) {
        continue;
      }

      const primaryType = getPrimaryLabel(node.labels);
      const name = deriveNodeDisplayName(node);
      const style = NODE_TYPE_STYLES[primaryType] || DEFAULT_NODE_STYLE;
      const icon = getSymbolicIcon(primaryType);

      const label = `${icon}${name}`;

      cyElements.push({
        group: 'nodes',
        data: {
          id: node.id,
          label,
          name,
          nodeType: primaryType,
          shape: style.shape,
          bgColor: style.bg,
          borderColor: style.border,
          textColor: style.text,
          rawNode: node,
        },
      });
    }

    // 4. Add relationships with category styling for intuitive visual language
    const edgeSeen = new Set<string>();

    for (const rel of relationships) {
      if (connectedNodeIds.has(rel.start_node) && connectedNodeIds.has(rel.end_node)) {
        const propRole = rel.properties?.role || rel.properties?.role_name || rel.properties?.assertion_type || rel.properties?.relationship_type;
        const displayLabel = propRole ? String(propRole).replace(/_/g, ' ') : rel.type.replace(/_/g, ' ');

        // Deduplicate duplicate edges between identical node pairs sharing the same label
        const edgeKey = [rel.start_node, rel.end_node, displayLabel].sort().join('::');
        if (edgeSeen.has(edgeKey)) continue;
        edgeSeen.add(edgeKey);

        const typeStr = (rel.type + ' ' + (propRole || '')).toUpperCase();
        let category = 'CASE';
        if (typeStr.includes('VEHICLE') || typeStr.includes('OPERATED') || typeStr.includes('REGISTERED') || typeStr.includes('DRIVEN') || typeStr.includes('OWNER')) {
          category = 'VEHICLE';
        } else if (typeStr.includes('LOCATION') || typeStr.includes('SEEN') || typeStr.includes('CAPTURED') || typeStr.includes('TRANSIT') || typeStr.includes('LOCATED')) {
          category = 'LOCATION';
        } else if (typeStr.includes('CASE') || typeStr.includes('SUBJECT') || typeStr.includes('SUSPECT') || typeStr.includes('MEMBER') || typeStr.includes('ASSOCIATED') || typeStr.includes('ROLE') || typeStr.includes('COMMUNICATED')) {
          category = 'CASE';
        } else if (typeStr.includes('EVIDENCE') || typeStr.includes('ATTACHED') || typeStr.includes('CORROBORATE') || typeStr.includes('FIR') || typeStr.includes('LEAD')) {
          category = 'EVIDENCE';
        }

        cyElements.push({
          group: 'edges',
          data: {
            id: rel.id,
            source: rel.start_node,
            target: rel.end_node,
            label: displayLabel,
            category,
            proposalStatus: rel.properties?.proposal_status || 'CONFIRMED',
            rawRel: rel,
          },
        });
      }
    }

    cy.batch(() => {
      cy.elements().remove();
      cy.add(cyElements);
    });

    // Detect multi-case graph status
    const caseCount = cy.nodes('[nodeType = "Case"]').length;
    const hasMultipleCases = caseCount >= 2;

    // Run COSE layout inside setTimeout so the browser UI thread is never blocked
    setTimeout(() => {
      if (!cyRef.current) return;
      const layout = cy.elements().layout({
        name: 'cose',
        animate: false,
        randomize: false,
        componentSpacing: hasMultipleCases ? 320 : 220,
        nodeRepulsion: (node: any) => {
          const type = node.data('nodeType');
          if (type === 'Case') return hasMultipleCases ? 50000 : 35000;
          if (type === 'Lead') return 28000;
          return 22000;
        },
        idealEdgeLength: (edge: any) => {
          const srcType = edge.source().data('nodeType');
          const tgtType = edge.target().data('nodeType');
          if (srcType === 'Case' || tgtType === 'Case') {
            return hasMultipleCases ? 320 : 240;
          }
          return 190;
        },
        gravity: 0.025, // Low gravity prevents central clumping and allows horizontal expansion
        edgeElasticity: (edge: any) => {
          const srcType = edge.source().data('nodeType');
          const tgtType = edge.target().data('nodeType');
          if (srcType === 'Case' || tgtType === 'Case') return 15;
          return 60;
        },
        numIter: 200,
      });

      layout.on('layoutstop', () => {
        if (!cyRef.current) return;

        // Horizontal Stretcher: Expand node X positions across wide horizontal space
        const visibleNodes = cy.nodes(':visible');
        if (visibleNodes.length > 1) {
          let minX = Infinity, maxX = -Infinity;
          visibleNodes.forEach((n) => {
            const x = n.position('x');
            if (x < minX) minX = x;
            if (x > maxX) maxX = x;
          });

          const spanX = maxX - minX;
          if (spanX > 0) {
            const centerX = (minX + maxX) / 2;
            const stretchFactor = 2.2; // Stretch network horizontally across full canvas width
            cy.batch(() => {
              visibleNodes.forEach((n) => {
                const currentX = n.position('x');
                n.position('x', centerX + (currentX - centerX) * stretchFactor);
              });
            });
          }
        }

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
        if (visibleElements.length > 0) {
          cy.fit(visibleElements, 45);
        }
      });

      layout.run();
    }, 0);
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

  // ── SIGNATURE CIVIX REAL FOCUS MODE: HIDE EVERYTHING EXCEPT FOCUS NODE & N-HOP NETWORK ──
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    if (isFocusMode && focusNodeId) {
      const hop = focusHopDepth || 1;

      // Calculate N-hop neighborhood set from focusNodeId
      const focusNetworkNodes = new Set<string>([focusNodeId]);
      let currentFrontier = new Set<string>([focusNodeId]);

      for (let h = 0; h < hop; h++) {
        const nextFrontier = new Set<string>();
        for (const rel of relationships) {
          if (currentFrontier.has(rel.start_node) && !focusNetworkNodes.has(rel.end_node)) {
            nextFrontier.add(rel.end_node);
            focusNetworkNodes.add(rel.end_node);
          }
          if (currentFrontier.has(rel.end_node) && !focusNetworkNodes.has(rel.start_node)) {
            nextFrontier.add(rel.start_node);
            focusNetworkNodes.add(rel.start_node);
          }
        }
        currentFrontier = nextFrontier;
      }

      // Hide all nodes and edges outside focusNetworkNodes
      cy.batch(() => {
        cy.nodes().forEach((nodeEle) => {
          if (focusNetworkNodes.has(nodeEle.id())) {
            nodeEle.style('display', 'element');
            if (nodeEle.id() === focusNodeId) {
              nodeEle.addClass('focus-anchor');
            } else {
              nodeEle.removeClass('focus-anchor');
            }
          } else {
            nodeEle.style('display', 'none');
          }
        });

        cy.edges().forEach((edgeEle) => {
          const rawRel = edgeEle.data('rawRel');
          if (rawRel && focusNetworkNodes.has(rawRel.start_node) && focusNetworkNodes.has(rawRel.end_node)) {
            edgeEle.style('display', 'element');
          } else {
            edgeEle.style('display', 'none');
          }
        });
      });

      // Animate focused layout
      setTimeout(() => {
        if (!cyRef.current) return;
        const visibleEles = cy.elements(':visible');
        if (visibleEles.length > 0) {
          const focusLayout = visibleEles.layout({
            name: 'cose',
            animate: true,
            animationDuration: 400,
            componentSpacing: 220,
            nodeRepulsion: () => 32000,
            idealEdgeLength: () => 220,
            gravity: 0.04,
          });
          focusLayout.run();
          cy.fit(visibleEles, 60);
        }
      }, 0);
    } else {
      // Remove focus anchor styling when exiting focus mode
      cy.batch(() => {
        cy.nodes().removeClass('focus-anchor');
      });
    }
  }, [isFocusMode, focusNodeId, focusHopDepth, relationships]);

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
      componentSpacing: hasMultipleCases ? 320 : 220,
      nodeRepulsion: (node: any) => {
        const type = node.data('nodeType');
        if (type === 'Case') return hasMultipleCases ? 50000 : 35000;
        if (type === 'Lead') return 28000;
        return 22000;
      },
      idealEdgeLength: (edge: any) => {
        const srcType = edge.source().data('nodeType');
        const tgtType = edge.target().data('nodeType');
        if (srcType === 'Case' || tgtType === 'Case') {
          return hasMultipleCases ? 320 : 240;
        }
        return 190;
      },
      gravity: 0.025,
      numIter: 300,
    });

    layout.on('layoutstop', () => {
      if (!cyRef.current) return;
      const visibleNodes = cy.nodes(':visible');
      if (visibleNodes.length > 1) {
        let minX = Infinity, maxX = -Infinity;
        visibleNodes.forEach((n) => {
          const x = n.position('x');
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
        });

        const spanX = maxX - minX;
        if (spanX > 0) {
          const centerX = (minX + maxX) / 2;
          const stretchFactor = 2.2;
          cy.batch(() => {
            visibleNodes.forEach((n) => {
              const currentX = n.position('x');
              n.position('x', centerX + (currentX - centerX) * stretchFactor);
            });
          });
        }
      }
      cy.resize();
      const visibleElements = cy.elements(':visible');
      if (visibleElements.length > 0) {
        cy.fit(visibleElements, 45);
      }
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
