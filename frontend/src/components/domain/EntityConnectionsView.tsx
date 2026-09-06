import React, { useEffect, useRef, useState } from 'react';
import cytoscape, { type Core, type ElementDefinition } from 'cytoscape';
import { EntityConnectionInspector } from './EntityConnectionInspector';

interface SimpleGraphRel {
  id: string;
  targetId: string;
  targetName: string;
  targetType: string;
  predicate: string;
  rawPredicate: string;
  epistemicStatus?: string;
  isCandidate?: boolean;
}

interface EntityConnectionsViewProps {
  entityId: string;
  entityName: string;
  entityType: string;
  relationships: SimpleGraphRel[];
  onBack: () => void;
}

// ── Institutional Node Color & Icon Configuration (NO PURPLE) ──
const NODE_TYPE_STYLES: Record<string, { bg: string; border: string }> = {
  Person: { bg: '#0f172a', border: '#3b82f6' },
  Organization: { bg: '#0f172a', border: '#d97706' },
  Device: { bg: '#0f172a', border: '#0284c7' },
  PhoneNumber: { bg: '#0f172a', border: '#10b981' },
  Vehicle: { bg: '#0f172a', border: '#ef4444' },
  FinancialAccount: { bg: '#0f172a', border: '#f59e0b' },
  Case: { bg: '#1e293b', border: '#64748b' },
  Event: { bg: '#1e293b', border: '#94a3b8' },
  Assertion: { bg: '#0f172a', border: '#475569' },
  SourceIdentity: { bg: '#0f172a', border: '#475569' },
  Evidence: { bg: '#1e293b', border: '#3b82f6' },
};

export const EntityConnectionsView: React.FC<EntityConnectionsViewProps> = ({
  entityId,
  entityName,
  entityType,
  relationships,
  onBack
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  
  const [selectedRel, setSelectedRel] = useState<any | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Build Elements
    const elements: ElementDefinition[] = [];

    // Central Node
    elements.push({
      data: {
        id: entityId,
        label: entityName,
        type: entityType,
        isCenter: true
      }
    });

    // Connected Nodes & Edges
    relationships.forEach(rel => {
      // Add target node
      if (!elements.find(e => e.data.id === rel.targetId)) {
        elements.push({
          data: {
            id: rel.targetId,
            label: rel.targetName,
            type: rel.targetType,
          }
        });
      }

      // Add edge
      elements.push({
        data: {
          id: rel.id,
          source: entityId,
          target: rel.targetId,
          label: rel.predicate,
          isCandidate: rel.isCandidate,
          rawPredicate: rel.rawPredicate,
          epistemicStatus: rel.epistemicStatus,
          targetName: rel.targetName
        }
      });
    });

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(label)',
            'color': '#f8fafc',
            'font-size': '10px',
            'font-family': 'monospace',
            'font-weight': 'bold',
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 6,
            'background-color': (ele) => {
              if (ele.data('isCenter')) return '#1e3a8a'; // Deep blue for center
              return NODE_TYPE_STYLES[ele.data('type')]?.bg || '#1e293b';
            },
            'border-width': (ele) => ele.data('isCenter') ? 3 : 2,
            'border-color': (ele) => {
              if (ele.data('isCenter')) return '#60a5fa'; // Bright blue border for center
              return NODE_TYPE_STYLES[ele.data('type')]?.border || '#64748b';
            },
            'width': (ele) => ele.data('isCenter') ? 48 : 36,
            'height': (ele) => ele.data('isCenter') ? 48 : 36,
            'text-wrap': 'wrap',
            'text-max-width': '120px'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': (ele) => ele.data('isCandidate') ? '#d97706' : '#475569', // Amber for ML lead
            'line-style': (ele) => ele.data('isCandidate') ? 'dashed' : 'solid',
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': (ele) => ele.data('isCandidate') ? '#d97706' : '#475569',
            'label': 'data(label)',
            'font-size': '8px',
            'font-family': 'monospace',
            'color': '#94a3b8',
            'text-rotation': 'autorotate',
            'text-margin-y': -8,
            'text-background-opacity': 1,
            'text-background-color': '#090C12',
            'text-background-padding': 2
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#60a5fa',
            'target-arrow-color': '#60a5fa',
            'width': 3
          }
        }
      ],
      layout: {
        name: 'concentric', // Focuses central node
        minNodeSpacing: 80,
        animate: true,
        animationDuration: 500
      },
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false
    });

    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      setSelectedRel({
        id: edge.id(),
        sourceName: entityName,
        targetName: edge.data('targetName'),
        predicate: edge.data('rawPredicate'),
        isModelGenerated: edge.data('isCandidate'),
        modelScore: edge.data('isCandidate') ? 87 : undefined, // In reality, map actual ML score
        status: edge.data('epistemicStatus') || (edge.data('isCandidate') ? 'UNRESOLVED' : 'AUTHORITATIVE'),
        explanation: edge.data('isCandidate') ? 'Candidate relationship surfaced from available investigative features.' : 'Direct associative link found in the intelligence workspace.',
      });
    });

    cy.on('tap', 'core', () => {
      setSelectedRel(null);
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [entityId, entityName, entityType, relationships]);

  return (
    <div className="absolute inset-0 bg-civix-surface z-50 flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-civix-border bg-civix-surface-2 flex-shrink-0 shadow-sm">
        <div className="flex items-center space-x-4">
          <button 
            onClick={onBack}
            className="text-xs font-mono font-bold text-civix-text-muted hover:text-white transition-colors"
          >
            ← BACK TO DOSSIER
          </button>
          <div className="h-4 w-px bg-civix-border" />
          <h2 className="text-sm font-bold text-white uppercase tracking-widest font-mono">
            ENTITY CONNECTIONS: {entityName}
          </h2>
        </div>
      </div>
      
      <div className="flex-1 relative flex overflow-hidden">
        <div className="flex-1 h-full relative" ref={containerRef} />
        
        {selectedRel && (
          <EntityConnectionInspector 
            relationship={selectedRel}
            onClose={() => setSelectedRel(null)}
          />
        )}
      </div>
    </div>
  );
};
