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
  User,
  MapPin,
  Car,
  Smartphone,
  ChevronDown,
  Calendar,
  Clock,
  Shield,
  Info,
  ExternalLink,
  Printer,
  ChevronRight
} from 'lucide-react';
import { CaseEntityRegistry } from '../components/domain/CaseEntityRegistry';
import { SpatialIntelligencePage } from './SpatialIntelligencePage';
import { CaseLeadsView } from '../components/domain/CaseLeadsView';
import { CaseReportsView } from '../components/domain/CaseReportsView';
import { InvestigativeGraphPage } from './InvestigativeGraphPage';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

type WorkspaceTab = 'OVERVIEW' | 'ENTITIES' | 'LEADS' | 'SPATIAL' | 'GRAPH' | 'REPORTS';

export const CaseWorkspacePage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const { setSelectedCaseId } = useCaseSelection();
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('OVERVIEW');
  const [showActionsDropdown, setShowActionsDropdown] = useState(false);

  useEffect(() => {
    if (caseId) setSelectedCaseId(caseId);
  }, [caseId, setSelectedCaseId]);

  // 1. Fetch Case Basic Info
  const { data: caseData, isLoading: isCaseLoading, error: caseError } = useQuery({
    queryKey: ['case', caseId],
    queryFn: () => (caseId ? casesApi.getCase(caseId) : Promise.reject(new Error('No case ID'))),
    enabled: !!caseId,
  });

  // 2. Fetch Case Linked Person Entities (specifically entity_type: PERSON)
  const { data: entitiesResponse } = useQuery({
    queryKey: ['case-entities-person', caseId],
    queryFn: () => (caseId ? casesApi.getCaseEntities(caseId, { entity_type: 'PERSON', limit: 100 }) : Promise.resolve(null)),
    enabled: !!caseId,
  });

  // 3. Fetch Case Evidence Instances (for Preview and Counts)
  const { data: evidenceData } = useQuery({
    queryKey: ['case-evidence', caseId],
    queryFn: () => (caseId ? evidenceApi.listEvidence(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  // 4. Fetch Case Investigative Leads (for Counts)
  const { data: leadsData } = useQuery({
    queryKey: ['case-leads', caseId],
    queryFn: () => (caseId ? leadsApi.getCaseLeads(caseId) : Promise.resolve([])),
    enabled: !!caseId,
  });

  // 5. Fetch Spatial Events (for Locations)
  const { data: spatialData } = useQuery({
    queryKey: ['case-spatial', caseId],
    queryFn: () => (caseId ? spatialApi.getSpatialCaseEvents(caseId) : Promise.resolve(null)),
    enabled: !!caseId,
  });

  if (isCaseLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4 text-civix-text-muted font-mono bg-[#05080D] min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
        <span className="text-xs uppercase tracking-widest">Initializing Investigation Workstation...</span>
      </div>
    );
  }

  if (caseError || !caseData) {
    return (
      <div className="py-24 text-center space-y-4 font-mono bg-[#05080D] min-h-screen">
        <AlertTriangle className="w-12 h-12 text-red-500 mx-auto" />
        <div>
          <p className="text-sm font-bold text-white uppercase tracking-wide">Case Not Accessible</p>
          <p className="text-xs text-slate-400 mt-1">
            Case ID <span className="text-cyan-400">{caseId}</span> could not be loaded or authorized.
          </p>
        </div>
        <button onClick={() => navigate('/cases')} className="civix-btn-secondary inline-flex items-center space-x-2">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Case Registry</span>
        </button>
      </div>
    );
  }

  const rawItems = entitiesResponse?.items || [];
  const entityCounts = entitiesResponse?.entity_counts;
  const totalEntityCount = entitiesResponse?.total_count || rawItems.length;

  const evidenceList = evidenceData || [];
  const leadsList = leadsData || [];
  
  // Person Entities & Officers Classification
  const personEntities = rawItems.filter(e => e.entity_type?.toUpperCase() === 'PERSON');
  const officerRoles = ['OFFICER_IN_CHARGE', 'INVESTIGATING_OFFICER', 'SUPERVISING_OFFICER'];
  const civilians = personEntities.filter(e => !officerRoles.includes(e.role));
  const officers = personEntities.filter(e => officerRoles.includes(e.role));

  const boundedCivilians = civilians.slice(0, 12);
  const boundedOfficers = officers.slice(0, 12);

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return '4 Sept 2026';
    return new Date(isoString).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const calculateDuration = () => {
    if (!caseData.opened_at) return '14 years';
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
    <div className="w-full text-slate-100 bg-[#05080D] min-h-screen font-mono select-none pb-12">
      {/* ── 1. CINEMATIC HERO CASE BANNER ────────────────────────────────────────── */}
      <div className="relative border-b border-[#1E293B] overflow-hidden bg-[#070B14]">
        {/* Widescreen Banner Image - Clear High-Visibility Rendering */}
        <div 
          className="absolute inset-0 bg-cover bg-center opacity-85 pointer-events-none transition-opacity duration-700"
          style={{ backgroundImage: "url('/assets/case_workspace_dwarka_banner.png')" }}
        />

        {/* Very Subtle Text Readability Vignette & Light Gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#05080F]/70 via-[#070B14]/30 to-[#05080F]/70 pointer-events-none" />
        <div className="absolute inset-0 bg-gradient-to-b from-[#05080F]/30 via-transparent to-[#05080D]/90 pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(#38BDF8_1px,transparent_1px)] [background-size:24px_24px] opacity-5 pointer-events-none" />

        {/* Hero Banner Content Container */}
        <div className="relative z-10 px-6 pt-5 pb-4 space-y-4 max-w-[1700px] mx-auto">
          {/* Top Breadcrumb & Status Row */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <button
              onClick={() => navigate('/cases')}
              className="flex items-center space-x-1.5 text-xs font-mono text-slate-400 hover:text-cyan-400 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Cases</span>
              <span className="text-slate-600">/</span>
              <span className="text-cyan-400 font-bold">{caseData.case_number}</span>
            </button>
          </div>

          {/* Status & Priority Badges */}
          <div className="flex items-center space-x-2">
            <span className="bg-emerald-950/70 text-emerald-400 border border-emerald-800/50 text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-xs tracking-wider uppercase flex items-center shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
              {caseData.status || 'ACTIVE'}
            </span>

            <span className="bg-red-950/70 text-red-400 border border-red-800/50 text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-xs tracking-wider uppercase flex items-center shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 mr-1.5 animate-pulse" />
              {caseData.priority || 'CRITICAL'}
            </span>
          </div>

          {/* Case Number Title Header */}
          <div className="space-y-1">
            <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight font-sans text-white uppercase drop-shadow-md">
              {caseData.case_number}
            </h1>
            <p className="text-lg lg:text-xl font-bold text-slate-200 font-sans tracking-wide max-w-4xl">
              {caseData.title}
            </p>
          </div>

          {/* Sub-Metadata Row */}
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400 pt-1 border-t border-slate-800/40">
            <div className="flex items-center space-x-1.5">
              <MapPin className="w-3.5 h-3.5 text-cyan-400" />
              <span>{caseData.police_station || caseData.jurisdiction || 'Dwarka Sector 23, New Delhi'}</span>
            </div>
            <span className="text-slate-700">•</span>
            <div className="flex items-center space-x-1.5">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span>Created: {formatDate(caseData.created_at)}</span>
            </div>
            <span className="text-slate-700">•</span>
            <div className="flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-500" />
              <span>Last Activity: {formatDate(caseData.updated_at)}</span>
            </div>
            <span className="text-slate-700">•</span>
            <div className="flex items-center space-x-1.5">
              <Info className="w-3.5 h-3.5 text-slate-500" />
              <span>Case Age: {calculateDuration()}</span>
            </div>
          </div>

          {/* ── 2. DYNAMIC INVESTIGATION METRICS BAR ───────────────────────────────── */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-3">
            <div className="bg-[#0C1220]/80 backdrop-blur-md border border-[#1E293B] p-3 rounded-md shadow-lg hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center space-x-2 text-cyan-400 mb-1">
                <Users className="w-4 h-4" />
                <span className="text-lg font-extrabold font-mono text-white">
                  {entityCounts?.person_count ?? civilians.length ?? 0}
                </span>
              </div>
              <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">People Involved</p>
            </div>

            <div className="bg-[#0C1220]/80 backdrop-blur-md border border-[#1E293B] p-3 rounded-md shadow-lg hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center space-x-2 text-emerald-400 mb-1">
                <Car className="w-4 h-4" />
                <span className="text-lg font-extrabold font-mono text-white">
                  {entityCounts?.vehicle_count ?? 0}
                </span>
              </div>
              <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Vehicles</p>
            </div>

            <div className="bg-[#0C1220]/80 backdrop-blur-md border border-[#1E293B] p-3 rounded-md shadow-lg hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center space-x-2 text-purple-400 mb-1">
                <Smartphone className="w-4 h-4" />
                <span className="text-lg font-extrabold font-mono text-white">
                  {entityCounts?.phone_count !== undefined ? entityCounts.phone_count.toLocaleString() : '0'}
                </span>
              </div>
              <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Phone Numbers</p>
            </div>

            <div className="bg-[#0C1220]/80 backdrop-blur-md border border-[#1E293B] p-3 rounded-md shadow-lg hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center space-x-2 text-amber-400 mb-1">
                <FileText className="w-4 h-4" />
                <span className="text-lg font-extrabold font-mono text-white">
                  {entityCounts?.evidence_count ?? evidenceList.length ?? 0}
                </span>
              </div>
              <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Evidence Items</p>
            </div>

            <div className="bg-[#0C1220]/80 backdrop-blur-md border border-[#1E293B] p-3 rounded-md shadow-lg hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center space-x-2 text-red-400 mb-1">
                <MapPin className="w-4 h-4" />
                <span className="text-lg font-extrabold font-mono text-white">
                  {entityCounts?.location_count ?? 0}
                </span>
              </div>
              <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Event Locations</p>
            </div>

            <div className="bg-[#0C1220]/80 backdrop-blur-md border border-[#1E293B] p-3 rounded-md shadow-lg hover:border-cyan-500/40 transition-colors">
              <div className="flex items-center space-x-2 text-blue-400 mb-1">
                <GitFork className="w-4 h-4" />
                <span className="text-lg font-extrabold font-mono text-white">
                  {leadsList.length ?? 0}
                </span>
              </div>
              <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Leads</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── 3. CASE NAVIGATION TABS (EXACTLY 6 TABS) ────────────────────────────── */}
      <div className="border-b border-[#1E293B] bg-[#0A0E17] sticky top-0 z-30 shadow-md">
        <div className="px-6 flex items-center justify-between max-w-[1700px] mx-auto overflow-x-auto">
          <div className="flex items-center space-x-1">
            {[
              { id: 'OVERVIEW', label: 'Overview', icon: Briefcase },
              { id: 'ENTITIES', label: 'Entities', icon: Users, count: entityCounts ? (entityCounts.person_count + entityCounts.vehicle_count + entityCounts.phone_count) : totalEntityCount },
              { id: 'LEADS', label: 'Leads', icon: Sparkles, count: leadsList.length },
              { id: 'SPATIAL', label: 'Spatial', icon: MapPin },
              { id: 'GRAPH', label: 'Graph', icon: GitFork },
              { id: 'REPORTS', label: 'Reports', icon: FileText },
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
                  className={`px-4 py-3 text-xs font-mono font-semibold flex items-center space-x-2 border-b-2 transition-all whitespace-nowrap cursor-pointer ${
                    isActive
                      ? 'border-cyan-400 text-cyan-300 bg-cyan-950/40 font-bold'
                      : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-900/60'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                  {tab.count !== undefined && tab.count > 0 && (
                    <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                      isActive ? 'bg-cyan-500 text-black' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {tab.count.toLocaleString()}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Right Action Dropdown */}
          <div className="relative py-2">
            <button
              onClick={() => setShowActionsDropdown(!showActionsDropdown)}
              className="bg-[#0C1220] hover:bg-slate-800 border border-[#1E293B] px-3 py-1.5 rounded text-xs font-mono text-slate-300 flex items-center space-x-1.5 transition-colors cursor-pointer"
            >
              <span>Case Actions</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </button>

            {showActionsDropdown && (
              <div className="absolute right-0 mt-2 w-56 bg-[#0C1220] border border-[#1E293B] rounded-md shadow-2xl z-50 py-1 font-mono text-xs text-slate-300 divide-y divide-[#1E293B]">
                <button
                  onClick={() => { setActiveTab('REPORTS'); setShowActionsDropdown(false); }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-800 flex items-center space-x-2"
                >
                  <Printer className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Print Case Dossier</span>
                </button>
                <button
                  onClick={() => { setActiveTab('LEADS'); setShowActionsDropdown(false); }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-800 flex items-center space-x-2"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span>Run C3 Lead Generation</span>
                </button>
                <button
                  onClick={() => { 
                    navigate(`/cases/${caseId}/graph`); 
                    setShowActionsDropdown(false); 
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-slate-800 flex items-center space-x-2"
                >
                  <GitFork className="w-3.5 h-3.5 text-purple-400" />
                  <span>Open Graph Workspace</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── 4. MAIN CONTENT AREA (PROGRESSIVE VERTICAL SCROLL) ──────────────────── */}
      <div className="px-6 pt-6 max-w-[1700px] mx-auto space-y-6">
        {activeTab === 'OVERVIEW' ? (
          <div className="space-y-6">
            {/* ROW 1: People Involved (Top Left 50%) & Key Information (Top Right 50%) */}
            <div className="flex flex-col lg:flex-row gap-6 items-stretch">
              {/* Top Left: People Involved */}
              <div className="w-full lg:w-1/2 bg-[#0C1220] border border-[#1E293B] p-5 rounded-md shadow-xl space-y-4 flex flex-col justify-between">
                <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
                  <div className="flex items-center space-x-2">
                    <Users className="w-4 h-4 text-cyan-400" />
                    <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                      People Involved
                    </h2>
                    <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                      {civilians.length || 8}
                    </span>
                  </div>

                  <button
                    onClick={() => setActiveTab('ENTITIES')}
                    className="text-xs font-mono text-cyan-400 hover:underline flex items-center space-x-1 cursor-pointer"
                  >
                    <span>View All →</span>
                  </button>
                </div>

                {civilians.length === 0 ? (
                  <div className="p-8 text-center bg-[#070A0F] border border-[#1E293B] rounded">
                    <p className="text-xs font-mono text-slate-400 font-bold">NO PEOPLE LINKED</p>
                    <p className="text-[10px] text-slate-500 mt-1">No civilian person entities associated with this case.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {boundedCivilians.map((person, idx) => (
                      <div
                        key={idx}
                        onClick={() => navigate(`/entities/${person.entity_id}`)}
                        className="bg-[#070A0F] border border-[#1E293B] hover:border-cyan-500/50 rounded overflow-hidden cursor-pointer transition-all flex flex-col justify-between group"
                      >
                        <div className="h-28 bg-[#0F172A] flex items-center justify-center border-b border-[#1E293B] relative overflow-hidden">
                          {person.avatar_url ? (
                            <img src={person.avatar_url} alt={person.display_name} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                          ) : (
                            <User className="w-10 h-10 text-slate-600" />
                          )}
                        </div>
                        <div className="p-2.5 space-y-0.5">
                          <h3 className="text-xs font-bold text-white font-sans truncate" title={person.display_name}>
                            {person.display_name}
                          </h3>
                          <span className="text-[9px] font-mono text-amber-400 block font-semibold uppercase">
                            {person.role?.replace(/_/g, ' ') || 'Suspect'}
                          </span>
                        </div>
                      </div>
                    ))}

                    {civilians.length > 4 && (
                      <div
                        onClick={() => setActiveTab('ENTITIES')}
                        className="bg-[#070A0F] border border-[#1E293B] border-dashed hover:border-cyan-400 rounded flex flex-col items-center justify-center p-4 cursor-pointer transition-colors"
                      >
                        <span className="text-sm font-bold text-cyan-400">+{civilians.length - 4}</span>
                        <span className="text-[10px] text-slate-400">More</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Top Right: Divided into 2 Sections (1. Case Summary, 2. Incident Location Map) */}
              <div className="w-full lg:w-1/2 flex flex-col gap-6 justify-between">
                {/* Section 1: Case Summary */}
                <div className="bg-[#0C1220] border border-[#1E293B] p-5 rounded-md shadow-xl space-y-4">
                  <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
                    <div className="flex items-center space-x-2">
                      <Briefcase className="w-4 h-4 text-cyan-400" />
                      <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                        Case Summary
                      </h2>
                    </div>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                      {caseData.status || 'ACTIVE'}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <span className="text-[9px] font-mono font-bold text-slate-400 uppercase tracking-widest block">
                      OPERATIONAL SYNOPSIS
                    </span>
                    <p className="text-xs text-slate-300 font-sans leading-relaxed">
                      {caseData.investigating_unit || 'Armed robbery on a cash van near Dwarka Sector 23, New Delhi. Multiple assailants intercepted the vehicle, looted cash consignments, and fled using a stolen vehicle. The case involves CCTV analysis, telecom data correlation, and inter-state linkages. Investigation is ongoing.'}
                    </p>
                  </div>

                  {/* 6-Grid Metadata Details */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-3 border-t border-[#1E293B] text-xs font-mono">
                    <div>
                      <span className="text-[9px] text-slate-400 uppercase block mb-0.5">Case Type</span>
                      <span className="text-slate-200 font-bold">{caseData.case_type || 'Criminal'}</span>
                    </div>

                    <div>
                      <span className="text-[9px] text-slate-400 uppercase block mb-0.5">Priority</span>
                      <span className="text-red-400 font-bold flex items-center space-x-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" />
                        <span>{caseData.priority || 'Critical'}</span>
                      </span>
                    </div>

                    <div>
                      <span className="text-[9px] text-slate-400 uppercase block mb-0.5">Status</span>
                      <span className="text-emerald-400 font-bold flex items-center space-x-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
                        <span>{caseData.status || 'Active'}</span>
                      </span>
                    </div>

                    <div>
                      <span className="text-[9px] text-slate-400 uppercase block mb-0.5">Investigating Unit</span>
                      <span className="text-slate-200 font-bold truncate block">{caseData.police_station || 'Dwarka PS Crime Branch'}</span>
                    </div>

                    <div>
                      <span className="text-[9px] text-slate-400 uppercase block mb-0.5">Jurisdiction</span>
                      <span className="text-slate-200 font-bold truncate block">{caseData.jurisdiction || 'Dwarka Sector 23 New Delhi'}</span>
                    </div>

                    <div>
                      <span className="text-[9px] text-slate-400 uppercase block mb-0.5">Related FIR</span>
                      <span className="text-slate-200 font-bold truncate block">{caseData.fir_number || 'FIR No. 328/2026 Dwarka PS'}</span>
                    </div>
                  </div>
                </div>

                {/* Section 2: Incident Location Map */}
                <div className="bg-[#0C1220] border border-[#1E293B] p-5 rounded-md shadow-xl space-y-3 flex-1 flex flex-col justify-between">
                  <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
                    <div className="flex items-center space-x-2">
                      <MapPin className="w-4 h-4 text-cyan-400" />
                      <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                        Incident Location Map
                      </h2>
                    </div>

                    <button
                      onClick={() => setActiveTab('SPATIAL')}
                      className="text-xs font-mono text-cyan-400 hover:underline flex items-center space-x-1 cursor-pointer"
                    >
                      <span>Full Spatial Map →</span>
                    </button>
                  </div>

                  {/* Map Canvas & Location Bar */}
                  <div className="space-y-2 flex-1 flex flex-col justify-between">
                    <div className="flex items-center justify-between text-xs font-mono text-slate-300">
                      <span className="text-cyan-300 font-bold flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-red-500 animate-pulse" />
                        <span>{caseData.police_station || caseData.jurisdiction || 'Dwarka Sector 23, New Delhi'}</span>
                      </span>
                      <span className="text-[10px] text-slate-400">Coords: 28.5665° N, 77.0600° E</span>
                    </div>

                    {/* Interactive Tactical Leaflet Map Canvas */}
                    <div className="w-full h-44 rounded border border-[#1E293B] overflow-hidden relative z-0">
                      <MapContainer
                        center={[28.5665, 77.0600]}
                        zoom={13}
                        style={{ width: '100%', height: '100%' }}
                        zoomControl={false}
                        attributionControl={false}
                      >
                        <TileLayer
                          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
                        />
                        <Marker
                          position={[28.5665, 77.0600]}
                          icon={L.divIcon({
                            className: 'civix-incident-pin',
                            html: `
                              <div style="
                                width: 22px;
                                height: 22px;
                                background-color: #ef4444;
                                border: 2px solid #ffffff;
                                border-radius: 50%;
                                box-shadow: 0 0 14px #ef4444;
                                display: flex;
                                items-center: center;
                                justify-content: center;
                              ">
                                <div style="width: 6px; height: 6px; background-color: #ffffff; border-radius: 50%;"></div>
                              </div>
                            `,
                            iconSize: [22, 22],
                            iconAnchor: [11, 11]
                          })}
                        >
                          <Popup className="civix-map-popup">
                            <div className="p-1 font-sans text-xs">
                              <p className="font-bold text-white uppercase">{caseData.case_number}</p>
                              <p className="text-slate-300 text-[10px]">{caseData.title}</p>
                              <p className="text-cyan-400 text-[9px] mt-1">Dwarka Sector 23 Primary Incident Scene</p>
                            </div>
                          </Popup>
                        </Marker>
                      </MapContainer>

                      {/* Map Overlay Indicator */}
                      <div className="absolute top-2 left-2 z-[1000] bg-[#070A0F]/90 border border-[#1E293B] text-[9px] font-mono text-cyan-300 px-2 py-0.5 rounded shadow">
                        INCIDENT SCENE PREVIEW
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* ROW 2: Officers (Bottom Left 50%) & Timeline (Bottom Right 50%) */}
            <div className="flex flex-col lg:flex-row gap-6 items-stretch">
              {/* Bottom Left: Officers */}
              <div className="w-full lg:w-1/2 bg-[#0C1220] border border-[#1E293B] p-5 rounded-md shadow-xl space-y-4 flex flex-col justify-between">
                <div className="flex items-center justify-between border-b border-[#1E293B] pb-3">
                  <div className="flex items-center space-x-2">
                    <Shield className="w-4 h-4 text-cyan-400" />
                    <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                      Officers
                    </h2>
                    <span className="text-[10px] font-mono text-cyan-300 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                      {officers.length || 6}
                    </span>
                  </div>

                  <button
                    onClick={() => setActiveTab('ENTITIES')}
                    className="text-xs font-mono text-cyan-400 hover:underline flex items-center space-x-1 cursor-pointer"
                  >
                    <span>View All →</span>
                  </button>
                </div>

                {officers.length === 0 ? (
                  <div className="p-8 text-center bg-[#070A0F] border border-[#1E293B] rounded">
                    <p className="text-xs font-mono text-slate-400 font-bold">NO OFFICERS ASSIGNED</p>
                    <p className="text-[10px] text-slate-500 mt-1">No police personnel records linked to this case.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {boundedOfficers.map((officer, idx) => (
                      <div
                        key={idx}
                        className="bg-[#070A0F] border border-[#1E293B] rounded overflow-hidden flex flex-col justify-between"
                      >
                        <div className="h-28 bg-[#0F172A] flex items-center justify-center border-b border-[#1E293B] relative overflow-hidden">
                          {officer.avatar_url ? (
                            <img src={officer.avatar_url} alt={officer.display_name} className="w-full h-full object-cover" />
                          ) : (
                            <User className="w-10 h-10 text-cyan-500/60" />
                          )}
                          <div className="absolute top-1.5 right-1.5 bg-blue-950/90 text-cyan-300 border border-blue-800/60 text-[8px] font-bold px-1.5 py-0.2 rounded">
                            POLICE
                          </div>
                        </div>
                        <div className="p-2.5 space-y-0.5">
                          <h3 className="text-xs font-bold text-white font-sans truncate" title={officer.display_name}>
                            {officer.display_name}
                          </h3>
                          <span className="text-[9px] font-mono text-cyan-400 block font-semibold uppercase truncate">
                            {officer.role?.replace(/_/g, ' ') || 'Investigating Officer'}
                          </span>
                        </div>
                      </div>
                    ))}

                    {officers.length > 3 && (
                      <div
                        onClick={() => setActiveTab('ENTITIES')}
                        className="bg-[#070A0F] border border-[#1E293B] border-dashed hover:border-cyan-400 rounded flex flex-col items-center justify-center p-4 cursor-pointer transition-colors"
                      >
                        <span className="text-sm font-bold text-cyan-400">+{officers.length - 3}</span>
                        <span className="text-[10px] text-slate-400">More</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Bottom Right: Timeline */}
              <div className="w-full lg:w-1/2 bg-[#0C1220] border border-[#1E293B] p-5 rounded-md shadow-xl flex flex-col justify-between space-y-4">
                <div className="flex items-center space-x-2 border-b border-[#1E293B] pb-3">
                  <Calendar className="w-4 h-4 text-cyan-400" />
                  <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                    Timeline
                  </h2>
                </div>

                {/* Vertical Timeline Activity */}
                <div className="space-y-4 py-2 font-mono">
                  <div className="flex items-start space-x-3">
                    <div className="flex flex-col items-center">
                      <span className="w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_8px_#38bdf8]" />
                      <span className="w-0.5 h-10 bg-slate-800" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-white block">{formatDate(caseData.created_at)}</span>
                      <span className="text-[10px] text-slate-400 font-sans">Case Created</span>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="flex flex-col items-center">
                      <span className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_8px_#3b82f6]" />
                      <span className="w-0.5 h-10 bg-slate-800" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-white block">{formatDate(caseData.updated_at)}</span>
                      <span className="text-[10px] text-slate-400 font-sans">Last Activity</span>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3">
                    <div className="flex flex-col items-center">
                      <span className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-emerald-400 block">Ongoing</span>
                      <span className="text-[10px] text-slate-400 font-sans">Investigation Status</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : activeTab === 'ENTITIES' ? (
          <div className="py-4">
            <CaseEntityRegistry caseId={caseId || ''} />
          </div>
        ) : activeTab === 'LEADS' ? (
          <CaseLeadsView caseId={caseId || ''} />
        ) : activeTab === 'SPATIAL' ? (
          <SpatialIntelligencePage />
        ) : activeTab === 'GRAPH' ? (
          <div className="p-12 text-center bg-[#0C1220] border border-[#1E293B] rounded-md space-y-4 max-w-xl mx-auto my-12">
            <GitFork className="w-12 h-12 text-purple-400 mx-auto animate-pulse" />
            <div>
              <h3 className="text-sm font-bold text-white font-mono uppercase">Dedicated Graph Workspace</h3>
              <p className="text-xs text-slate-400 mt-1 font-sans leading-relaxed">
                Investigative Graph Analysis operates in a dedicated full-screen workspace with unencumbered topology controls, Cytoscape canvas, node dossier inspector, and ML intelligence context.
              </p>
            </div>
            <button
              onClick={() => navigate(`/cases/${caseId}/graph`)}
              className="civix-btn-primary inline-flex items-center space-x-2 cursor-pointer"
            >
              <GitFork className="w-4 h-4" />
              <span>Launch Standalone Graph Workspace</span>
            </button>
          </div>
        ) : activeTab === 'REPORTS' ? (
          <CaseReportsView caseId={caseId || ''} caseData={caseData} />
        ) : null}
      </div>
    </div>
  );
};
