import React from 'react';
import { Route, ArrowRight, X, Eye, EyeOff, MousePointerClick, CheckCircle2, AlertCircle, RefreshCw, RotateCcw } from 'lucide-react';
import type { GraphNode, GraphRelationship } from '../../types/api';

interface PathAnalysisPanelProps {
  sourceNode: GraphNode | null;
  targetNode: GraphNode | null;
  pathNodes: GraphNode[];
  pathRelationships: GraphRelationship[];
  isSearching: boolean;
  isPathFiltered: boolean;
  allNodes: GraphNode[];
  onSetSourceNode: (node: GraphNode | null) => void;
  onSetTargetNode: (node: GraphNode | null) => void;
  onToggleShowPath: () => void;
  onClearPath: () => void;
  onSelectNode: (node: GraphNode) => void;
}

function deriveDisplayName(node: GraphNode | null): string {
  if (!node) return '';
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
  return String(raw).replace(/_[0-9a-f]{8}$/i, '');
}

export const PathAnalysisPanel: React.FC<PathAnalysisPanelProps> = ({
  sourceNode,
  targetNode,
  pathNodes,
  pathRelationships,
  isPathFiltered,
  allNodes,
  onSetSourceNode,
  onSetTargetNode,
  onToggleShowPath,
  onClearPath,
  onSelectNode,
}) => {
  const sourceName = deriveDisplayName(sourceNode);
  const targetName = deriveDisplayName(targetNode);
  const pathFound = pathNodes.length > 0;
  const hopCount = Math.max(0, pathNodes.length - 1);

  // Step state
  const currentStep = !sourceNode ? 1 : !targetNode ? 2 : 3;

  return (
    <div className="absolute top-14 left-1/2 -translate-x-1/2 z-40 bg-civix-surface/95 border border-civix-blue/60 rounded-md p-4 shadow-civix-lg backdrop-blur-md text-civix-text-primary max-w-2xl w-full select-none font-mono text-xs antialiased">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-civix-border pb-2 mb-3">
        <div className="flex items-center space-x-2">
          <Route className="w-4 h-4 text-civix-blue-light animate-pulse" />
          <h3 className="text-xs font-bold text-civix-text-primary uppercase tracking-wider">
            PATH ANALYSIS — NETWORK TOPOLOGY DISCOVERY
          </h3>
        </div>
        <button
          onClick={onClearPath}
          className="p-1 text-civix-text-muted hover:text-white rounded hover:bg-civix-surface-3 transition-colors"
          title="Exit Path Analysis"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* ── Step Guidance Banners ────────────────────────────────────────── */}
      {currentStep === 1 && (
        <div className="flex items-center space-x-2 bg-civix-blue-subtle/40 border border-civix-blue/50 p-2.5 rounded-sm mb-3">
          <MousePointerClick className="w-4 h-4 text-civix-blue-light flex-shrink-0 animate-bounce" />
          <div className="text-xs text-civix-blue-light font-bold">
            STEP 1 OF 2: Click the FIRST entity on the graph canvas to set as SOURCE node.
          </div>
        </div>
      )}

      {currentStep === 2 && (
        <div className="flex items-center space-x-2 bg-civix-gold-subtle/40 border border-civix-gold/50 p-2.5 rounded-sm mb-3">
          <MousePointerClick className="w-4 h-4 text-civix-gold flex-shrink-0 animate-bounce" />
          <div className="text-xs text-civix-gold font-bold">
            STEP 2 OF 2: Click the SECOND entity on the graph canvas to set as TARGET node.
          </div>
        </div>
      )}

      {/* ── Source / Target Selection Grid ────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
        {/* Source Box */}
        <div className={`p-2.5 rounded-sm border transition-all ${
          sourceNode 
            ? 'bg-civix-surface-2 border-civix-blue-light/60' 
            : 'bg-civix-bg border-civix-border border-dashed'
        }`}>
          <div className="flex items-center justify-between text-[10px] font-bold text-civix-text-muted uppercase tracking-widest mb-1">
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-civix-blue-light inline-block"></span>
              <span>1. SOURCE ENTITY</span>
            </span>
            {sourceNode && (
              <button
                onClick={() => onSetSourceNode(null)}
                className="text-civix-text-muted hover:text-civix-red transition-colors text-[9px]"
              >
                Change
              </button>
            )}
          </div>
          {sourceNode ? (
            <div className="text-xs font-bold text-civix-text-primary truncate">
              {sourceName}
            </div>
          ) : (
            <div className="text-xs text-civix-text-muted italic flex items-center space-x-1">
              <span>Click graph node to select...</span>
            </div>
          )}
        </div>

        {/* Target Box */}
        <div className={`p-2.5 rounded-sm border transition-all ${
          targetNode 
            ? 'bg-civix-surface-2 border-civix-gold/60' 
            : 'bg-civix-bg border-civix-border border-dashed'
        }`}>
          <div className="flex items-center justify-between text-[10px] font-bold text-civix-text-muted uppercase tracking-widest mb-1">
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-civix-gold inline-block"></span>
              <span>2. TARGET ENTITY</span>
            </span>
            {targetNode && (
              <button
                onClick={() => onSetTargetNode(null)}
                className="text-civix-text-muted hover:text-civix-red transition-colors text-[9px]"
              >
                Change
              </button>
            )}
          </div>
          {targetNode ? (
            <div className="text-xs font-bold text-civix-text-primary truncate">
              {targetName}
            </div>
          ) : (
            <div className="text-xs text-civix-text-muted italic flex items-center space-x-1">
              <span>Click graph node to select...</span>
            </div>
          )}
        </div>
      </div>

      {/* Dropdown selectors for quick fallback */}
      <div className="grid grid-cols-2 gap-2 mb-3 text-[11px]">
        <select
          value={sourceNode?.id || ''}
          onChange={(e) => {
            const found = allNodes.find(n => n.id === e.target.value);
            onSetSourceNode(found || null);
          }}
          className="bg-civix-bg border border-civix-border rounded-sm px-2 py-1 text-civix-text-primary focus:outline-none focus:border-civix-blue"
        >
          <option value="">Select Source Node from list...</option>
          {allNodes.map(n => (
            <option key={n.id} value={n.id}>{deriveDisplayName(n)}</option>
          ))}
        </select>

        <select
          value={targetNode?.id || ''}
          onChange={(e) => {
            const found = allNodes.find(n => n.id === e.target.value);
            onSetTargetNode(found || null);
          }}
          className="bg-civix-bg border border-civix-border rounded-sm px-2 py-1 text-civix-text-primary focus:outline-none focus:border-civix-blue"
        >
          <option value="">Select Target Node from list...</option>
          {allNodes.map(n => (
            <option key={n.id} value={n.id}>{deriveDisplayName(n)}</option>
          ))}
        </select>
      </div>

      {/* ── Path Results & Show Path Action ────────────────────────────────── */}
      {sourceNode && targetNode && (
        <div className="space-y-3 pt-2 border-t border-civix-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {pathFound ? (
                <span className="flex items-center space-x-1 bg-civix-green-subtle/50 text-civix-green border border-civix-green/30 px-2 py-1 rounded-xs text-[10px] font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>PATH FOUND — {hopCount} {hopCount === 1 ? 'HOP' : 'HOPS'} IN GRAPH</span>
                </span>
              ) : (
                <span className="flex items-center space-x-1 bg-civix-red-subtle/50 text-civix-red border border-civix-red/30 px-2 py-1 rounded-xs text-[10px] font-bold">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>NO DIRECT PATH IN LOADED TOPOLOGY</span>
                </span>
              )}
            </div>

            {/* Main Action Button: SHOW PATH (HIDE DISCONNECTED NODES) */}
            {pathFound && (
              <button
                onClick={onToggleShowPath}
                className={`px-3 py-1.5 rounded-sm font-bold text-xs flex items-center space-x-1.5 transition-all shadow-md ${
                  isPathFiltered
                    ? 'bg-civix-gold text-civix-bg hover:bg-civix-gold/90'
                    : 'bg-civix-blue-light text-civix-bg hover:bg-civix-blue-light/90'
                }`}
              >
                {isPathFiltered ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>SHOW ALL NODES (RESET)</span>
                  </>
                ) : (
                  <>
                    <Eye className="w-3.5 h-3.5" />
                    <span>SHOW PATH (HIDE DISCONNECTED NODES)</span>
                  </>
                )}
              </button>
            )}
          </div>

          {/* Path Sequence Flow */}
          {pathFound && (
            <div className="bg-civix-bg border border-civix-border p-2.5 rounded-sm">
              <div className="text-[10px] font-bold text-civix-text-muted uppercase tracking-widest mb-1.5">
                ORDERED PATH SEQUENCE ({pathNodes.length} NODES):
              </div>
              <div className="flex items-center gap-1.5 overflow-x-auto py-1">
                {pathNodes.map((node, index) => {
                  const rel = pathRelationships[index];
                  const name = deriveDisplayName(node);

                  return (
                    <React.Fragment key={node.id}>
                      <button
                        onClick={() => onSelectNode(node)}
                        className="px-2.5 py-1 rounded bg-civix-surface-2 border border-civix-blue/60 text-xs font-semibold text-civix-text-primary hover:bg-civix-surface-3 transition-colors shrink-0 font-mono"
                      >
                        {name}
                      </button>

                      {rel && (
                        <div className="flex flex-col items-center shrink-0 px-1">
                          <span className="text-[8px] font-mono font-bold text-civix-blue-light uppercase tracking-wide">
                            {rel.type.replace(/_/g, ' ')}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5 text-civix-blue-light" />
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
