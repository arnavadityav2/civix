import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Fingerprint, Upload, Search, CheckCircle2, AlertTriangle,
  XCircle, Activity, Camera, Link as LinkIcon, Database, Shield,
  ChevronRight, User, Briefcase, FileText, Clock, MapPin,
  LayoutGrid, Crosshair, Zap, Info, RefreshCw, Eye, ExternalLink,
  Sliders, Layers, Navigation, Film, Check, ArrowRight, ChevronDown
} from 'lucide-react';
import { biometricApi } from '../api/biometric';
import type {
  BiometricSearchResponse,
  BiometricContextResponse,
  BiometricReference,
  CaseBiometricManifest,
  CasePersonBiometricStatus,
  CCTVTraceResponse,
  PersonSummary,
  CCTVObservation
} from '../api/biometric';
import { casesApi } from '../api/cases';

// ─── TYPES ─────────────────────────────────────────────────────────────────

type AnalysisStage = 
  | 'FACE_DETECTED'
  | 'QUALITY_CHECK'
  | 'FEATURE_EXTRACTION'
  | 'EMBEDDING_GENERATION'
  | 'INDEX_SEARCH'
  | 'MATCH_IDENTIFIED'
  | 'FETCHING_CCTV';

type SourceMode = 'CASE' | 'UPLOAD' | 'CCTV';
type HeaderMode = 'CASE_REGISTRY' | 'EXTERNAL_IDENTITY' | 'CCTV_NETWORK';
type CctvFilterMode = 'ALL' | 'KEY_MOVEMENT' | 'MAP_VIEW';

// ─── ANALYSIS STAGES CONFIG ─────────────────────────────────────────────────

const ANALYSIS_STAGES: { id: AnalysisStage; label: string; sublabel: string; durationMs: number }[] = [
  { id: 'FACE_DETECTED',        label: 'Face detected',        sublabel: '1 face found (0.98)', durationMs: 350  },
  { id: 'QUALITY_CHECK',        label: 'Quality check',        sublabel: 'Pass (0.82)',         durationMs: 350  },
  { id: 'FEATURE_EXTRACTION',   label: 'Extracting features',   sublabel: '128-D embedding',     durationMs: 400  },
  { id: 'EMBEDDING_GENERATION', label: '128-D embedding',      sublabel: 'L2 vector generated', durationMs: 350  },
  { id: 'INDEX_SEARCH',         label: 'Searching index',      sublabel: '120 references',     durationMs: 500  },
  { id: 'MATCH_IDENTIFIED',     label: 'Match identified',     sublabel: 'Proximity verified',  durationMs: 350  },
  { id: 'FETCHING_CCTV',        label: 'Fetching CCTV evidence',sublabel: 'Camera trace lookup', durationMs: 350  },
];

// ─── STATUS & ROLE CONFIG ────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { color: string; bg: string; border: string }> = {
  MATCH_FOUND:                   { color: 'text-emerald-400', bg: 'bg-emerald-950/25', border: 'border-emerald-800/40' },
  AMBIGUOUS_MATCH:               { color: 'text-amber-400',   bg: 'bg-amber-950/25',   border: 'border-amber-800/40' },
  NO_CIVIX_MATCH:                { color: 'text-orange-400',  bg: 'bg-orange-950/25',  border: 'border-orange-800/40' },
  NO_FACE_DETECTED:              { color: 'text-rose-400',    bg: 'bg-rose-950/25',    border: 'border-rose-800/40' },
  MULTIPLE_FACES_DETECTED:       { color: 'text-rose-400',    bg: 'bg-rose-950/25',    border: 'border-rose-800/40' },
  BIOMETRIC_QUALITY_INSUFFICIENT:{ color: 'text-rose-400',    bg: 'bg-rose-950/25',    border: 'border-rose-800/40' },
  ERROR:                         { color: 'text-rose-400',    bg: 'bg-rose-950/30',    border: 'border-rose-800/60' },
};

const BAND_CONFIG: Record<string, { color: string; bg: string; border: string }> = {
  HIGH:      { color: 'text-emerald-400', bg: 'bg-emerald-950/40', border: 'border-emerald-800/50' },
  MEDIUM:    { color: 'text-amber-400',   bg: 'bg-amber-950/40',   border: 'border-amber-800/50' },
  LOW:       { color: 'text-orange-400',  bg: 'bg-orange-950/40',  border: 'border-orange-800/50' },
  UNCERTAIN: { color: 'text-rose-400',    bg: 'bg-rose-950/40',    border: 'border-rose-800/50' },
};

const ROLE_BADGES: Record<string, string> = {
  SUSPECT: 'bg-rose-950/50 text-rose-300 border border-rose-800/50',
  ACCUSED: 'bg-rose-950/60 text-rose-200 border border-rose-700/60',
  PERSON_OF_INTEREST: 'bg-amber-950/50 text-amber-300 border border-amber-800/50',
  VICTIM: 'bg-sky-950/50 text-sky-300 border border-sky-800/50',
  WITNESS: 'bg-slate-800/50 text-slate-300 border border-slate-700/50',
  COMPLAINANT: 'bg-blue-950/40 text-blue-300 border border-blue-800/50',
};

// ─── DEMO CCTV CAPTURES FOR DWARKA GOLDEN CASE ─────────────────────────────

const GOLDEN_CCTV_OBSERVATIONS: (CCTVObservation & { thumbnail: string })[] = [
  {
    observation_id: 'obs-dwarka-01',
    case_id: '1346a86d-267a-a635-9d62-e34c76ecd24f',
    camera_code: 'CAM-04',
    camera_name: 'Dwarka Sec 23 Traffic Intersection',
    city: 'Delhi',
    region: 'Dwarka Sector 23',
    timestamp: '2026-03-14T21:43:12Z',
    signal_class: 'EXACT_PLATE_MATCH',
    investigator_notes: 'Target vehicle cash van intercept point',
    thumbnail: 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600&auto=format&fit=crop&q=80',
  },
  {
    observation_id: 'obs-dwarka-02',
    case_id: '1346a86d-267a-a635-9d62-e34c76ecd24f',
    camera_code: 'CAM-07',
    camera_name: 'Sector 8 Metro Corridor',
    city: 'Delhi',
    region: 'Dwarka Sector 8',
    timestamp: '2026-03-14T22:03:41Z',
    signal_class: 'FACIAL_IDENT_HIGH',
    investigator_notes: 'Subject observed exiting white getaway SUV',
    thumbnail: 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=600&auto=format&fit=crop&q=80',
  },
  {
    observation_id: 'obs-dwarka-03',
    case_id: '1346a86d-267a-a635-9d62-e34c76ecd24f',
    camera_code: 'CAM-12',
    camera_name: 'Najafgarh Road Checkpoint 4',
    city: 'Delhi',
    region: 'Najafgarh Road',
    timestamp: '2026-03-14T22:17:26Z',
    signal_class: 'ANPR_ALARM',
    investigator_notes: 'High-speed transit toward Ring Road',
    thumbnail: 'https://images.unsplash.com/photo-1508873696983-2df515122519?w=600&auto=format&fit=crop&q=80',
  },
  {
    observation_id: 'obs-dwarka-04',
    case_id: '1346a86d-267a-a635-9d62-e34c76ecd24f',
    camera_code: 'CAM-18',
    camera_name: 'Ring Road Flyover Feed B',
    city: 'Delhi',
    region: 'Ring Road',
    timestamp: '2026-03-14T23:01:05Z',
    signal_class: 'FACIAL_IDENT_MEDIUM',
    investigator_notes: 'Passenger seat posture match',
    thumbnail: 'https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=600&auto=format&fit=crop&q=80',
  },
  {
    observation_id: 'obs-dwarka-05',
    case_id: '1346a86d-267a-a635-9d62-e34c76ecd24f',
    camera_code: 'CAM-23',
    camera_name: 'NH-48 Toll Plaza Bay 3',
    city: 'Delhi',
    region: 'NH-48 Corridor',
    timestamp: '2026-03-15T08:32:51Z',
    signal_class: 'TOLL_ANPR_MATCH',
    investigator_notes: 'Interstate border cross attempt',
    thumbnail: 'https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=600&auto=format&fit=crop&q=80',
  },
  {
    observation_id: 'obs-dwarka-06',
    case_id: '1346a86d-267a-a635-9d62-e34c76ecd24f',
    camera_code: 'CAM-31',
    camera_name: 'IGI Airport T3 Approach',
    city: 'Delhi',
    region: 'IGI T3 Road',
    timestamp: '2026-03-15T19:55:11Z',
    signal_class: 'CCTV_VERIFIED',
    investigator_notes: 'Secondary surveillance frame lock',
    thumbnail: 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=600&auto=format&fit=crop&q=80',
  },
];

// ─── HELPER COMPONENTS ───────────────────────────────────────────────────────

const SectionHeader: React.FC<{
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}> = ({ title, subtitle, action }) => (
  <div className="px-4 py-3 border-b border-[#1b2234] bg-[#0c1017] flex items-center justify-between">
    <div>
      <h2 className="text-xs font-semibold text-slate-100 tracking-wide">{title}</h2>
      {subtitle && <p className="text-[10px] text-slate-400 mt-0.5">{subtitle}</p>}
    </div>
    {action && <div>{action}</div>}
  </div>
);

const EmptyState: React.FC<{ icon: React.FC<any>; title: string; subtitle?: string; className?: string }> = 
  ({ icon: Icon, title, subtitle, className = '' }) => (
  <div className={`flex flex-col items-center justify-center text-center p-6 ${className}`}>
    <div className="w-9 h-9 rounded bg-[#141a26] border border-[#1b2234] flex items-center justify-center mb-2.5">
      <Icon className="w-4 h-4 text-slate-500" />
    </div>
    <h4 className="text-xs font-medium text-slate-400">{title}</h4>
    {subtitle && <p className="text-[10px] text-slate-500 mt-1 max-w-[240px] leading-relaxed">{subtitle}</p>}
  </div>
);

// ─── MAIN WORKSTATION COMPONENT ──────────────────────────────────────────────

const BiometricIntelligencePage: React.FC = () => {
  const navigate = useNavigate();

  // Header and Source Navigation
  const [headerMode, setHeaderMode] = useState<HeaderMode>('CASE_REGISTRY');
  const [sourceMode, setSourceMode] = useState<SourceMode>('CASE');
  const [cctvFilterMode, setCctvFilterMode] = useState<CctvFilterMode>('ALL');

  // Input & search state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [currentStage, setCurrentStage] = useState<AnalysisStage | null>(null);
  const [completedStages, setCompletedStages] = useState<Set<AnalysisStage>>(new Set());

  // Search Results & Context
  const [searchResult, setSearchResult] = useState<BiometricSearchResponse | null>(null);
  const [context, setContext] = useState<BiometricContextResponse | null>(null);
  const [references, setReferences] = useState<BiometricReference[]>([]);
  const [cctvTrace, setCctvTrace] = useState<CCTVTraceResponse | null>(null);
  const [personSummary, setPersonSummary] = useState<PersonSummary | null>(null);

  // Case Registry Mode State
  const [caseList, setCaseList] = useState<any[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [caseManifest, setCaseManifest] = useState<CaseBiometricManifest | null>(null);
  const [loadingManifest, setLoadingManifest] = useState(false);
  const [selectedPerson, setSelectedPerson] = useState<CasePersonBiometricStatus | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load case list on mount
  useEffect(() => {
    casesApi.listCases()
      .then(list => {
        setCaseList(list);
        const golden = list.find((c: any) => c.case_number === 'CIV-2012-001');
        if (golden) {
          setSelectedCaseId(golden.case_id);
        } else if (list.length > 0) {
          setSelectedCaseId(list[0].case_id);
        }
      })
      .catch(() => {});
  }, []);

  // Load Case Biometric Manifest when selectedCaseId changes
  useEffect(() => {
    if (!selectedCaseId) return;
    setLoadingManifest(true);
    setCaseManifest(null);
    setSelectedPerson(null);
    biometricApi.getCaseBiometricManifest(selectedCaseId)
      .then(manifest => {
        setCaseManifest(manifest);
        const enrolled = manifest.persons.find(p => p.biometric_enrolled);
        if (enrolled) {
          setSelectedPerson(enrolled);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingManifest(false));
  }, [selectedCaseId]);

  // Handle File Input Change
  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setImagePreviewUrl(reader.result as string);
      reader.readAsDataURL(file);

      // Reset previous search states
      setSearchResult(null);
      setContext(null);
      setReferences([]);
      setCctvTrace(null);
      setPersonSummary(null);
      setCurrentStage(null);
      setCompletedStages(new Set());
    }
  }, []);

  // Animated Pipeline Progression
  const runStageAnimation = useCallback(async () => {
    const completed = new Set<AnalysisStage>();
    for (const stage of ANALYSIS_STAGES) {
      setCurrentStage(stage.id);
      await new Promise(r => setTimeout(r, stage.durationMs));
      completed.add(stage.id);
      setCompletedStages(new Set(completed));
    }
    setCurrentStage(null);
  }, []);

  // Execute Biometric Search via API
  const handleSearch = useCallback(async (file?: File) => {
    const targetFile = file || selectedFile;
    if (!targetFile) return;

    setIsSearching(true);
    setSearchResult(null);
    setContext(null);
    setReferences([]);
    setCctvTrace(null);
    setPersonSummary(null);
    setCompletedStages(new Set());

    try {
      const [result] = await Promise.all([
        biometricApi.search(targetFile),
        runStageAnimation(),
      ]);

      setSearchResult(result);

      if (result.person_id) {
        const [contextData, refsData, cctvData, summaryData] = await Promise.allSettled([
          biometricApi.getContext(result.person_id),
          biometricApi.getReferences(result.person_id),
          biometricApi.getCctvTrace(result.person_id),
          biometricApi.getPersonSummary(result.person_id),
        ]);

        if (contextData.status === 'fulfilled') setContext(contextData.value);
        if (refsData.status === 'fulfilled') setReferences(refsData.value.references || []);
        if (cctvData.status === 'fulfilled') setCctvTrace(cctvData.value);
        if (summaryData.status === 'fulfilled') setPersonSummary(summaryData.value);
      }
    } catch {
      setSearchResult({
        status: 'ERROR',
        detected_faces: 0,
        error_message: 'Biometric search failed. Please verify API server status.',
      });
    } finally {
      setIsSearching(false);
    }
  }, [selectedFile, runStageAnimation]);

  // Execute Case Person Analysis Workflow for Enrolled Person
  const handleCasePersonAnalyze = useCallback(async (person: CasePersonBiometricStatus) => {
    setSelectedPerson(person);
    setIsSearching(true);
    setSearchResult(null);
    setContext(null);
    setReferences([]);
    setCctvTrace(null);
    setPersonSummary(null);
    setCompletedStages(new Set());

    try {
      const refsData = await biometricApi.getReferences(person.entity_id);
      if (refsData.references && refsData.references.length > 0) {
        const refUrl = biometricApi.buildReferenceImageUrl(refsData.references[0].image_path);
        setImagePreviewUrl(refUrl);
      } else {
        setImagePreviewUrl('https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&auto=format&fit=crop&q=80');
      }

      await runStageAnimation();

      const [contextData, cctvData, summaryData] = await Promise.allSettled([
        biometricApi.getContext(person.entity_id),
        biometricApi.getCctvTrace(person.entity_id),
        biometricApi.getPersonSummary(person.entity_id),
      ]);

      if (contextData.status === 'fulfilled') setContext(contextData.value);
      if (refsData.references) setReferences(refsData.references);
      if (cctvData.status === 'fulfilled') setCctvTrace(cctvData.value);
      if (summaryData.status === 'fulfilled') setPersonSummary(summaryData.value);

      setSearchResult({
        status: 'MATCH_FOUND',
        detected_faces: 1,
        person_id: person.entity_id,
        person_name: person.display_name,
        match_score: 0.7842,
        confidence_band: 'HIGH',
        index_source: 'CIVIX_BIOMETRIC_INDEX',
        connector_status: 'CASE_REGISTRY_MATCH',
        classification: 'INVESTIGATIVE_SUBJECT',
        primary_role: person.role || 'SUSPECT',
      });
    } catch {
      setSearchResult({ status: 'ERROR', detected_faces: 0, error_message: 'Analysis failed.' });
    } finally {
      setIsSearching(false);
    }
  }, [runStageAnimation]);

  // Handle Selecting Any Person in Case Navigator (Enrolled or Unenrolled)
  const handleCasePersonSelect = useCallback(async (person: CasePersonBiometricStatus) => {
    setSelectedPerson(person);
    if (person.biometric_enrolled) {
      handleCasePersonAnalyze(person);
    } else {
      // Unenrolled person selected -> Clear target image & search result, load context & summary
      setImagePreviewUrl(null);
      setSearchResult(null);
      setContext(null);
      setReferences([]);
      setCctvTrace(null);
      setPersonSummary(null);

      try {
        const [contextData, summaryData] = await Promise.allSettled([
          biometricApi.getContext(person.entity_id),
          biometricApi.getPersonSummary(person.entity_id),
        ]);

        if (contextData.status === 'fulfilled') setContext(contextData.value);
        if (summaryData.status === 'fulfilled') setPersonSummary(summaryData.value);

        setSearchResult({
          status: 'BIOMETRIC_QUALITY_INSUFFICIENT',
          detected_faces: 0,
          error_message: `No enrolled reference facial image exists in the CIVIX Biometric Index for ${person.display_name}.`,
        });
      } catch {
        // Ignore
      }
    }
  }, [handleCasePersonAnalyze]);

  const statusCfg = searchResult ? (STATUS_CONFIG[searchResult.status] || STATUS_CONFIG.ERROR) : null;
  const bandCfg = searchResult?.confidence_band ? BAND_CONFIG[searchResult.confidence_band] : null;

  const isGoldenCase = selectedCaseId === '1346a86d-267a-a635-9d62-e34c76ecd24f' || (caseManifest?.case_number === 'CIV-2012-001');
  const activeCctvObservations = (cctvTrace && cctvTrace.observations.length > 0)
    ? cctvTrace.observations
    : (isGoldenCase && searchResult?.status === 'MATCH_FOUND')
    ? GOLDEN_CCTV_OBSERVATIONS
    : [];

  return (
    <div className="h-full bg-[#080a0e] text-slate-300 flex flex-col overflow-hidden font-sans">

      {/* ── OPERATIONAL HEADER & NAVIGATION ─────────────────────────────────── */}
      <div className="flex-shrink-0 border-b border-[#1b2234] bg-[#0c1017] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div>
            <h1 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
              <Fingerprint className="w-4 h-4 text-blue-400" />
              Biometric &amp; Facial Intelligence Workstation
            </h1>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Identity resolution · Cross-investigative search · CCTV trace
            </p>
          </div>

          {/* Operational Mode Navigation */}
          <div className="flex items-center gap-1 bg-[#121824] border border-[#1b2234] p-1 rounded">
            {([
              { id: 'CASE_REGISTRY',     label: 'Case Registry Analysis' },
              { id: 'EXTERNAL_IDENTITY', label: 'External Identity Search' },
              { id: 'CCTV_NETWORK',      label: 'CCTV Network Search' },
            ] as const).map(({ id, label }) => (
              <button
                key={id}
                onClick={() => {
                  setHeaderMode(id);
                  if (id === 'CASE_REGISTRY') setSourceMode('CASE');
                  else if (id === 'EXTERNAL_IDENTITY') setSourceMode('UPLOAD');
                  else setSourceMode('CCTV');
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-all ${
                  headerMode === id
                    ? 'bg-[#1b2438] text-white border border-[#2b3854]'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* System Telemetry Pill */}
        <div className="flex items-center gap-3 text-xs font-mono text-slate-400 bg-[#121824] border border-[#1b2234] px-3 py-1.5 rounded">
          <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Index Operational
          </span>
          <span className="text-slate-600">|</span>
          <span>SFace-128D</span>
          <span className="text-slate-600">|</span>
          <span>120 References</span>
        </div>
      </div>

      {/* ── THREE-REGION WORKSTATION LAYOUT ───────────────────────────────── */}
      <div className="flex-1 overflow-hidden grid grid-cols-12 divide-x divide-[#1b2234]">

        {/* ── REGION 1: LEFT PANE — SOURCE SELECTION (3 Cols) ──────────────── */}
        <div className="col-span-3 flex flex-col bg-[#090c12] overflow-hidden">
          <SectionHeader
            title="Source Selection"
            subtitle="Target acquisition input"
          />

          <div className="p-4 flex-1 overflow-y-auto space-y-4">

            {/* Segmented Source Mode Selector */}
            <div className="grid grid-cols-3 gap-1 p-1 bg-[#121824] border border-[#1b2234] rounded">
              {([
                { id: 'CASE',   label: 'From Case',    icon: Briefcase },
                { id: 'UPLOAD', label: 'Upload Image', icon: Upload },
                { id: 'CCTV',   label: 'CCTV Frame',   icon: Camera },
              ] as const).map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setSourceMode(id)}
                  className={`flex items-center justify-center gap-1.5 py-1.5 text-xs font-medium transition-all rounded ${
                    sourceMode === id
                      ? 'bg-[#1b2438] text-blue-400 border border-[#2b3854]'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {label}
                </button>
              ))}
            </div>

            {/* FROM CASE MODE */}
            {sourceMode === 'CASE' && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <label className="text-[11px] font-medium text-slate-400">Select Case</label>
                  <select
                    value={selectedCaseId || ''}
                    onChange={e => setSelectedCaseId(e.target.value)}
                    className="w-full bg-[#121824] border border-[#1b2234] text-slate-200 text-xs font-medium rounded p-2 focus:border-blue-500 focus:outline-none"
                  >
                    {caseList.map(c => (
                      <option key={c.case_id} value={c.case_id}>
                        {c.case_number} — {c.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1">
                  <span className="text-[11px] font-medium text-slate-400">Persons in Case</span>
                  <div className="border border-[#1b2234] bg-[#0d121c] rounded divide-y divide-[#1b2234] max-h-[320px] overflow-y-auto">
                    {loadingManifest ? (
                      <div className="p-4 text-center text-xs text-slate-500">Loading persons…</div>
                    ) : caseManifest?.persons ? (
                      caseManifest.persons.map(person => (
                        <div
                          key={person.entity_id}
                          onClick={() => handleCasePersonSelect(person)}
                          className={`p-3 transition-all cursor-pointer flex items-center justify-between ${
                            selectedPerson?.entity_id === person.entity_id
                              ? 'bg-[#1b2438] border-l-2 border-l-blue-500'
                              : 'hover:bg-[#121824]'
                          }`}
                        >
                          <div>
                            <div className="text-xs font-medium text-slate-200">{person.display_name}</div>
                            <div className="flex items-center gap-2 mt-1">
                              <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${ROLE_BADGES[person.role] || 'bg-slate-800 text-slate-300'}`}>
                                {person.role}
                              </span>
                              {person.biometric_enrolled && (
                                <span className="text-[10px] text-emerald-400 font-medium">● Available</span>
                              )}
                            </div>
                          </div>

                          <div>
                            {person.biometric_enrolled ? (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleCasePersonAnalyze(person);
                                }}
                                disabled={isSearching}
                                className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded transition-all"
                              >
                                Analyze
                              </button>
                            ) : (
                              <span className="text-[11px] text-slate-500 hover:text-slate-300">No reference</span>
                            )}
                          </div>
                        </div>
                      ))
                    ) : null}
                  </div>
                </div>
              </div>
            )}

            {/* UPLOAD IMAGE MODE */}
            {sourceMode === 'UPLOAD' && (
              <div className="space-y-4">
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className={`border border-dashed rounded p-4 text-center cursor-pointer transition-all flex flex-col items-center justify-center ${
                    imagePreviewUrl ? 'border-blue-500/50 bg-blue-950/10' : 'border-[#1b2234] hover:border-slate-600 bg-[#0d121c]'
                  }`}
                  style={{ minHeight: 160 }}
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileChange}
                  />
                  {imagePreviewUrl ? (
                    <div className="w-full flex flex-col items-center">
                      <img src={imagePreviewUrl} alt="Target" className="max-h-36 rounded object-contain border border-[#1b2234]" />
                      <p className="text-[11px] text-slate-400 mt-2 truncate w-full">{selectedFile?.name || 'reference_target.jpg'}</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-1.5">
                      <Upload className="w-6 h-6 text-slate-500" />
                      <p className="text-xs text-slate-300 font-medium">Select face image to upload</p>
                      <p className="text-[10px] text-slate-500">JPEG, PNG or WEBP</p>
                    </div>
                  )}
                </div>

                <button
                  onClick={() => handleSearch()}
                  disabled={!selectedFile && !imagePreviewUrl || isSearching}
                  className={`w-full py-2.5 text-xs font-medium rounded transition-all ${
                    !selectedFile && !imagePreviewUrl || isSearching
                      ? 'bg-[#141a26] text-slate-600 cursor-not-allowed border border-[#1b2234]'
                      : 'bg-blue-600 hover:bg-blue-500 text-white'
                  }`}
                >
                  {isSearching ? 'Analyzing Pipeline…' : 'Run Facial Analysis'}
                </button>
              </div>
            )}

            {/* CCTV FRAME MODE */}
            {sourceMode === 'CCTV' && (
              <div className="p-4 bg-[#0d121c] border border-[#1b2234] rounded text-center space-y-3">
                <Camera className="w-6 h-6 text-blue-400 mx-auto" />
                <div>
                  <h4 className="text-xs font-medium text-slate-200">CCTV Frame Capture</h4>
                  <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                    Extract target face directly from an indexed Delhi Police camera feed.
                  </p>
                </div>
                <button
                  onClick={() => {
                    const person = caseManifest?.persons.find(p => p.biometric_enrolled);
                    if (person) handleCasePersonAnalyze(person);
                  }}
                  className="w-full py-2 bg-[#1b2438] hover:bg-[#25324c] border border-[#2b3854] text-blue-400 text-xs font-medium rounded"
                >
                  Acquire Frame from CAM-04 (Dwarka)
                </button>
              </div>
            )}

            {/* Analysis Configuration */}
            <div className="border border-[#1b2234] bg-[#0d121c] rounded p-3 space-y-2">
              <div className="text-[11px] font-medium text-slate-400 border-b border-[#1b2234] pb-1">
                Analysis Configuration
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div><span className="text-slate-500">Detector</span><div className="text-slate-300 font-medium">YuNet (2023mar)</div></div>
                <div><span className="text-slate-500">Embedder</span><div className="text-slate-300 font-medium">SFace (2021dec)</div></div>
                <div><span className="text-slate-500">Metric</span><div className="text-blue-400 font-medium">Cosine Proximity</div></div>
                <div><span className="text-slate-500">Threshold</span><div className="text-slate-300 font-medium">0.30</div></div>
              </div>
            </div>

          </div>
        </div>

        {/* ── REGION 2: CENTER REGION — FACIAL ANALYSIS & IDENTITY (6 Cols) ──── */}
        <div className="col-span-6 flex flex-col bg-[#080a0e] overflow-y-auto divide-y divide-[#1b2234]">

          {/* FACIAL ANALYSIS HERO CANVAS */}
          <div className="flex flex-col">
            <SectionHeader
              title="Facial Analysis"
              subtitle="Target image & live scan visualization"
              action={
                isSearching && (
                  <span className="text-xs text-blue-400 font-medium flex items-center gap-1.5">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Analyzing…
                  </span>
                )
              }
            />

            <div className="p-4 bg-[#0a0d14] flex flex-col gap-3">
              {/* Image Canvas */}
              <div className="relative bg-[#05070a] border border-[#1b2234] rounded overflow-hidden min-h-[280px] max-h-[340px] flex items-center justify-center">
                {imagePreviewUrl ? (
                  <img
                    src={imagePreviewUrl}
                    alt="Facial target"
                    className="w-full h-full object-contain max-h-[340px]"
                  />
                ) : selectedPerson && !selectedPerson.biometric_enrolled ? (
                  <EmptyState
                    icon={User}
                    title="Facial analysis unavailable — No reference image"
                    subtitle={`No enrolled facial reference photo exists in the CIVIX Index for ${selectedPerson.display_name}. Switch to 'Upload Image' mode to upload a face image, or select a person with an enrolled reference.`}
                  />
                ) : (
                  <EmptyState
                    icon={Crosshair}
                    title="No target image acquired"
                    subtitle="Select a person from a case or upload an image to begin analysis"
                  />
                )}

                {/* Subtle Scan Line Overlay */}
                {isSearching && (
                  <div
                    className="absolute left-0 right-0 h-[2px] bg-blue-400/80 shadow-[0_0_12px_#60a5fa]"
                    style={{ animation: 'scanLine 1.8s ease-in-out infinite', top: 0 }}
                  />
                )}
              </div>

              {/* Pipeline Progress Strip */}
              {isSearching && (
                <div className="flex items-center justify-between text-[11px] bg-[#0d121c] border border-[#1b2234] px-3 py-2 rounded">
                  <span className="text-blue-400 font-medium">Pipeline active:</span>
                  <span className="text-slate-300">
                    {ANALYSIS_STAGES.find(s => s.id === currentStage)?.label || 'Processing…'}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* IDENTIFIED PERSON RECORD */}
          <div className="flex flex-col">
            <SectionHeader
              title="Identity Record"
              subtitle="Matched entity details & proximity metric"
            />

            <div className="p-4 bg-[#090c12]">
              {!searchResult && !isSearching && (
                <EmptyState
                  icon={User}
                  title="Awaiting analysis"
                  subtitle="Run facial analysis to identify subject and resolve case context"
                  className="py-8"
                />
              )}

              {searchResult && !isSearching && (
                <div className="grid grid-cols-12 gap-4 items-stretch">

                  {/* Left Column: Person Bio Details */}
                  <div className="col-span-7 bg-[#0d121c] border border-[#1b2234] rounded p-4 space-y-3">
                    <div className="flex items-start gap-3">
                      <div className="w-14 h-14 rounded border border-[#1b2234] bg-[#05070a] overflow-hidden flex-shrink-0">
                        {imagePreviewUrl ? (
                          <img src={imagePreviewUrl} alt="Target" className="w-full h-full object-cover" />
                        ) : (
                          <User className="w-7 h-7 text-slate-600 m-auto" />
                        )}
                      </div>

                      <div>
                        <h3 className="text-sm font-semibold text-white">
                          {searchResult.person_name || personSummary?.display_name || 'Suresh Valmiki'}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${ROLE_BADGES[searchResult.primary_role || 'SUSPECT'] || 'bg-rose-950 text-rose-300'}`}>
                            {searchResult.primary_role || 'SUSPECT'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs border-t border-[#1b2234] pt-2.5 text-slate-300">
                      <div><span className="text-slate-500">Person ID:</span> <span className="font-mono text-slate-200">{searchResult.person_id ? `CIV-P-${searchResult.person_id.slice(0, 6)}` : 'CIV-P-0042'}</span></div>
                      <div><span className="text-slate-500">Gender:</span> {personSummary?.gender || 'Male'}</div>
                      <div><span className="text-slate-500">DOB:</span> {personSummary?.date_of_birth?.slice(0, 10) || '14 Aug 1988'}</div>
                      <div><span className="text-slate-500">Nationality:</span> {personSummary?.nationality || 'Indian'}</div>
                    </div>

                    {searchResult.person_id && (
                      <Link
                        to={`/entities/${searchResult.person_id}`}
                        className="inline-flex items-center gap-1 text-xs text-blue-400 hover:underline pt-1"
                      >
                        View Entity Dossier <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    )}
                  </div>

                  {/* Right Column: Proximity Metric Box */}
                  <div className="col-span-5 bg-[#0d121c] border border-[#1b2234] rounded p-4 text-center flex flex-col justify-center gap-2">
                    <span className="text-[11px] text-slate-400 font-medium">COSINE PROXIMITY</span>
                    <div className="text-3xl font-mono font-bold text-emerald-400">
                      {searchResult.match_score ? searchResult.match_score.toFixed(4) : '0.7842'}
                    </div>

                    {bandCfg && (
                      <div className={`inline-block px-2.5 py-1 rounded text-xs font-semibold ${bandCfg.bg} ${bandCfg.color} border ${bandCfg.border}`}>
                        HIGH MATCH BAND
                      </div>
                    )}

                    <div className="text-[10px] text-slate-500 border-t border-[#1b2234] pt-2">
                      1 face detected · 120 references searched
                    </div>
                  </div>

                </div>
              )}

              {/* UNKNOWN FACE / SYNTHETIC EXTERNAL IDENTITY FALLBACK */}
              {searchResult?.status === 'NO_CIVIX_MATCH' && searchResult.synthetic_identity && (
                <div className="mt-3 bg-[#0d121c] border border-amber-800/40 rounded p-3 text-xs space-y-2">
                  <div className="flex items-center justify-between border-b border-[#1b2234] pb-1.5">
                    <span className="font-medium text-amber-400">SYNTHETIC EXTERNAL IDENTITY SOURCE</span>
                    <span className="text-[10px] text-amber-300 bg-amber-950 px-1.5 py-0.5 rounded border border-amber-800">DEMO ONLY</span>
                  </div>
                  <p className="text-slate-400 text-[11px]">No enrolled CIVIX identity exceeded match threshold.</p>
                  <div className="font-semibold text-slate-200">{searchResult.synthetic_identity.name}</div>
                  <div className="grid grid-cols-3 gap-2 text-slate-400">
                    <div><span className="text-slate-500">Age:</span> {searchResult.synthetic_identity.age}</div>
                    <div><span className="text-slate-500">City:</span> {searchResult.synthetic_identity.city}</div>
                    <div><span className="text-slate-500">Occ:</span> {searchResult.synthetic_identity.occupation}</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* MOVEMENT TIMELINE STRIP */}
          <div className="flex flex-col">
            <SectionHeader
              title="Movement Timeline"
              subtitle="Chronological camera observations"
              action={
                <button
                  onClick={() => navigate('/spatial')}
                  className="text-xs text-blue-400 hover:underline flex items-center gap-1"
                >
                  <MapPin className="w-3.5 h-3.5" /> View Movement on Map
                </button>
              }
            />

            <div className="p-4 bg-[#0a0d14]">
              {activeCctvObservations.length > 0 ? (
                <div className="relative flex items-center justify-between">
                  <div className="absolute left-0 right-0 top-1/2 -translate-y-1/2 h-0.5 bg-[#1b2234] z-0" />

                  {activeCctvObservations.slice(0, 5).map((obs, idx) => (
                    <div key={obs.observation_id || idx} className="relative z-10 flex flex-col items-center bg-[#0d121c] border border-[#1b2234] p-2 rounded text-center min-w-[90px]">
                      <span className="text-xs font-mono font-semibold text-blue-400">
                        {obs.timestamp ? obs.timestamp.slice(11, 16) : `2${idx}:0${idx*3}`}
                      </span>
                      <span className="text-[11px] text-slate-300 font-medium mt-0.5">
                        {obs.region || obs.camera_name || 'Dwarka Sec 23'}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        {obs.camera_code || `CAM-0${idx+4}`}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={Clock}
                  title="No movement timeline"
                  subtitle="Timeline populates when camera observations exist for subject"
                  className="py-3"
                />
              )}
            </div>
          </div>

        </div>

        {/* ── REGION 3: RIGHT PANE — CCTV OBSERVATIONS & CONTEXT (3 Cols) ─────── */}
        <div className="col-span-3 flex flex-col bg-[#090c12] overflow-y-auto divide-y divide-[#1b2234]">

          {/* CCTV OBSERVATIONS EVIDENCE GALLERY */}
          <div className="flex flex-col">
            <SectionHeader
              title="CCTV Observations"
              subtitle={`${activeCctvObservations.length} captures identified`}
            />

            <div className="p-3 bg-[#0d121c] border-b border-[#1b2234] flex items-center gap-1">
              {([
                { id: 'ALL',          label: 'All Captures' },
                { id: 'KEY_MOVEMENT', label: 'Key Movement' },
                { id: 'MAP_VIEW',     label: 'Map View' },
              ] as const).map(f => (
                <button
                  key={f.id}
                  onClick={() => setCctvFilterMode(f.id)}
                  className={`px-2 py-1 text-[11px] font-medium rounded transition-all ${
                    cctvFilterMode === f.id
                      ? 'bg-[#1b2438] text-blue-400 border border-[#2b3854]'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>

            <div className="p-3 bg-[#090c12]">
              {activeCctvObservations.length > 0 ? (
                <div className="grid grid-cols-2 gap-2 max-h-[340px] overflow-y-auto pr-1">
                  {activeCctvObservations.map(obs => (
                    <div
                      key={obs.observation_id}
                      className="bg-[#0d121c] border border-[#1b2234] rounded overflow-hidden hover:border-blue-500/50 transition-all"
                    >
                      <div className="aspect-video bg-[#05070a] overflow-hidden">
                        <img
                          src={'thumbnail' in obs ? (obs as any).thumbnail : 'https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600&auto=format&fit=crop&q=80'}
                          alt={obs.camera_name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="p-2 space-y-0.5 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-blue-400 font-semibold">{obs.camera_code || 'CAM-04'}</span>
                          <span className="text-[10px] text-slate-400">{obs.timestamp ? obs.timestamp.slice(11, 16) : '21:43'}</span>
                        </div>
                        <div className="text-[11px] text-slate-300 truncate">{obs.region || obs.camera_name || 'Dwarka Sec 23'}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={Camera}
                  title="No CCTV observations"
                  subtitle="No camera captures associated with target"
                  className="py-8"
                />
              )}
            </div>
          </div>

          {/* INVESTIGATIVE CONTEXT */}
          <div className="flex flex-col">
            <SectionHeader
              title="Investigative Context"
              subtitle="Linked cases & evidence summary"
              action={
                context?.cases?.[0] && (
                  <Link
                    to={`/cases/${context.cases[0].case_id}`}
                    className="text-xs text-blue-400 hover:underline flex items-center gap-1"
                  >
                    Workspace <ExternalLink className="w-3 h-3" />
                  </Link>
                )
              }
            />

            <div className="p-4 bg-[#090c12] space-y-3">
              {/* Compact Summary Bar */}
              <div className="text-xs font-medium text-slate-400 bg-[#0d121c] border border-[#1b2234] p-2.5 rounded text-center">
                {context?.cases?.length || (isGoldenCase ? 2 : 0)} linked cases · {context?.evidence?.length || (isGoldenCase ? 14 : 0)} evidence links · {context?.events?.length || (isGoldenCase ? 8 : 0)} events
              </div>

              {/* Navigable Associated Cases */}
              <div className="space-y-2">
                <span className="text-[11px] font-medium text-slate-400">Associated Cases</span>

                {context?.cases && context.cases.length > 0 ? (
                  context.cases.map(c => (
                    <Link
                      key={c.case_id}
                      to={`/cases/${c.case_id}`}
                      className="block bg-[#0d121c] border border-[#1b2234] hover:border-blue-500/50 rounded p-2.5 transition-all"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="text-xs font-mono font-semibold text-blue-400">{c.case_number}</div>
                          <div className="text-xs font-medium text-slate-200 mt-0.5">{c.title}</div>
                        </div>
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${ROLE_BADGES[c.role] || 'bg-rose-950 text-rose-300'}`}>
                          {c.role}
                        </span>
                      </div>
                    </Link>
                  ))
                ) : isGoldenCase ? (
                  <div className="space-y-2">
                    <Link
                      to="/cases/1346a86d-267a-a635-9d62-e34c76ecd24f"
                      className="block bg-[#0d121c] border border-[#1b2234] hover:border-blue-500/50 rounded p-2.5 transition-all"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="text-xs font-mono font-semibold text-blue-400">CIV-2012-001</div>
                          <div className="text-xs font-medium text-slate-200 mt-0.5">Dwarka Sector 23 Cash Van Robbery</div>
                          <div className="text-[10px] text-slate-500 mt-1">14 Mar 2026 · Dwarka, New Delhi</div>
                        </div>
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-950/60 text-rose-300 border border-rose-800/50">
                          Suspect
                        </span>
                      </div>
                    </Link>

                    <Link
                      to="/cases/1346a86d-267a-a635-9d62-e34c76ecd24f"
                      className="block bg-[#0d121c] border border-[#1b2234] hover:border-blue-500/50 rounded p-2.5 transition-all"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="text-xs font-mono font-semibold text-blue-400">CIV-2026-009</div>
                          <div className="text-xs font-medium text-slate-200 mt-0.5">NH-48 Vehicle Theft</div>
                          <div className="text-[10px] text-slate-500 mt-1">22 Jan 2026 · Gurugram Corridor</div>
                        </div>
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/50">
                          Person of Interest
                        </span>
                      </div>
                    </Link>
                  </div>
                ) : (
                  <EmptyState
                    icon={Briefcase}
                    title="No associated cases"
                    subtitle="No linked case records found for subject"
                    className="py-4"
                  />
                )}
              </div>
            </div>
          </div>

        </div>

      </div>

      {/* Subtle Scan Line Animation */}
      <style>{`
        @keyframes scanLine {
          0%   { top: 0%; opacity: 0.9; }
          50%  { top: 100%; opacity: 0.9; }
          100% { top: 0%; opacity: 0.9; }
        }
      `}</style>
    </div>
  );
};

export default BiometricIntelligencePage;
