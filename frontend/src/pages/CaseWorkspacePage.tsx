import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { casesApi } from '../api/cases';
import { evidenceApi } from '../api/evidence';
import { leadsApi } from '../api/leads';
import { spatialApi } from '../api/spatial';
import { useCaseSelection } from '../context/CaseSelectionContext';
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
  Clock,
  Link2,
  ShieldCheck,
  User
} from 'lucide-react';
import { MapContainer, TileLayer, Marker } from 'react-leaflet';
import L from 'leaflet';
import { SpatialIntelligencePage } from './SpatialIntelligencePage';
import { InvestigativeGraphPage } from './InvestigativeGraphPage';
import { CaseEvidenceVault } from '../components/domain/CaseEvidenceVault';

const PRIORITY_VARIANTS: Record<string, string> = {
  HIGH: 'critical',
  CRITICAL: 'critical',
  MEDIUM: 'warning',
  LOW: 'default',
};

type WorkspaceTab = 'OVERVIEW' | 'ENTITIES' | 'EVIDENCE' | 'LEADS' | 'TIMELINE' | 'SPATIAL' | 'GRAPH' | 'RELATED' | 'AUDIT';

// Fix leaflet icon
const markerIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

export const CaseWorkspacePage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const { setSelectedCaseId } = useCaseSelection();
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('OVERVIEW');

  useEffect(() => {
    if (caseId) setSelectedCaseId(caseId);
  }, [caseId, setSelectedCaseId]);

  // 1. Fetch Case Basic Info
  const { data: caseData, isLoading: isCaseLoading, error: caseError } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => (caseId ? casesApi.getCase(caseId) : Promise.reject(new Error('No case ID'))),
    enabled: !!caseId,
  });

  // 2. Fetch Case Linked Entities
  const { data: entitiesData } = useQuery({
    queryKey: ['case-entities', caseId],
    queryFn: () => (caseId ? casesApi.getCaseEntities(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  // 3. Fetch Case Evidence Instances
  const { data: evidenceData, isLoading: isEvidenceLoading, error: evidenceError, refetch: refetchEvidence } = useQuery({
    queryKey: ['case-evidence', caseId],
    queryFn: () => (caseId ? evidenceApi.listEvidence(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  // 4. Fetch Case Investigative Leads (For Counts)
  const { data: leadsData } = useQuery({
    queryKey: ['case-leads', caseId],
    queryFn: () => (caseId ? leadsApi.getCaseLeads(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  // 5. Fetch Spatial Events
  const { data: spatialData } = useQuery({
    queryKey: ['case-spatial', caseId],
    queryFn: () => (caseId ? spatialApi.getSpatialCaseEvents(caseId) : Promise.resolve(null)),
    enabled: !!caseId,
  });

  if (isCaseLoading) {
    return (
      <div className="flex items-center justify-center py-24 space-x-3 text-civix-text-muted font-mono">
        <Loader2 className="w-5 h-5 animate-spin text-civix-blue-light" />
        <span className="text-xs">Initializing Investigation Workspace...</span>
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
        <button onClick={() => navigate('/cases')} className="civix-btn-secondary inline-flex items-center space-x-2">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Case Registry</span>
        </button>
      </div>
    );
  }

  const isGolden = !caseData.case_number.startsWith('SYN-');
  const entitiesList = entitiesData || [];
  const evidenceList = evidenceData || [];
  const imageEvidenceList = evidenceList.filter(evidence => 
    evidence.mime_type?.startsWith('image/') || 
    evidence.original_filename?.match(/\.(png|jpg|jpeg|webp|gif)$/i)
  );
  const leadsList = leadsData || [];
  
  const officerRoles = ['OFFICER_IN_CHARGE', 'INVESTIGATING_OFFICER', 'SUPERVISING_OFFICER'];
  const civilians = entitiesList.filter(e => !officerRoles.includes(e.role));
  const officers = entitiesList.filter(e => officerRoles.includes(e.role));

  const mapCenter = spatialData?.features?.[0]?.geometry?.coordinates; // [lng, lat]
  const centerPosition: [number, number] | undefined = (Array.isArray(mapCenter) && typeof mapCenter[0] === 'number' && typeof mapCenter[1] === 'number')
    ? [mapCenter[1] as number, mapCenter[0] as number]
    : undefined;

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'Not available';
    return new Date(isoString).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const calculateDuration = () => {
    if (!caseData.opened_at) return null;
    const start = new Date(caseData.opened_at).getTime();
    const end = (caseData.status === 'CLOSED_SOLVED' || caseData.status === 'CLOSED_UNSOLVED') && caseData.updated_at 
        ? new Date(caseData.updated_at).getTime() 
        : new Date().getTime();
    const days = Math.floor((end - start) / (1000 * 60 * 60 * 24));
    if (days < 0) return 'Just opened';
    if (days < 30) return `${days} days`;
    if (days < 365) return `${Math.floor(days / 30)} months`;
    return `${Math.floor(days / 365)} years`;
  };

  return (
    <div className="w-full text-civix-text-primary bg-[#05080D] min-h-screen">
      {/* CASE HEADER */}
      <div className="px-6 py-6 bg-civix-surface border-b border-civix-border space-y-4 shadow-sm">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/cases')}
            className="flex items-center space-x-1.5 text-xs font-semibold text-civix-text-muted hover:text-civix-text-primary transition-colors font-mono"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Cases / {caseData.case_number}</span>
          </button>
        </div>

        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-extrabold tracking-tight font-sans text-white">
                {caseData.case_number}
              </h1>
              {isGolden ? (
                <span className="bg-civix-gold/20 text-civix-gold border border-civix-gold/40 text-[9px] font-mono font-bold px-2 py-0.5 rounded-xs tracking-widest uppercase flex items-center">
                  <span className="mr-1">★</span> GOLDEN BENCHMARK
                </span>
              ) : (
                <span className="bg-civix-surface-3 text-civix-text-secondary border border-civix-border text-[9px] font-mono font-bold px-2 py-0.5 rounded-xs tracking-widest uppercase">
                  SYNTHETIC BENCHMARK
                </span>
              )}
            </div>
            
            <p className="text-lg font-medium text-white max-w-3xl font-sans">
              {caseData.title}
            </p>
            
            <div className="flex items-center space-x-2 text-xs font-mono text-civix-text-muted">
              <span>{caseData.police_station || caseData.jurisdiction}</span>
              <span className="text-civix-border-strong">·</span>
              <span>Created {formatDate(caseData.created_at)}</span>
              <span className="text-civix-border-strong">·</span>
              <span>Last activity {formatDate(caseData.updated_at)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* CASE NAVIGATION */}
      <div className="border-b border-civix-border bg-civix-surface px-4 flex items-center space-x-1 overflow-x-auto shadow-sm">
        {[
          { id: 'OVERVIEW', label: 'Overview', icon: Briefcase },
          { id: 'ENTITIES', label: 'Entities', icon: Users, count: entitiesList.length },
          { id: 'EVIDENCE', label: 'Evidence', icon: FileText, count: evidenceList.length },
          { id: 'LEADS', label: 'Leads', icon: Sparkles, count: leadsList.length },
          { id: 'TIMELINE', label: 'Timeline', icon: Clock },
          { id: 'SPATIAL', label: 'Spatial', icon: MapPin },
          { id: 'GRAPH', label: 'Graph', icon: GitFork },
          { id: 'RELATED', label: 'Related Cases', icon: Link2 },
          { id: 'AUDIT', label: 'Audit', icon: ShieldCheck },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                if (tab.id === 'GRAPH') {
                  navigate(`/cases/${caseId}/graph`);
                } else {
                  setActiveTab(tab.id as WorkspaceTab);
                }
              }}
              className={`px-4 py-3 text-xs font-mono font-semibold flex items-center space-x-2 border-b-2 transition-all whitespace-nowrap ${
                isActive
                  ? 'border-[#E6B325] text-[#E6B325] bg-[#E6B325]/10'
                  : 'border-transparent text-civix-text-secondary hover:text-white hover:bg-civix-surface-2'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#E6B325]' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* MAIN LAYOUT */}
      <div className="p-6">
        {activeTab === 'OVERVIEW' ? (
          <div className="flex flex-col xl:flex-row gap-6">
            
            {/* LEFT INVESTIGATION COLUMN (75-78%) */}
            <div className="flex-1 space-y-8 min-w-0">
              
              {/* PEOPLE INVOLVED */}
              <section>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                    People Involved
                  </h2>
                  <button className="text-xs font-mono text-civix-blue-light hover:underline">
                    View All ({civilians.length}) →
                  </button>
                </div>
                {civilians.length === 0 ? (
                  <div className="p-8 text-center bg-civix-surface border border-civix-border rounded-sm">
                    <p className="text-xs font-mono text-civix-text-muted font-bold">NO PEOPLE LINKED</p>
                    <p className="text-[10px] font-sans text-civix-text-muted mt-1">No person entities are currently associated with this case.</p>
                  </div>
                ) : (
                  <div className="flex overflow-x-auto space-x-4 pb-4 snap-x">
                    {civilians.map((person, idx) => (
                      <div key={idx} className="flex-none w-48 bg-civix-surface border border-civix-border rounded-sm overflow-hidden flex flex-col snap-start cursor-pointer hover:border-civix-blue/50 transition-colors">
                        <div className="h-32 bg-civix-surface-2 flex items-center justify-center border-b border-civix-border relative">
                          {person.avatar_url ? (
                            <img src={person.avatar_url} alt={person.display_name} className="w-full h-full object-cover" />
                          ) : (
                            <User className="w-10 h-10 text-slate-500 opacity-50" />
                          )}
                          <div className="absolute inset-0 flex items-center justify-center bg-black/60 opacity-0 hover:opacity-100 transition-opacity">
                            <span className="text-[9px] font-mono font-bold text-white uppercase">VIEW PROFILE ▶</span>
                          </div>
                        </div>
                        <div className="p-3">
                          <span className="text-[9px] font-mono font-bold text-civix-gold uppercase tracking-wider block mb-1">
                            {person.role.replace(/_/g, ' ')}
                          </span>
                          <h3 className="text-sm font-bold text-white font-sans truncate" title={person.display_name}>
                            {person.display_name}
                          </h3>
                          <p className="text-[10px] text-civix-text-secondary mt-1 font-sans">
                            {person.gender ? person.gender : 'Unknown gender'}{person.date_of_birth ? ` · DOB: ${person.date_of_birth}` : ''}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* KEY EVIDENCE */}
              <section>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                      Key Evidence
                    </h2>
                    <span className="text-[10px] font-mono text-civix-gold bg-civix-gold/10 px-2 py-0.5 rounded border border-civix-gold/30">
                      Visual Previews Only ({imageEvidenceList.length})
                    </span>
                  </div>
                  <button 
                    onClick={() => setActiveTab('EVIDENCE')}
                    className="text-xs font-mono text-civix-blue-light hover:underline flex items-center space-x-1 cursor-pointer"
                  >
                    <span>View All Evidence ({evidenceList.length})</span>
                    <span>→</span>
                  </button>
                </div>
                {imageEvidenceList.length === 0 ? (
                  <div className="p-8 text-center bg-civix-surface border border-civix-border rounded-sm">
                    <p className="text-xs font-mono text-civix-text-muted font-bold">NO IMAGE EVIDENCE PREVIEWS AVAILABLE</p>
                    <p className="text-[10px] font-sans text-civix-text-muted mt-1">
                      No visual image artifacts exist in this case preview ({evidenceList.length} total document/file artifacts linked).
                    </p>
                    <button 
                      onClick={() => setActiveTab('EVIDENCE')} 
                      className="mt-3 civix-btn-secondary text-xs font-mono cursor-pointer"
                    >
                      View All Case Evidence ({evidenceList.length}) →
                    </button>
                  </div>
                ) : (
                  <div className="flex overflow-x-auto space-x-4 pb-4 snap-x">
                    {imageEvidenceList.map((evidence, idx) => {
                      const contentUrl = `/api/v1/evidence/artifacts/${evidence.artifact_id}/content?v=${new Date(evidence.created_at || Date.now()).getTime()}`;
                      return (
                        <div 
                          key={idx} 
                          onClick={() => setActiveTab('EVIDENCE')}
                          className="flex-none w-64 bg-civix-surface border border-civix-border rounded-sm overflow-hidden flex flex-col snap-start cursor-pointer hover:border-civix-blue/50 transition-colors"
                        >
                          <div className="h-32 bg-[#0a0e17] flex items-center justify-center border-b border-civix-border relative group overflow-hidden">
                            <img 
                              src={contentUrl} 
                              alt={evidence.evidence_title || evidence.original_filename || 'Evidence Artifact'} 
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                              onError={(e) => {
                                (e.target as HTMLElement).style.display = 'none';
                              }}
                            />
                            <div className="absolute inset-0 flex items-center justify-center bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity">
                              <span className="text-[9px] font-mono font-bold text-white uppercase">OPEN EVIDENCE STORE ▶</span>
                            </div>
                          </div>
                          <div className="p-3">
                            <span className="text-[9px] font-mono font-bold text-civix-gold uppercase tracking-wider block mb-1">
                              {evidence.evidence_type?.replace(/_/g, ' ') || 'IMAGE ARTIFACT'}
                            </span>
                            <h3 className="text-xs font-semibold text-white font-sans line-clamp-2" title={evidence.evidence_title || evidence.original_filename || 'Unknown Evidence'}>
                              {evidence.evidence_title || evidence.original_filename || 'Unknown Evidence'}
                            </h3>
                            <p className="text-[9px] text-civix-text-secondary mt-1.5 font-mono">
                              {formatDate(evidence.created_at)} · {evidence.mime_type?.split('/')[1]?.toUpperCase() || 'IMAGE'}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>

              {/* OFFICERS INVOLVED */}
              <section>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                    Officers Involved
                  </h2>
                </div>
                {officers.length === 0 ? (
                  <div className="p-6 bg-civix-surface border border-civix-border rounded-sm">
                    <p className="text-xs font-mono text-civix-text-muted font-bold mb-1">OFFICER RECORDS UNAVAILABLE</p>
                    <p className="text-[10px] font-sans text-civix-text-muted">Personnel information has not yet been linked to this case in the current dataset.</p>
                  </div>
                ) : (
                  <div className="flex overflow-x-auto space-x-4 pb-4 snap-x">
                    {officers.map((officer, idx) => (
                      <div key={idx} className="flex-none w-48 bg-civix-surface border border-civix-border rounded-sm overflow-hidden flex flex-col snap-start">
                        <div className="h-28 bg-civix-surface-2 flex items-center justify-center border-b border-civix-border relative">
                          <User className="w-9 h-9 text-civix-blue-light/70" />
                          <div className="absolute top-2 right-2 bg-civix-blue/30 text-civix-blue-light border border-civix-blue/50 text-[8px] font-mono font-bold px-1.5 py-0.5 rounded-xs">
                            POLICE
                          </div>
                        </div>
                        <div className="p-3">
                          <span className="text-[9px] font-mono font-bold text-civix-blue-light uppercase tracking-wider block mb-0.5 truncate">
                            {officer.role.replace(/_/g, ' ')}
                          </span>
                          <h3 className="text-xs font-bold text-white font-sans truncate" title={officer.display_name}>
                            {officer.display_name}
                          </h3>
                          <p className="text-[9px] text-civix-text-muted mt-1 font-mono">
                            {officer.role_basis || 'Delhi Police'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>

            {/* RIGHT INFORMATION COLUMN (22-25%) */}
            <div className="xl:w-80 flex-shrink-0 space-y-6">
              
              {/* CASE SUMMARY */}
              <div className="bg-civix-surface border border-civix-border rounded-sm">
                <div className="border-b border-civix-border p-3 bg-civix-surface-2">
                  <h3 className="text-[10px] font-mono font-bold text-white uppercase tracking-widest">Case Summary</h3>
                </div>
                <div className="p-4">
                  <span className="text-[9px] font-mono font-bold text-civix-text-muted uppercase tracking-wider block mb-2">
                    OPERATIONAL SYNOPSIS
                  </span>
                  <p className="text-xs text-civix-text-secondary leading-relaxed font-sans">
                    {caseData.investigating_unit || 'No detailed case synopsis available in the dataset.'}
                  </p>
                </div>
              </div>

              {/* CASE STATUS */}
              <div className="bg-civix-surface border border-civix-border rounded-sm">
                <div className="border-b border-civix-border p-3 bg-civix-surface-2">
                  <h3 className="text-[10px] font-mono font-bold text-white uppercase tracking-widest">Case Status</h3>
                </div>
                <div className="p-4 space-y-4">
                  <div className="flex items-center space-x-2">
                    <span className={`w-2 h-2 rounded-full ${caseData.status.startsWith('CLOSED') ? 'bg-civix-green' : 'bg-civix-gold'}`}></span>
                    <span className="text-xs font-bold font-mono text-white uppercase">{caseData.status.replace(/_/g, ' — ')}</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-[9px] font-mono font-bold text-civix-text-muted uppercase tracking-wider block mb-1">
                        Last Activity
                      </span>
                      <span className="text-xs font-mono text-white">
                        {formatDate(caseData.updated_at)}
                      </span>
                    </div>
                    <div>
                      <span className="text-[9px] font-mono font-bold text-civix-text-muted uppercase tracking-wider block mb-1">
                        Duration
                      </span>
                      <span className="text-xs font-mono text-white">
                        {calculateDuration() || 'Unknown'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* CASE DETAILS */}
              <div className="bg-civix-surface border border-civix-border rounded-sm">
                <div className="border-b border-civix-border p-3 bg-civix-surface-2">
                  <h3 className="text-[10px] font-mono font-bold text-white uppercase tracking-widest">Case Details</h3>
                </div>
                <div className="p-4">
                  <dl className="space-y-3 text-xs font-mono">
                    <div className="flex justify-between">
                      <dt className="text-civix-text-muted">Case Number</dt>
                      <dd className="text-white font-bold">{caseData.case_number}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-civix-text-muted">Case Type</dt>
                      <dd className="text-white capitalize">{caseData.case_type?.toLowerCase()}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-civix-text-muted">Priority</dt>
                      <dd className={`font-bold ${PRIORITY_VARIANTS[caseData.priority] === 'critical' ? 'text-civix-red' : 'text-civix-gold'}`}>
                        {caseData.priority}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-civix-text-muted">Provenance</dt>
                      <dd className="text-white">{isGolden ? 'Golden Benchmark' : 'Synthetic Benchmark'}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-civix-text-muted">Jurisdiction</dt>
                      <dd className="text-white text-right max-w-[120px] truncate" title={caseData.jurisdiction}>
                        {caseData.jurisdiction}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-civix-text-muted">Related District</dt>
                      <dd className="text-white text-right max-w-[120px] truncate" title={caseData.district || 'Not available'}>
                        {caseData.district || 'Not available'}
                      </dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-civix-text-muted">FIR Reference</dt>
                      <dd className="text-white">{caseData.fir_number || 'Not available'}</dd>
                    </div>
                    <div className="flex justify-between flex-col gap-1">
                      <dt className="text-civix-text-muted">Primary Offences</dt>
                      <dd className="text-white">
                        {caseData.sections_invoked && caseData.sections_invoked.length > 0
                          ? caseData.sections_invoked.join(', ')
                          : 'Not available'}
                      </dd>
                    </div>
                  </dl>
                </div>
              </div>

              {/* INCIDENT LOCATION */}
              <div className="bg-civix-surface border border-civix-border rounded-sm">
                <div className="border-b border-civix-border p-3 bg-civix-surface-2 flex items-center justify-between">
                  <h3 className="text-[10px] font-mono font-bold text-white uppercase tracking-widest">Incident Location</h3>
                  <MapPin className="w-3 h-3 text-civix-text-muted" />
                </div>
                <div className="p-1">
                  <div className="h-40 w-full bg-[#0a0e17] rounded-sm overflow-hidden relative z-0">
                    {centerPosition ? (
                      <MapContainer
                        center={centerPosition}
                        zoom={13}
                        style={{ height: '100%', width: '100%', background: '#0a0e17' }}
                        zoomControl={false}
                        attributionControl={false}
                        dragging={false}
                        doubleClickZoom={false}
                        scrollWheelZoom={false}
                      >
                        <TileLayer
                          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        />
                        <Marker position={centerPosition} icon={markerIcon} />
                      </MapContainer>
                    ) : (
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <MapPin className="w-6 h-6 text-civix-text-muted/50 mb-2" />
                        <span className="text-[9px] font-mono font-bold text-civix-text-muted uppercase">No coordinate data</span>
                      </div>
                    )}
                  </div>
                  {centerPosition && spatialData?.features?.[0] && (
                    <div className="p-3">
                      <h4 className="text-xs font-bold text-white font-sans truncate">
                        {spatialData.features[0].properties.location_name}
                      </h4>
                      <p className="text-[10px] text-civix-text-muted font-mono mt-0.5">
                        {spatialData.features[0].properties.location_type || 'General Location'}
                      </p>
                    </div>
                  )}
                </div>
              </div>

            </div>
          </div>
        ) : activeTab === 'ENTITIES' ? (
          <div className="bg-civix-surface border border-civix-border rounded-sm shadow-sm">
            <div className="border-b border-civix-border p-4 bg-civix-surface-2 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-widest font-mono">LINKED ENTITIES & SUSPECT MATRIX</h3>
                <p className="text-[10px] font-sans text-civix-text-muted mt-1">All persons, organizations, vehicles, and devices linked to this case</p>
              </div>
            </div>
            <div className="p-0">
              {entitiesList.length === 0 ? (
                <div className="py-12 text-center text-xs font-mono text-civix-text-muted">No entities linked to this case.</div>
              ) : (
                <div className="overflow-x-auto">
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
            </div>
          </div>
        ) : activeTab === 'EVIDENCE' ? (
          <CaseEvidenceVault
            caseId={caseId || ''}
            evidenceList={evidenceList}
            isLoading={isEvidenceLoading}
            error={evidenceError}
            refetch={refetchEvidence}
          />
        ) : activeTab === 'LEADS' ? (
          <div className="bg-civix-surface border border-civix-border rounded-sm shadow-sm">
            <div className="border-b border-civix-border p-4 bg-civix-surface-2 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-widest font-mono">AI INVESTIGATIVE LEADS</h3>
                <p className="text-[10px] font-sans text-civix-text-muted mt-1">Machine learning anomaly predictions and behavioral graph leads</p>
              </div>
            </div>
            <div className="p-6">
              {leadsList.length === 0 ? (
                <div className="py-12 text-center space-y-3 font-mono">
                  <Sparkles className="w-8 h-8 text-civix-gold mx-auto" />
                  <p className="text-xs text-civix-text-muted">No investigative leads generated yet for this case.</p>
                </div>
              ) : (
                <div className="space-y-4 font-mono">
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
            </div>
          </div>
        ) : activeTab === 'GRAPH' ? (
          <div className="bg-civix-surface border border-civix-border rounded-sm shadow-sm p-8 text-center space-y-4">
            <GitFork className="w-10 h-10 text-cyan-400 mx-auto" />
            <div>
              <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider">INVESTIGATIVE GRAPH WORKSPACE</h3>
              <p className="text-xs text-slate-400 font-mono mt-1">Full-screen 5-hop knowledge graph network workspace</p>
            </div>
            <button
              onClick={() => navigate(`/cases/${caseId}/graph`)}
              className="bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold px-4 py-2 rounded transition-colors inline-flex items-center gap-2"
            >
              <span>OPEN FULL GRAPH WORKSPACE →</span>
            </button>
          </div>
        ) : activeTab === 'SPATIAL' ? (
          <div className="bg-civix-surface border border-civix-border rounded-sm shadow-sm p-4 min-h-[620px]">
            <SpatialIntelligencePage caseIdProp={caseId} embedded={true} />
          </div>
        ) : (
          <div className="flex items-center justify-center py-24 text-civix-text-muted font-mono text-xs border border-civix-border border-dashed rounded-sm">
            Component not implemented for this view.
          </div>
        )}
      </div>
    </div>
  );
};
