import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  X, 
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
  GitFork, 
  Focus, 
  ExternalLink, 
  AlertTriangle,
  Clock,
  Link2,
  Network
} from 'lucide-react';
import type { GraphNode, GraphRelationship } from '../../types/api';

interface EntityDossierProps {
  node: GraphNode | null;
  relationships: GraphRelationship[];
  allNodes: GraphNode[];
  caseData?: any;
  onClose: () => void;
  onSeeThread: (nodeId: string) => void;
  onFocusNode: (nodeId: string) => void;
  onSelectNode?: (node: GraphNode) => void;
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

function deriveDisplayName(node: GraphNode): string {
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

export const EntityDossier: React.FC<EntityDossierProps> = ({
  node,
  relationships,
  allNodes,
  caseData,
  onClose,
  onSeeThread,
  onFocusNode,
  onSelectNode,
}) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'RELATIONSHIPS' | 'CASES' | 'EVIDENCE' | 'TIMELINE'>('OVERVIEW');

  // Map nodes for fast lookup
  const nodeMap = useMemo(() => new Map(allNodes.map((n) => [n.id, n])), [allNodes]);

  if (!node) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center text-slate-500 font-mono text-xs select-none bg-[#0d1322] border-l border-[#1e2d4a]">
        <GitFork className="w-8 h-8 text-slate-600 mb-2 stroke-1" />
        <p className="font-bold text-slate-400 uppercase">NO ENTITY SELECTED</p>
        <p className="text-[11px] text-slate-500 mt-1 max-w-xs leading-relaxed">
          Click any entity node on the graph canvas to inspect its dossier, connections, evidence, and provenance.
        </p>
      </div>
    );
  }

  const p = node.properties || {};
  const primaryType = getPrimaryLabel(node.labels);
  const displayName = deriveDisplayName(node);
  const Icon = TYPE_ICONS[primaryType] || User;

  // Derive connected relationships for selected node
  const connectedEdges = relationships.filter(
    (r) => r.start_node === node.id || r.end_node === node.id
  );

  const keyConnections = connectedEdges.map((rel) => {
    const isSource = rel.start_node === node.id;
    const partnerId = isSource ? rel.end_node : rel.start_node;
    const partnerNode = nodeMap.get(partnerId);
    return {
      relId: rel.id,
      predicate: rel.type.replace(/_/g, ' '),
      partnerNode,
      partnerName: partnerNode ? deriveDisplayName(partnerNode) : partnerId,
      partnerType: partnerNode ? getPrimaryLabel(partnerNode.labels) : 'Entity',
      proposalStatus: rel.properties?.proposal_status || 'CONFIRMED',
    };
  });

  const hasHighConnectivity = connectedEdges.length >= 4;
  const isSuspectOrAccused = p.role === 'SUSPECT' || p.role === 'ACCUSED';

  return (
    <div className="flex flex-col h-full bg-[#0d1322] border-l border-[#1e2d4a] text-slate-200 select-none">
      {/* ── Header: Identity & Close ── */}
      <div className="p-3 border-b border-[#162035] bg-[#0b0f19] flex items-start justify-between">
        <div className="flex items-start gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded bg-[#131b2e] border border-cyan-500/50 flex items-center justify-center text-cyan-400 shrink-0 mt-0.5">
            <Icon className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider">
                {primaryType}
              </span>
              {p.role && (
                <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-amber-950/80 border border-amber-500/60 text-amber-400">
                  {p.role}
                </span>
              )}
            </div>
            <h2 className="text-sm font-bold text-white truncate leading-tight mt-0.5">
              {displayName}
            </h2>
            <p className="text-[10px] font-mono text-slate-500 truncate mt-0.5">
              ID: {node.id.length > 18 ? `${node.id.slice(0, 16)}…` : node.id}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-white rounded hover:bg-[#131b2e] transition-colors shrink-0"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* ── Primary Action Ribbon ── */}
      <div className="px-3 py-2 border-b border-[#162035] bg-[#090d16] flex items-center gap-2">
        <button
          onClick={() => onSeeThread(node.id)}
          className="flex-1 flex items-center justify-center gap-1.5 py-1 bg-cyan-950/80 border border-cyan-500/60 hover:bg-cyan-900/80 text-cyan-300 text-xs font-semibold rounded transition-colors"
        >
          <GitFork className="w-3.5 h-3.5" />
          <span>See Thread</span>
        </button>
        <button
          onClick={() => onFocusNode(node.id)}
          className="flex-1 flex items-center justify-center gap-1.5 py-1 bg-[#131b2e] border border-[#1e2d4a] hover:border-slate-500 text-slate-300 text-xs font-semibold rounded transition-colors"
        >
          <Focus className="w-3.5 h-3.5 text-cyan-400" />
          <span>Focus</span>
        </button>
      </div>

      {/* ── Dossier Navigation Tabs ── */}
      <div className="flex items-center px-2 bg-[#0b0f19] border-b border-[#162035] overflow-x-auto">
        {(['OVERVIEW', 'RELATIONSHIPS', 'CASES', 'EVIDENCE', 'TIMELINE'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 text-[11px] font-semibold border-b-2 transition-colors whitespace-nowrap ${
              activeTab === tab
                ? 'border-cyan-500 text-cyan-400 bg-[#0d1322]'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* ── Tab Content Panel ── */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4 font-sans">
        {activeTab === 'OVERVIEW' && (
          <div className="space-y-4">
            {/* Authoritative Role Indicator */}
            {isSuspectOrAccused && (
              <div className="p-2.5 rounded bg-rose-950/60 border border-rose-800/60 flex items-center gap-2 text-rose-300">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                <div className="text-xs">
                  <p className="font-bold leading-tight font-mono uppercase">Authoritative Role: {String(p.role)}</p>
                  <p className="text-[10px] text-rose-400/90 leading-tight">Entity registered as {String(p.role)} in case role assignment ledger.</p>
                </div>
              </div>
            )}

            {/* Truthful Structural Connectivity Indicator (Graph Degree) */}
            {hasHighConnectivity && (
              <div className="p-2.5 rounded bg-cyan-950/60 border border-cyan-800/60 flex items-center gap-2 text-cyan-300">
                <Network className="w-4 h-4 text-cyan-400 shrink-0" />
                <div className="text-xs">
                  <p className="font-bold leading-tight font-mono uppercase tracking-wide">Network Hub / High Connectivity</p>
                  <p className="text-[10px] text-cyan-400/90 leading-tight">Structural network metric: {connectedEdges.length} direct graph connections.</p>
                </div>
              </div>
            )}

            {/* ENTITY -> CURRENT CASE CONTEXT TREE */}
            <div>
              <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
                CASE CONTEXT & CONNECTIONS
              </h3>
              <div className="p-3 bg-[#131b2e]/60 border border-[#1e2d4a] rounded font-mono text-xs space-y-2">
                <div>
                  <span className="text-slate-500 text-[10px]">ENTITY</span>
                  <p className="text-white font-bold text-sm truncate">{displayName}</p>
                </div>
                <div className="pt-2 border-t border-[#162035] flex items-center justify-between">
                  <div>
                    <span className="text-slate-500 text-[10px]">CURRENT CASE</span>
                    <p className="text-cyan-400 font-bold">{caseData?.case_number || 'ACTIVE INVESTIGATION'}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-500 text-[10px]">ROLE</span>
                    <p className={`font-bold ${isSuspectOrAccused ? 'text-rose-400' : 'text-amber-400'}`}>
                      {p.role || 'ASSOCIATED ENTITY'}
                    </p>
                  </div>
                </div>

                {/* CASE CONNECTIONS TREE */}
                <div className="pt-2 border-t border-[#162035] space-y-1">
                  <span className="text-slate-500 text-[10px] uppercase">CASE CONNECTIONS</span>
                  {keyConnections.length === 0 ? (
                    <p className="text-slate-500 text-[11px] italic">No direct connections recorded.</p>
                  ) : (
                    <div className="pl-1 space-y-1 text-[11px] text-slate-300">
                      {keyConnections.map((conn, idx) => {
                        const isLast = idx === keyConnections.length - 1;
                        const prefix = isLast ? '└── ' : '├── ';
                        return (
                          <div
                            key={conn.relId}
                            onClick={() => conn.partnerNode && onSelectNode && onSelectNode(conn.partnerNode)}
                            className="flex items-center gap-1.5 hover:text-cyan-300 cursor-pointer py-0.5 rounded px-1 hover:bg-[#162035]/60 transition-colors"
                          >
                            <span className="text-slate-500 font-mono select-none">{prefix}</span>
                            <span className="font-semibold text-cyan-400 shrink-0">{conn.partnerType}:</span>
                            <span className="truncate">{conn.partnerName}</span>
                            <span className="text-[9px] text-slate-500 ml-auto font-mono shrink-0">({conn.predicate})</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Entity Attributes Table */}
            <div>
              <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
                VERIFIED ATTRIBUTES
              </h3>
              <div className="bg-[#131b2e]/60 border border-[#1e2d4a] rounded divide-y divide-[#1e2d4a] text-xs">
                <div className="p-2 flex items-center justify-between">
                  <span className="text-slate-400">Entity Type</span>
                  <span className="font-mono font-bold text-white">{primaryType}</span>
                </div>
                {p.registration_number && (
                  <div className="p-2 flex items-center justify-between">
                    <span className="text-slate-400">Registration</span>
                    <span className="font-mono text-cyan-400">{String(p.registration_number)}</span>
                  </div>
                )}
                {p.msisdn && (
                  <div className="p-2 flex items-center justify-between">
                    <span className="text-slate-400">Phone Number</span>
                    <span className="font-mono text-emerald-400">{String(p.msisdn)}</span>
                  </div>
                )}
                {p.imei && (
                  <div className="p-2 flex items-center justify-between">
                    <span className="text-slate-400">IMEI</span>
                    <span className="font-mono text-slate-200">{String(p.imei)}</span>
                  </div>
                )}
                {p.gender && (
                  <div className="p-2 flex items-center justify-between">
                    <span className="text-slate-400">Gender</span>
                    <span className="text-slate-200">{String(p.gender)}</span>
                  </div>
                )}
                {p.nationality && (
                  <div className="p-2 flex items-center justify-between">
                    <span className="text-slate-400">Nationality</span>
                    <span className="text-slate-200">{String(p.nationality)}</span>
                  </div>
                )}
                <div className="p-2 flex items-center justify-between">
                  <span className="text-slate-400">Direct Connections</span>
                  <span className="font-mono font-bold text-amber-400">{connectedEdges.length}</span>
                </div>
              </div>
            </div>

            {/* Key Connections Quick List */}
            <div>
              <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
                KEY NETWORK CONNECTIONS
              </h3>
              <div className="space-y-1.5">
                {keyConnections.length === 0 ? (
                  <p className="text-xs text-slate-500 font-mono italic">No direct connections recorded.</p>
                ) : (
                  keyConnections.slice(0, 5).map((conn) => (
                    <div
                      key={conn.relId}
                      className="p-2 rounded bg-[#131b2e]/60 border border-[#1e2d4a] flex items-center justify-between text-xs"
                    >
                      <div className="min-w-0">
                        <p className="font-semibold text-slate-200 truncate">{conn.partnerName}</p>
                        <p className="text-[10px] font-mono text-cyan-400">
                          {conn.predicate} • <span className="text-slate-400">{conn.partnerType}</span>
                        </p>
                      </div>
                      {conn.proposalStatus === 'PROPOSED' && (
                        <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-amber-950/80 border border-amber-500/60 text-amber-400 shrink-0">
                          PROPOSED
                        </span>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'RELATIONSHIPS' && (
          <div className="space-y-2">
            <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
              ALL RELATIONSHIP EDGES ({keyConnections.length})
            </h3>
            {keyConnections.map((conn) => (
              <div
                key={conn.relId}
                className="p-2.5 rounded bg-[#131b2e]/60 border border-[#1e2d4a] space-y-1 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-cyan-400 uppercase">{conn.predicate}</span>
                  <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                    conn.proposalStatus === 'PROPOSED'
                      ? 'bg-amber-950/80 border-amber-500/60 text-amber-400'
                      : conn.proposalStatus === 'ACCEPTED_BY_SUPERVISOR'
                      ? 'bg-emerald-950/80 border-emerald-500/60 text-emerald-400'
                      : 'bg-slate-900 border-slate-700 text-slate-300'
                  }`}>
                    {conn.proposalStatus === 'PROPOSED'
                      ? 'INVESTIGATOR PROPOSED'
                      : conn.proposalStatus === 'ACCEPTED_BY_SUPERVISOR'
                      ? 'SUPERVISOR ACCEPTED'
                      : 'GRAPH RECORD'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-300">
                  <span className="truncate">{conn.partnerName}</span>
                  <span className="text-[10px] font-mono text-slate-400">{conn.partnerType}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'CASES' && (
          <div className="space-y-2 text-xs">
            <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
              ASSOCIATED CASES
            </h3>
            <div className="p-3 rounded bg-[#131b2e]/60 border border-[#1e2d4a] space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono font-bold text-cyan-400">ACTIVE CASE</span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">LINKED</span>
              </div>
              <p className="text-slate-300 font-semibold leading-tight">
                Current Case Context
              </p>
            </div>
          </div>
        )}

        {activeTab === 'EVIDENCE' && (
          <div className="space-y-2 text-xs">
            <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
              LINKED EVIDENCE REFERENCES
            </h3>
            <div className="p-3 rounded bg-[#131b2e]/60 border border-[#1e2d4a] space-y-2">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-cyan-400" />
                <span className="font-mono font-semibold text-slate-200">Authenticated Evidence Reference</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-tight">
                Inspect high-resolution crime scene photos, CCTV frames, or documents via the Authenticated Evidence Viewer.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'TIMELINE' && (
          <div className="space-y-2 text-xs font-mono">
            <h3 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
              CHRONOLOGICAL EVENTS
            </h3>
            <div className="p-3 rounded bg-[#131b2e]/60 border border-[#1e2d4a] space-y-1">
              <div className="flex items-center gap-1.5 text-cyan-400">
                <Clock className="w-3.5 h-3.5" />
                <span className="font-bold">Investigation Active</span>
              </div>
              <p className="text-[10px] text-slate-400">Node associated with current case timeline events.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
