import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { casesApi } from '../api/cases';
import { evidenceApi } from '../api/evidence';
import { leadsApi } from '../api/leads';
import { useCaseSelection } from '../context/CaseSelectionContext';
import { Badge } from '../components/ui/Badge';
import { Panel } from '../components/ui/Panel';
import { 
  ArrowLeft, 
  Briefcase, 
  Loader2, 
  AlertTriangle, 
  GitFork, 
  FileText,
  Users,
  Sparkles,
  MapPin,
  Shield,
  CheckCircle2,
  UserCheck
} from 'lucide-react';

const STATUS_VARIANTS: Record<string, string> = {
  OPEN: 'active',
  ACTIVE: 'confirmed',
  CLOSED_SOLVED: 'closed',
  CLOSED_UNSOLVED: 'closed',
  CLOSED: 'closed',
  ARCHIVED: 'deferred',
  SUSPENDED: 'warning',
};

const PRIORITY_VARIANTS: Record<string, string> = {
  HIGH: 'critical',
  CRITICAL: 'critical',
  MEDIUM: 'warning',
  LOW: 'default',
};

type WorkspaceTab = 'OVERVIEW' | 'ENTITIES' | 'EVIDENCE' | 'LEADS' | 'GRAPH' | 'SPATIAL';

export const CaseWorkspacePage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { setSelectedCaseId } = useCaseSelection();

  const [activeTab, setActiveTab] = useState<WorkspaceTab>('OVERVIEW');
  const [generateMessage, setGenerateMessage] = useState<string | null>(null);

  // 1. Fetch Case Basic Info
  const { data: caseData, isLoading: isCaseLoading, error: caseError } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => (caseId ? casesApi.getCase(caseId) : Promise.reject(new Error('No case ID'))),
    enabled: !!caseId,
  });

  // 2. Fetch Case Linked Entities
  const { data: entitiesData, isLoading: isEntitiesLoading } = useQuery({
    queryKey: ['case-entities', caseId],
    queryFn: () => (caseId ? casesApi.getCaseEntities(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  // 3. Fetch Case Evidence Instances
  const { data: evidenceData, isLoading: isEvidenceLoading } = useQuery({
    queryKey: ['case-evidence', caseId],
    queryFn: () => (caseId ? evidenceApi.listEvidence(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  // 4. Fetch Case Investigative Leads
  const { data: leadsData, isLoading: isLeadsLoading } = useQuery({
    queryKey: ['case-leads', caseId],
    queryFn: () => (caseId ? leadsApi.getCaseLeads(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  // Generate Leads Mutation
  const generateLeadsMutation = useMutation({
    mutationFn: () => (caseId ? leadsApi.generateLeads(caseId) : Promise.reject(new Error('No case ID'))),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['case-leads', caseId] });
      setGenerateMessage(res.message || 'AI Investigative Leads generated successfully.');
      setTimeout(() => setGenerateMessage(null), 4000);
    },
  });

  React.useEffect(() => {
    if (caseId) setSelectedCaseId(caseId);
  }, [caseId, setSelectedCaseId]);

  function handleBack() {
    navigate('/cases');
  }

  if (isCaseLoading) {
    return (
      <div className="flex items-center justify-center py-24 space-x-3 text-civix-text-muted font-mono">
        <Loader2 className="w-5 h-5 animate-spin text-civix-blue-light" />
        <span className="text-xs">Initializing Case Command Center Workspace...</span>
      </div>
    );
  }

  if (caseError || !caseData) {
    return (
      <div className="py-16 text-center space-y-4 font-mono">
        <AlertTriangle className="w-10 h-10 text-civix-red mx-auto" />
        <div>
          <p className="text-sm font-bold text-civix-text-primary uppercase tracking-wide">Case Not Accessible</p>
          <p className="text-xs text-civix-text-muted mt-1">
            Case ID <span className="text-civix-text-mono">{caseId}</span> could not be loaded or authorized.
          </p>
        </div>
        <button onClick={handleBack} className="civix-btn-secondary inline-flex items-center space-x-2">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Case Registry</span>
        </button>
      </div>
    );
  }

  const statusVariant = STATUS_VARIANTS[caseData.status?.toUpperCase()] || 'default';
  const priorityVariant = PRIORITY_VARIANTS[caseData.priority?.toUpperCase()] || 'default';
  const isGolden = !caseData.case_number.startsWith('SYN-');

  const entitiesList = entitiesData || [];
  const evidenceList = evidenceData || [];
  const leadsList = leadsData || [];

  return (
    <div className="space-y-4 select-none font-sans">
      {/* ── Top Header & Command Bar ────────────────────────────────────────── */}
      <div className="bg-civix-surface border border-civix-border p-4 rounded-sm space-y-3">
        {/* Breadcrumb & Institutional Tags */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={handleBack}
              className="flex items-center space-x-1.5 text-xs font-semibold text-civix-text-muted hover:text-civix-text-primary transition-colors font-mono"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Case Registry</span>
            </button>
            <span className="text-civix-border-strong">/</span>
            <span className="text-xs font-mono text-civix-text-secondary font-bold">
              {caseData.case_number}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            {isGolden && (
              <span className="bg-civix-gold/20 text-civix-gold border border-civix-gold/40 text-[9px] font-mono font-bold px-2 py-0.5 rounded-xs tracking-widest uppercase">
                ★ GOLDEN BENCHMARK CASE
              </span>
            )}
            <span className="bg-civix-surface-3 border border-civix-border text-civix-text-muted text-[9px] font-mono px-2 py-0.5 rounded-xs">
              ID: {caseData.case_id}
            </span>
          </div>
        </div>

        {/* Title + Status Badges & Quick Action Bar */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-t border-civix-border-subtle pt-3">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-xl font-extrabold text-civix-text-primary tracking-tight font-mono uppercase">
                {caseData.case_number}
              </h1>
              <Badge variant={statusVariant as any}>{caseData.status}</Badge>
              <Badge variant={priorityVariant as any}>{caseData.priority}</Badge>
              <span className="text-xs font-mono font-semibold text-civix-blue-light bg-civix-blue-subtle/40 border border-civix-blue/30 px-2 py-0.5 rounded-xs">
                {caseData.case_type}
              </span>
            </div>
            <p className="text-sm font-semibold text-civix-text-primary mt-1 font-sans">
              {caseData.title}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2 flex-wrap gap-y-2">
            <button
              onClick={() => navigate(`/cases/${caseId}/graph`)}
              className="flex items-center space-x-2 bg-[#E6B325] hover:bg-[#d4a31f] text-black font-bold text-xs px-3 py-1.5 rounded-sm shadow-sm transition-colors font-mono"
            >
              <GitFork className="w-3.5 h-3.5 text-black" />
              <span>Launch Knowledge Graph</span>
            </button>

            <button
              onClick={() => generateLeadsMutation.mutate()}
              disabled={generateLeadsMutation.isPending}
              className="flex items-center space-x-1.5 civix-btn-secondary text-xs py-1.5 font-mono disabled:opacity-50"
            >
              <Sparkles className={`w-3.5 h-3.5 text-civix-gold ${generateLeadsMutation.isPending ? 'animate-spin' : ''}`} />
              <span>{generateLeadsMutation.isPending ? 'Analyzing...' : 'Generate AI Leads'}</span>
            </button>

            <button
              onClick={() => navigate('/spatial')}
              className="flex items-center space-x-1.5 civix-btn-secondary text-xs py-1.5 font-mono"
            >
              <MapPin className="w-3.5 h-3.5 text-civix-blue-light" />
              <span>Spatial Map</span>
            </button>
          </div>
        </div>

        {/* Success Alert */}
        {generateMessage && (
          <div className="flex items-center space-x-2 bg-civix-green-subtle border border-civix-green-muted text-civix-green text-xs font-semibold px-3 py-2 rounded-sm font-mono">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{generateMessage}</span>
          </div>
        )}
      </div>

      {/* ── Summary Metrics Bar ────────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-civix-surface border border-civix-border p-3 rounded-sm">
          <div className="flex items-center justify-between text-civix-text-muted">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider">Linked Entities</span>
            <Users className="w-3.5 h-3.5 text-civix-blue-light" />
          </div>
          <p className="text-xl font-extrabold font-mono text-civix-text-primary mt-1">
            {entitiesList.length}
          </p>
          <p className="text-[10px] text-civix-text-muted font-mono mt-0.5">Suspects, Victims &amp; Assets</p>
        </div>

        <div className="bg-civix-surface border border-civix-border p-3 rounded-sm">
          <div className="flex items-center justify-between text-civix-text-muted">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider">Evidence Artifacts</span>
            <FileText className="w-3.5 h-3.5 text-civix-gold" />
          </div>
          <p className="text-xl font-extrabold font-mono text-civix-gold mt-1">
            {evidenceList.length}
          </p>
          <p className="text-[10px] text-civix-text-muted font-mono mt-0.5">Documents, Media &amp; CCTV</p>
        </div>

        <div className="bg-civix-surface border border-civix-border p-3 rounded-sm">
          <div className="flex items-center justify-between text-civix-text-muted">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider">AI Leads</span>
            <Sparkles className="w-3.5 h-3.5 text-civix-green" />
          </div>
          <p className="text-xl font-extrabold font-mono text-civix-green mt-1">
            {leadsList.length}
          </p>
          <p className="text-[10px] text-civix-text-muted font-mono mt-0.5">Hypotheses &amp; Predictions</p>
        </div>

        <div className="bg-civix-surface border border-civix-border p-3 rounded-sm">
          <div className="flex items-center justify-between text-civix-text-muted">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider">Jurisdiction</span>
            <Shield className="w-3.5 h-3.5 text-slate-400" />
          </div>
          <p className="text-xs font-bold font-mono text-civix-text-primary truncate mt-1.5">
            {caseData.jurisdiction}
          </p>
          <p className="text-[10px] text-civix-text-muted font-mono mt-0.5">Delhi Police Department</p>
        </div>
      </div>

      {/* ── Navigation Tabs Bar ────────────────────────────────────────── */}
      <div className="border-b border-civix-border flex items-center space-x-1 overflow-x-auto">
        {[
          { id: 'OVERVIEW', label: 'Overview & Briefing', icon: Briefcase, count: undefined },
          { id: 'ENTITIES', label: 'Entities & Suspects', icon: Users, count: entitiesList.length },
          { id: 'EVIDENCE', label: 'Evidence Store', icon: FileText, count: evidenceList.length },
          { id: 'LEADS', label: 'AI Leads', icon: Sparkles, count: leadsList.length },
          { id: 'GRAPH', label: 'Knowledge Graph', icon: GitFork, count: undefined },
          { id: 'SPATIAL', label: 'Spatial Movement', icon: MapPin, count: undefined },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as WorkspaceTab)}
              className={`px-4 py-2 text-xs font-mono font-bold flex items-center space-x-2 border-b-2 transition-all whitespace-nowrap ${
                isActive
                  ? 'border-[#E6B325] text-[#E6B325] bg-[#E6B325]/10'
                  : 'border-transparent text-civix-text-secondary hover:text-civix-text-primary hover:bg-civix-surface-2'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#E6B325]' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded-full ${isActive ? 'bg-[#E6B325] text-black' : 'bg-civix-surface-3 text-civix-text-muted'}`}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── TAB 1: OVERVIEW & BRIEFING ────────────────────────────────────────── */}
      {activeTab === 'OVERVIEW' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Executive Briefing & Parameters */}
          <div className="lg:col-span-2 space-y-4">
            <Panel title="INVESTIGATIVE CASE BRIEFING" subtitle="Official Case Parameters & Operational Overview">
              <div className="space-y-4 text-xs font-mono">
                <div className="p-3 bg-civix-surface-2 border border-civix-border rounded-sm space-y-2">
                  <div className="flex items-center justify-between text-civix-text-muted text-[10px] uppercase tracking-wider font-bold">
                    <span>CASE SYNOPSIS</span>
                    <span>TYPE: {caseData.case_type}</span>
                  </div>
                  <p className="text-civix-text-primary leading-relaxed font-sans text-xs">
                    {caseData.title}. Authorized for active forensic tracking, graph projection, and multi-jurisdictional intelligence synthesis under Delhi Police jurisdiction.
                  </p>
                </div>

                {/* Key Parameters Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
                  <div className="p-2.5 bg-civix-surface-3 border border-civix-border rounded-sm">
                    <span className="text-[9px] text-civix-text-muted uppercase tracking-wider block font-bold">CASE NUMBER</span>
                    <span className="text-xs font-bold text-civix-blue-light mt-0.5 block">{caseData.case_number}</span>
                  </div>
                  <div className="p-2.5 bg-civix-surface-3 border border-civix-border rounded-sm">
                    <span className="text-[9px] text-civix-text-muted uppercase tracking-wider block font-bold">CURRENT STATUS</span>
                    <span className="text-xs font-bold text-civix-text-primary mt-0.5 block">{caseData.status}</span>
                  </div>
                  <div className="p-2.5 bg-civix-surface-3 border border-civix-border rounded-sm">
                    <span className="text-[9px] text-civix-text-muted uppercase tracking-wider block font-bold">PRIORITY RATING</span>
                    <span className="text-xs font-bold text-civix-red mt-0.5 block">{caseData.priority}</span>
                  </div>
                  <div className="p-2.5 bg-civix-surface-3 border border-civix-border rounded-sm">
                    <span className="text-[9px] text-civix-text-muted uppercase tracking-wider block font-bold">JURISDICTION</span>
                    <span className="text-xs font-bold text-civix-text-primary mt-0.5 block truncate">{caseData.jurisdiction}</span>
                  </div>
                  <div className="p-2.5 bg-civix-surface-3 border border-civix-border rounded-sm">
                    <span className="text-[9px] text-civix-text-muted uppercase tracking-wider block font-bold">EVIDENCE COUNT</span>
                    <span className="text-xs font-bold text-civix-gold mt-0.5 block">{evidenceList.length} Items</span>
                  </div>
                  <div className="p-2.5 bg-civix-surface-3 border border-civix-border rounded-sm">
                    <span className="text-[9px] text-civix-text-muted uppercase tracking-wider block font-bold">PROVENANCE</span>
                    <span className="text-xs font-bold text-civix-green mt-0.5 block">{isGolden ? 'GOLDEN BENCHMARK' : 'SYNTHETIC'}</span>
                  </div>
                </div>
              </div>
            </Panel>

            {/* Entities Summary Excerpt */}
            <Panel title="PRIMARY LINKED ENTITIES" subtitle="Key Persons, Vehicles & Accounts under active role assignment">
              {isEntitiesLoading ? (
                <div className="py-6 text-center text-xs font-mono text-civix-text-muted">Loading linked entities...</div>
              ) : entitiesList.length === 0 ? (
                <div className="py-6 text-center text-xs font-mono text-civix-text-muted">No entities linked to this case yet.</div>
              ) : (
                <div className="space-y-2">
                  {entitiesList.slice(0, 5).map((item) => (
                    <div key={item.role_id} className="flex items-center justify-between p-2.5 bg-civix-surface-2 border border-civix-border rounded-sm text-xs font-mono">
                      <div className="flex items-center space-x-3">
                        <UserCheck className="w-4 h-4 text-civix-blue-light" />
                        <div>
                          <span className="font-bold text-civix-text-primary block font-sans">{item.display_name}</span>
                          <span className="text-[10px] text-civix-text-muted block">Type: {item.entity_type}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="bg-civix-gold/20 text-civix-gold border border-civix-gold/40 text-[9px] font-bold px-2 py-0.5 rounded-xs">
                          {item.role}
                        </span>
                        {item.role_basis && <span className="text-[9px] text-civix-text-muted block truncate max-w-[150px]">{item.role_basis}</span>}
                      </div>
                    </div>
                  ))}
                  {entitiesList.length > 5 && (
                    <button onClick={() => setActiveTab('ENTITIES')} className="text-xs text-civix-blue-light hover:underline font-mono block w-full text-center py-1">
                      View all {entitiesList.length} entities &rarr;
                    </button>
                  )}
                </div>
              )}
            </Panel>
          </div>

          {/* Right Column: Knowledge Graph Launcher & AI Leads Preview */}
          <div className="space-y-4">
            <Panel title="INVESTIGATIVE GRAPH" subtitle="Neo4j Entity Relationship Projection">
              <div className="p-4 bg-civix-surface-2 border border-civix-border rounded-sm text-center space-y-3 font-mono">
                <GitFork className="w-8 h-8 text-civix-gold mx-auto" />
                <div>
                  <p className="text-xs font-bold text-civix-text-primary">Interactive Graph Network</p>
                  <p className="text-[10px] text-civix-text-muted mt-0.5">Explore bitemporal node connections and multi-hop pathways.</p>
                </div>
                <button
                  onClick={() => navigate(`/cases/${caseId}/graph`)}
                  className="w-full flex items-center justify-center space-x-2 bg-[#E6B325] hover:bg-[#d4a31f] text-black font-bold text-xs py-2 rounded-sm shadow-sm transition-colors font-mono"
                >
                  <GitFork className="w-4 h-4 text-black" />
                  <span>Open Full Graph Viewer</span>
                </button>
              </div>
            </Panel>

            <Panel title="AI INVESTIGATIVE LEADS" subtitle="Behavioral XGBoost & Graph Predictions">
              {isLeadsLoading ? (
                <div className="py-6 text-center text-xs font-mono text-civix-text-muted">Analyzing leads...</div>
              ) : leadsList.length === 0 ? (
                <div className="p-4 text-center space-y-2 font-mono">
                  <p className="text-xs text-civix-text-muted">No active leads generated for this case.</p>
                  <button
                    onClick={() => generateLeadsMutation.mutate()}
                    disabled={generateLeadsMutation.isPending}
                    className="civix-btn-primary text-xs py-1.5 font-mono"
                  >
                    Generate AI Leads
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  {leadsList.slice(0, 3).map((lead) => (
                    <div key={lead.lead_id} className="p-2.5 bg-civix-surface-2 border border-civix-border rounded-sm text-xs font-mono space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-civix-gold text-[10px] uppercase">LEAD #{lead.lead_id.slice(0, 8)}</span>
                        <span className="text-[9px] bg-civix-surface-3 px-1.5 py-0.5 rounded text-civix-text-muted">{lead.status}</span>
                      </div>
                      <p className="text-civix-text-primary text-xs font-sans leading-tight line-clamp-2">{lead.lead_text}</p>
                    </div>
                  ))}
                  {leadsList.length > 3 && (
                    <button onClick={() => setActiveTab('LEADS')} className="text-xs text-civix-blue-light hover:underline font-mono block w-full text-center py-1">
                      View all {leadsList.length} leads &rarr;
                    </button>
                  )}
                </div>
              )}
            </Panel>
          </div>
        </div>
      )}

      {/* ── TAB 2: ENTITIES & SUSPECTS ────────────────────────────────────────── */}
      {activeTab === 'ENTITIES' && (
        <Panel title="LINKED ENTITIES & SUSPECT MATRIX" subtitle="All persons, organizations, vehicles, and devices linked to this case">
          {isEntitiesLoading ? (
            <div className="py-12 text-center text-xs font-mono text-civix-text-muted">Loading linked entities...</div>
          ) : entitiesList.length === 0 ? (
            <div className="py-12 text-center text-xs font-mono text-civix-text-muted">No entities linked to this case.</div>
          ) : (
            <div className="overflow-x-auto -m-4">
              <table className="w-full text-xs font-mono border-collapse">
                <thead>
                  <tr className="bg-civix-surface-2 border-b border-civix-border text-[9px] font-bold text-civix-text-muted uppercase tracking-widest">
                    <th className="text-left px-4 py-3">NAME / IDENTIFIER</th>
                    <th className="text-left px-4 py-3">ENTITY TYPE</th>
                    <th className="text-left px-4 py-3">ASSIGNED ROLE</th>
                    <th className="text-left px-4 py-3">ROLE BASIS / EVIDENCE</th>
                    <th className="text-right px-4 py-3">ACTIONS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-civix-border-subtle">
                  {entitiesList.map((item) => (
                    <tr key={item.role_id} className="hover:bg-civix-surface-3 transition-colors">
                      <td className="px-4 py-3 font-sans font-bold text-civix-text-primary text-xs">
                        {item.display_name}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-xs bg-civix-surface-3 border border-civix-border text-civix-text-secondary">
                          {item.entity_type}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="bg-civix-gold/20 text-civix-gold border border-civix-gold/40 text-[9px] font-bold px-2 py-0.5 rounded-xs">
                          {item.role}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-civix-text-muted font-sans text-xs max-w-xs truncate">
                        {item.role_basis || 'Investigative Linking'}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => navigate(`/entities/${item.entity_id}`)}
                          className="civix-btn-secondary py-1 px-2.5 text-[10px] font-mono"
                        >
                          View Dossier
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      )}

      {/* ── TAB 3: EVIDENCE STORE ────────────────────────────────────────── */}
      {activeTab === 'EVIDENCE' && (
        <Panel
          title="CASE EVIDENCE STORE"
          subtitle={`Total ${evidenceList.length} evidence artifacts linked under chain of custody`}
          headerAction={
            <button onClick={() => navigate('/evidence')} className="civix-btn-primary text-xs py-1 px-3 font-mono">
              + Upload Evidence
            </button>
          }
        >
          {isEvidenceLoading ? (
            <div className="py-12 text-center text-xs font-mono text-civix-text-muted">Loading evidence items...</div>
          ) : evidenceList.length === 0 ? (
            <div className="py-12 text-center text-xs font-mono text-civix-text-muted">No evidence files stored for this case yet.</div>
          ) : (
            <div className="overflow-x-auto -m-4">
              <table className="w-full text-xs font-mono border-collapse">
                <thead>
                  <tr className="bg-civix-surface-2 border-b border-civix-border text-[9px] font-bold text-civix-text-muted uppercase tracking-widest">
                    <th className="text-left px-4 py-3">ARTIFACT / INSTANCE ID</th>
                    <th className="text-left px-4 py-3">FILENAME</th>
                    <th className="text-left px-4 py-3">MIME TYPE</th>
                    <th className="text-left px-4 py-3">STATUS</th>
                    <th className="text-left px-4 py-3">CREATED AT</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-civix-border-subtle">
                  {evidenceList.map((item) => (
                    <tr key={item.instance_id} className="hover:bg-civix-surface-3 transition-colors">
                      <td className="px-4 py-3 font-bold text-civix-blue-light text-xs">
                        {item.instance_id.slice(0, 18)}...
                      </td>
                      <td className="px-4 py-3 font-sans text-civix-text-primary text-xs">
                        {item.original_filename || 'Evidence File'}
                      </td>
                      <td className="px-4 py-3 text-civix-text-muted text-[10px]">
                        {item.mime_type || 'application/octet-stream'}
                      </td>
                      <td className="px-4 py-3">
                        <span className="bg-civix-green/20 text-civix-green border border-civix-green/40 text-[9px] font-bold px-2 py-0.5 rounded-xs">
                          {item.processing_status || 'STORED'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-civix-text-muted text-xs">
                        {new Date(item.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      )}

      {/* ── TAB 4: AI INVESTIGATIVE LEADS ────────────────────────────────────────── */}
      {activeTab === 'LEADS' && (
        <Panel
          title="AI INVESTIGATIVE LEADS & HYPOTHESIS SCORING"
          subtitle="Machine learning anomaly predictions and behavioral graph leads"
          headerAction={
            <button
              onClick={() => generateLeadsMutation.mutate()}
              disabled={generateLeadsMutation.isPending}
              className="civix-btn-primary text-xs py-1 px-3 font-mono disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 mr-1" />
              <span>Generate AI Leads</span>
            </button>
          }
        >
          {isLeadsLoading ? (
            <div className="py-12 text-center text-xs font-mono text-civix-text-muted">Loading investigative leads...</div>
          ) : leadsList.length === 0 ? (
            <div className="py-12 text-center space-y-3 font-mono">
              <Sparkles className="w-8 h-8 text-civix-gold mx-auto" />
              <p className="text-xs text-civix-text-muted">No investigative leads generated yet for this case.</p>
              <button onClick={() => generateLeadsMutation.mutate()} className="civix-btn-primary text-xs py-1.5 px-4">
                Run AI Lead Generator
              </button>
            </div>
          ) : (
            <div className="space-y-3 font-mono">
              {leadsList.map((lead) => (
                <div key={lead.lead_id} className="p-4 bg-civix-surface-2 border border-civix-border rounded-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-extrabold text-civix-gold text-xs">LEAD #{lead.lead_id.slice(0, 8)}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-civix-surface-3 border border-civix-border text-civix-text-primary">
                        PRIORITY: {lead.priority || 'MEDIUM'}
                      </span>
                    </div>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-xs bg-civix-green/20 text-civix-green border border-civix-green/40">
                      {lead.status}
                    </span>
                  </div>

                  <p className="text-xs font-sans text-civix-text-primary leading-relaxed">
                    {lead.lead_text}
                  </p>

                  {lead.ai_confidence !== undefined && (
                    <div className="flex items-center space-x-3 pt-1 text-[10px]">
                      <span className="text-civix-text-muted">AI Confidence:</span>
                      <div className="flex-1 max-w-xs bg-civix-surface-3 h-2 rounded-full overflow-hidden border border-civix-border">
                        <div
                          className="bg-civix-gold h-full rounded-full"
                          style={{ width: `${Math.min(100, Math.max(10, (lead.ai_confidence || 0.8) * 100))}%` }}
                        />
                      </div>
                      <span className="font-bold text-civix-gold">{( (lead.ai_confidence || 0.8) * 100).toFixed(0)}%</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Panel>
      )}

      {/* ── TAB 5: KNOWLEDGE GRAPH ────────────────────────────────────────── */}
      {activeTab === 'GRAPH' && (
        <Panel title="EMBEDDED KNOWLEDGE GRAPH" subtitle="Neo4j Graph Projection & Bitemporal Relationship Inspector">
          <div className="p-8 bg-civix-surface-2 border border-civix-border rounded-sm text-center space-y-4 font-mono">
            <GitFork className="w-12 h-12 text-civix-gold mx-auto animate-pulse" />
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-civix-text-primary uppercase tracking-wide">
                Neo4j Graph Projection — Case {caseData.case_number}
              </h3>
              <p className="text-xs text-civix-text-muted max-w-md mx-auto font-sans">
                Full interactive visualization ready with node traversal, relationship inspector, 1-hop and 2-hop filters.
              </p>
            </div>
            <button
              onClick={() => navigate(`/cases/${caseId}/graph`)}
              className="inline-flex items-center space-x-2 bg-[#E6B325] hover:bg-[#d4a31f] text-black font-bold text-xs px-5 py-2.5 rounded-sm shadow-md transition-colors"
            >
              <GitFork className="w-4 h-4 text-black" />
              <span>Launch Fullscreen Graph Viewer</span>
            </button>
          </div>
        </Panel>
      )}

      {/* ── TAB 6: SPATIAL MOVEMENT ────────────────────────────────────────── */}
      {activeTab === 'SPATIAL' && (
        <Panel title="SPATIAL MOVEMENT & CCTV SIGHTINGS" subtitle="PostGIS Geolocation Centroids & Camera Feeds">
          <div className="p-8 bg-civix-surface-2 border border-civix-border rounded-sm text-center space-y-4 font-mono">
            <MapPin className="w-12 h-12 text-civix-blue-light mx-auto" />
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-civix-text-primary uppercase tracking-wide">
                Spatial Intelligence Subsystem — Case {caseData.case_number}
              </h3>
              <p className="text-xs text-civix-text-muted max-w-md mx-auto font-sans">
                Interactive Leaflet operational map, timeline scrubber, and 25 Delhi NCR live CCTV streams.
              </p>
            </div>
            <button
              onClick={() => navigate('/spatial')}
              className="inline-flex items-center space-x-2 civix-btn-primary text-xs px-5 py-2.5"
            >
              <MapPin className="w-4 h-4" />
              <span>Open Spatial Intelligence Workstation</span>
            </button>
          </div>
        </Panel>
      )}
    </div>
  );
};
