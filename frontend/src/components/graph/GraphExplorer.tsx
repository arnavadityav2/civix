import React, { useState, useMemo, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  Route, 
  RotateCcw, 
  User, 
  Building2, 
  Smartphone, 
  Phone, 
  Car, 
  CreditCard, 
  MapPin, 
  FileText, 
  Briefcase, 
  Shield,
  MousePointerClick,
  CheckCircle2,
  AlertCircle,
  Eye,
  RefreshCw,
  ArrowRight,
  X
} from 'lucide-react';
import type { GraphNode, GraphRelationship } from '../../types/api';

export type ExplorerTab = 'SEARCH' | 'FILTERS' | 'PATH';

interface GraphExplorerProps {
  nodes: GraphNode[];
  relationships: GraphRelationship[];
  selectedNodeId?: string | null;
  onSelectNode: (node: GraphNode) => void;
  hiddenEntityTypes: Set<string>;
  onToggleEntityType: (type: string) => void;
  hiddenRelTypes: Set<string>;
  onToggleRelType: (type: string) => void;
  onResetFilters: () => void;

  // Path Analysis Props
  activeTabProp?: ExplorerTab;
  onTabChangeProp?: (tab: ExplorerTab) => void;
  pathSourceNode?: GraphNode | null;
  pathTargetNode?: GraphNode | null;
  pathNodes?: GraphNode[];
  pathRelationships?: GraphRelationship[];
  isPathFiltered?: boolean;
  onSetSourceNode?: (node: GraphNode | null) => void;
  onSetTargetNode?: (node: GraphNode | null) => void;
  onToggleShowPath?: () => void;
  onClearPath?: () => void;
}

const TYPE_ICONS: Record<string, React.ElementType> = {
  Person: User,
  Organization: Building2,
  Device: Smartphone,
  PhoneNumber: Phone,
  Vehicle: Car,
  FinancialAccount: CreditCard,
  Location: MapPin,
  Evidence: FileText,
  Case: Briefcase,
  Lead: Shield,
};

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
  const cleaned = String(raw).replace(/_[0-9a-f]{8}$/i, '');
  return cleaned.length > 24 ? `${cleaned.slice(0, 22)}…` : cleaned;
}

export const GraphExplorer: React.FC<GraphExplorerProps> = ({
  nodes,
  relationships,
  selectedNodeId,
  onSelectNode,
  hiddenEntityTypes,
  onToggleEntityType,
  hiddenRelTypes,
  onToggleRelType,
  onResetFilters,
  activeTabProp,
  onTabChangeProp,
  pathSourceNode,
  pathTargetNode,
  pathNodes = [],
  pathRelationships = [],
  isPathFiltered = false,
  onSetSourceNode,
  onSetTargetNode,
  onToggleShowPath,
  onClearPath,
}) => {
  const [internalTab, setInternalTab] = useState<ExplorerTab>('SEARCH');
  const [searchQuery, setSearchQuery] = useState('');

  const activeTab = activeTabProp !== undefined ? activeTabProp : internalTab;

  const handleTabClick = (tab: ExplorerTab) => {
    if (onTabChangeProp) {
      onTabChangeProp(tab);
    } else {
      setInternalTab(tab);
    }
  };

  // Dynamic Entity Type Counts
  const entityTypeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const node of nodes) {
      const type = getPrimaryLabel(node.labels);
      counts[type] = (counts[type] || 0) + 1;
    }
    return counts;
  }, [nodes]);

  // Dynamic Relationship Type Counts
  const relTypeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const rel of relationships) {
      const type = rel.type || 'RELATIONSHIP';
      counts[type] = (counts[type] || 0) + 1;
    }
    return counts;
  }, [relationships]);

  // Search Filtering
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return nodes;
    const query = searchQuery.toLowerCase().trim();
    return nodes.filter((node) => {
      const name = deriveDisplayName(node).toLowerCase();
      const id = node.id.toLowerCase();
      const type = getPrimaryLabel(node.labels).toLowerCase();
      const propsStr = JSON.stringify(node.properties || {}).toLowerCase();
      return name.includes(query) || id.includes(query) || type.includes(query) || propsStr.includes(query);
    });
  }, [nodes, searchQuery]);

  // Path Analysis calculations
  const sourceName = deriveDisplayName(pathSourceNode || null);
  const targetName = deriveDisplayName(pathTargetNode || null);
  const pathFound = pathNodes.length > 0;
  const hopCount = Math.max(0, pathNodes.length - 1);

  return (
    <div className="flex flex-col h-full bg-[#0d1322] border-r border-[#1e2d4a] text-slate-200 select-none antialiased">
      {/* ── Explorer Header & Tabs ── */}
      <div className="p-3 border-b border-[#162035] bg-[#0b0f19]">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-xs font-bold font-mono text-white uppercase tracking-wider">
            GRAPH EXPLORER
          </h2>
          <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-1.5 py-0.5 rounded">
            {nodes.length} NODES
          </span>
        </div>

        {/* Tab Buttons: Search | Filters | Path */}
        <div className="flex items-center bg-[#131b2e] border border-[#1e2d4a] p-0.5 rounded">
          <button
            onClick={() => handleTabClick('SEARCH')}
            className={`flex-1 flex items-center justify-center gap-1 py-1 rounded text-[11px] font-semibold transition-colors ${
              activeTab === 'SEARCH'
                ? 'bg-cyan-950/80 border border-cyan-500/60 text-cyan-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Search className="w-3 h-3" />
            <span>Search</span>
          </button>
          <button
            onClick={() => handleTabClick('FILTERS')}
            className={`flex-1 flex items-center justify-center gap-1 py-1 rounded text-[11px] font-semibold transition-colors ${
              activeTab === 'FILTERS'
                ? 'bg-cyan-950/80 border border-cyan-500/60 text-cyan-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Filter className="w-3 h-3" />
            <span>Filters</span>
          </button>
          <button
            onClick={() => handleTabClick('PATH')}
            className={`flex-1 flex items-center justify-center gap-1 py-1 rounded text-[11px] font-semibold transition-colors ${
              activeTab === 'PATH'
                ? 'bg-cyan-950/80 border border-cyan-500/60 text-cyan-400 font-bold'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Route className="w-3 h-3 text-cyan-400" />
            <span>Path</span>
          </button>
        </div>
      </div>

      {/* ── Tab Content ── */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4 font-mono">
        {/* TAB 1: SEARCH */}
        {activeTab === 'SEARCH' && (
          <div className="space-y-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search entities, case numbers..."
                className="w-full bg-[#131b2e] border border-[#1e2d4a] rounded pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 font-mono"
              />
            </div>

            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 px-1">
              <span>MATCHES: {searchResults.length}</span>
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="text-cyan-400 hover:underline"
                >
                  Clear search
                </button>
              )}
            </div>

            <div className="space-y-1 max-h-[calc(100vh-250px)] overflow-y-auto pr-1">
              {searchResults.map((node) => {
                const primaryType = getPrimaryLabel(node.labels);
                const name = deriveDisplayName(node);
                const Icon = TYPE_ICONS[primaryType] || User;
                const isSelected = selectedNodeId === node.id;

                return (
                  <button
                    key={node.id}
                    onClick={() => onSelectNode(node)}
                    className={`w-full flex items-center justify-between p-2 rounded text-left border transition-colors ${
                      isSelected
                        ? 'bg-cyan-950/80 border-cyan-500 text-white'
                        : 'bg-[#131b2e]/60 border-[#1e2d4a] hover:bg-[#131b2e] hover:border-slate-600 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="w-6 h-6 rounded bg-[#0b0f19] border border-[#1e2d4a] flex items-center justify-center shrink-0">
                        <Icon className="w-3 h-3 text-cyan-400" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-slate-200 truncate leading-tight">
                          {name}
                        </p>
                        <p className="text-[9px] font-mono text-slate-400 uppercase leading-none mt-0.5">
                          {primaryType}
                        </p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 2: FILTERS */}
        {activeTab === 'FILTERS' && (
          <div className="space-y-4">
            <div>
              <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
                Entity Types
              </h3>
              <div className="space-y-1">
                {Object.entries(entityTypeCounts).map(([type, count]) => {
                  const Icon = TYPE_ICONS[type] || User;
                  const isHidden = hiddenEntityTypes.has(type);

                  return (
                    <label
                      key={type}
                      className="flex items-center justify-between p-1.5 rounded bg-[#131b2e]/50 border border-[#1e2d4a] cursor-pointer hover:bg-[#131b2e]"
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={!isHidden}
                          onChange={() => onToggleEntityType(type)}
                          className="rounded border-[#1e2d4a] bg-[#0b0f19] text-cyan-500 focus:ring-0"
                        />
                        <Icon className="w-3.5 h-3.5 text-cyan-400" />
                        <span className="text-xs font-medium text-slate-300">{type}</span>
                      </div>
                      <span className="text-[10px] font-mono font-bold text-slate-400 bg-[#0b0f19] px-1.5 py-0.5 rounded border border-[#1e2d4a]">
                        {count}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>

            <div>
              <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
                Relationship Types
              </h3>
              <div className="space-y-1 max-h-48 overflow-y-auto">
                {Object.entries(relTypeCounts).map(([type, count]) => {
                  const isHidden = hiddenRelTypes.has(type);

                  return (
                    <label
                      key={type}
                      className="flex items-center justify-between p-1.5 rounded bg-[#131b2e]/50 border border-[#1e2d4a] cursor-pointer hover:bg-[#131b2e]"
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={!isHidden}
                          onChange={() => onToggleRelType(type)}
                          className="rounded border-[#1e2d4a] bg-[#0b0f19] text-cyan-500 focus:ring-0"
                        />
                        <span className="text-xs font-mono font-semibold text-slate-300">
                          {type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <span className="text-[10px] font-mono font-bold text-slate-400 bg-[#0b0f19] px-1.5 py-0.5 rounded border border-[#1e2d4a]">
                        {count}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>

            <button
              onClick={onResetFilters}
              className="w-full flex items-center justify-center gap-1.5 py-1.5 bg-[#131b2e] border border-[#1e2d4a] hover:border-slate-500 text-slate-300 text-xs font-semibold rounded transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
              <span>RESET FILTERS</span>
            </button>
          </div>
        )}

        {/* TAB 3: PATH (PATH ANALYSIS IN SIDEBAR PANEL) */}
        {activeTab === 'PATH' && (
          <div className="space-y-3">
            {/* Header / Title */}
            <div className="flex items-center justify-between border-b border-[#1e2d4a] pb-2">
              <div className="flex items-center gap-1.5">
                <Route className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  PATH ANALYSIS
                </h3>
              </div>
              {onClearPath && (
                <button
                  onClick={onClearPath}
                  className="text-[10px] text-slate-400 hover:text-rose-400 flex items-center gap-1"
                  title="Clear path analysis"
                >
                  <X className="w-3 h-3" />
                  <span>Reset</span>
                </button>
              )}
            </div>

            {/* Step Banners */}
            {!pathSourceNode && (
              <div className="p-2.5 rounded bg-cyan-950/40 border border-cyan-500/50 text-cyan-300 text-xs font-bold flex items-center gap-2">
                <MousePointerClick className="w-4 h-4 text-cyan-400 shrink-0 animate-bounce" />
                <span>STEP 1: Click 1st entity on graph canvas (SOURCE)</span>
              </div>
            )}

            {pathSourceNode && !pathTargetNode && (
              <div className="p-2.5 rounded bg-amber-950/40 border border-amber-500/50 text-amber-300 text-xs font-bold flex items-center gap-2">
                <MousePointerClick className="w-4 h-4 text-amber-400 shrink-0 animate-bounce" />
                <span>STEP 2: Click 2nd entity on graph canvas (TARGET)</span>
              </div>
            )}

            {/* 1. Source Entity Card */}
            <div className={`p-2.5 rounded border transition-all ${
              pathSourceNode ? 'bg-[#131b2e] border-cyan-500/60' : 'bg-[#0b0f19] border-[#1e2d4a] border-dashed'
            }`}>
              <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block"></span>
                  <span>SOURCE ENTITY</span>
                </span>
                {pathSourceNode && onSetSourceNode && (
                  <button
                    onClick={() => onSetSourceNode(null)}
                    className="text-slate-400 hover:text-rose-400 text-[9px]"
                  >
                    Clear
                  </button>
                )}
              </div>
              {pathSourceNode ? (
                <p className="text-xs font-bold text-white truncate">{sourceName}</p>
              ) : (
                <p className="text-[11px] text-slate-500 italic">Click graph node or select below...</p>
              )}
              {onSetSourceNode && (
                <select
                  value={pathSourceNode?.id || ''}
                  onChange={(e) => {
                    const found = nodes.find(n => n.id === e.target.value);
                    onSetSourceNode(found || null);
                  }}
                  className="w-full mt-1.5 bg-[#0b0f19] border border-[#1e2d4a] rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-cyan-500"
                >
                  <option value="">Choose Source entity...</option>
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>{deriveDisplayName(n)}</option>
                  ))}
                </select>
              )}
            </div>

            {/* 2. Target Entity Card */}
            <div className={`p-2.5 rounded border transition-all ${
              pathTargetNode ? 'bg-[#131b2e] border-amber-500/60' : 'bg-[#0b0f19] border-[#1e2d4a] border-dashed'
            }`}>
              <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-amber-400 inline-block"></span>
                  <span>TARGET ENTITY</span>
                </span>
                {pathTargetNode && onSetTargetNode && (
                  <button
                    onClick={() => onSetTargetNode(null)}
                    className="text-slate-400 hover:text-rose-400 text-[9px]"
                  >
                    Clear
                  </button>
                )}
              </div>
              {pathTargetNode ? (
                <p className="text-xs font-bold text-white truncate">{targetName}</p>
              ) : (
                <p className="text-[11px] text-slate-500 italic">Click graph node or select below...</p>
              )}
              {onSetTargetNode && (
                <select
                  value={pathTargetNode?.id || ''}
                  onChange={(e) => {
                    const found = nodes.find(n => n.id === e.target.value);
                    onSetTargetNode(found || null);
                  }}
                  className="w-full mt-1.5 bg-[#0b0f19] border border-[#1e2d4a] rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-cyan-500"
                >
                  <option value="">Choose Target entity...</option>
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>{deriveDisplayName(n)}</option>
                  ))}
                </select>
              )}
            </div>

            {/* 3. Path Status & Show Path Action Button */}
            {pathSourceNode && pathTargetNode && (
              <div className="space-y-2.5 pt-2 border-t border-[#1e2d4a]">
                <div className="flex items-center justify-between text-xs font-bold">
                  {pathFound ? (
                    <span className="flex items-center gap-1 text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded text-[10px]">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{hopCount} {hopCount === 1 ? 'HOP' : 'HOPS'} PATH FOUND</span>
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-rose-400 bg-rose-950/60 border border-rose-800/40 px-2 py-0.5 rounded text-[10px]">
                      <AlertCircle className="w-3.5 h-3.5" />
                      <span>NO DIRECT PATH FOUND</span>
                    </span>
                  )}
                </div>

                {pathFound && onToggleShowPath && (
                  <button
                    onClick={onToggleShowPath}
                    className={`w-full py-2 px-3 rounded font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-md ${
                      isPathFiltered
                        ? 'bg-amber-500 text-slate-950 hover:bg-amber-400'
                        : 'bg-cyan-500 text-slate-950 hover:bg-cyan-400'
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
                        <span>SHOW PATH (HIDE DISCONNECTED)</span>
                      </>
                    )}
                  </button>
                )}

                {/* Path Sequence Breakdown */}
                {pathFound && (
                  <div className="p-2 rounded bg-[#0b0f19] border border-[#1e2d4a] space-y-1.5">
                    <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                      PATH SEQUENCE ({pathNodes.length} NODES):
                    </div>
                    <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                      {pathNodes.map((node, idx) => {
                        const rel = pathRelationships[idx];
                        const name = deriveDisplayName(node);

                        return (
                          <div key={node.id} className="space-y-0.5">
                            <button
                              onClick={() => onSelectNode(node)}
                              className="w-full text-left p-1.5 rounded bg-[#131b2e] border border-cyan-500/40 hover:bg-cyan-950 text-xs font-bold text-white truncate"
                            >
                              {idx + 1}. {name}
                            </button>

                            {rel && (
                              <div className="flex items-center gap-1 px-3 text-[9px] font-mono text-cyan-400">
                                <ArrowRight className="w-3 h-3 text-cyan-500 shrink-0" />
                                <span className="uppercase tracking-wide truncate">
                                  {rel.type.replace(/_/g, ' ')}
                                </span>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
