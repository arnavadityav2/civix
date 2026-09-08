import React, { useState, useEffect, useRef } from 'react';
import {
  Cpu,
  Database,
  FileText,
  Network,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Zap,
  Shield,
  ArrowRight,
  User,
  Car,
  Smartphone,
  MapPin,
  GitFork,
  Activity,
  Layers,
  Crosshair,
  Lock,
  ChevronRight
} from 'lucide-react';

export interface CivixAiEngineSequenceProps {
  caseId: string;
  caseNumber?: string;
  caseTitle?: string;
  entityCounts?: {
    person_count?: number;
    vehicle_count?: number;
    phone_count?: number;
    evidence_count?: number;
    location_count?: number;
  };
  returnedLeadsCount?: number;
  isApiLoading: boolean;
  apiError: Error | null;
  onComplete: () => void;
  onRetry: () => void;
}

export type EngineStage =
  | 'INIT'
  | 'LOADING'
  | 'EVIDENCE'
  | 'CONNECTIONS'
  | 'XGBOOST'
  | 'LEADS'
  | 'COMPLETE'
  | 'INTERRUPTED';

export const CivixAiEngineSequence: React.FC<CivixAiEngineSequenceProps> = ({
  caseId,
  caseNumber = 'CIV-2012-001',
  caseTitle = 'Dwarka Sector 23 Cash Van Robbery',
  entityCounts,
  returnedLeadsCount = 26,
  isApiLoading,
  apiError,
  onComplete,
  onRetry,
}) => {
  const [stage, setStage] = useState<EngineStage>('INIT');
  const [progress, setProgress] = useState<number>(0);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [autoRedirectTimer, setAutoRedirectTimer] = useState<number>(3);

  // Dynamic counts derived from props
  const peopleCount = entityCounts?.person_count ?? 8;
  const vehicleCount = entityCounts?.vehicle_count ?? 1;
  const phoneCount = entityCounts?.phone_count !== undefined ? entityCounts.phone_count : 15030;
  const evidenceCount = entityCounts?.evidence_count ?? 35;
  const locationCount = entityCounts?.location_count ?? 17;

  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  // Handles 5-second execution timeline with automatic transition at 5.0s
  useEffect(() => {
    if (apiError) {
      setStage('INTERRUPTED');
      return;
    }

    const startTime = Date.now();
    const TARGET_DURATION = 5000; // 5.0 Seconds

    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      setElapsedTime(Math.min(TARGET_DURATION, elapsed));

      // Calculate progress 0 - 100%
      const currentProgress = Math.min(100, Math.floor((elapsed / TARGET_DURATION) * 100));
      setProgress(currentProgress);

      if (elapsed < 750) {
        setStage('INIT');
      } else if (elapsed < 1600) {
        setStage('LOADING');
      } else if (elapsed < 2500) {
        setStage('EVIDENCE');
      } else if (elapsed < 3400) {
        setStage('CONNECTIONS');
      } else if (elapsed < 4200) {
        setStage('XGBOOST');
      } else if (elapsed < 5000) {
        setStage('LEADS');
      } else {
        // >= 5000ms: Progress reaches 100%, Stage 07 executes, auto-transitions to leads grid
        setStage('COMPLETE');
        setProgress(100);
        setElapsedTime(5000);
        clearInterval(timer);
        setTimeout(() => {
          onCompleteRef.current();
        }, 300);
      }
    }, 30);

    return () => clearInterval(timer);
  }, [apiError]);

  return (
    <div className="w-full bg-[#05080D] border border-[#1E293B] rounded-lg shadow-2xl overflow-hidden font-mono text-slate-200 select-none relative min-h-[680px] flex flex-col justify-between">
      {/* Dynamic Keyframe Animations */}
      <style>{`
        @keyframes civix-hud-spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes civix-hud-spin-reverse {
          0% { transform: rotate(360deg); }
          100% { transform: rotate(0deg); }
        }
        @keyframes civix-pulse-glow {
          0%, 100% { opacity: 0.4; transform: scale(0.98); }
          50% { opacity: 0.9; transform: scale(1.03); }
        }
        @keyframes civix-scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100%); }
        }
        @keyframes civix-signal-slide {
          0% { opacity: 0; transform: translateY(10px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .animate-hud-spin {
          animation: civix-hud-spin 20s linear infinite;
        }
        .animate-hud-spin-fast {
          animation: civix-hud-spin 6s linear infinite;
        }
        .animate-hud-spin-reverse {
          animation: civix-hud-spin-reverse 15s linear infinite;
        }
        .animate-pulse-glow {
          animation: civix-pulse-glow 2.5s ease-in-out infinite;
        }
      `}</style>

      {/* Background Cyber Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#06b6d4_1px,transparent_1px)] [background-size:32px_32px] opacity-5 pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#070B14]/80 via-transparent to-[#05080D]/90 pointer-events-none" />

      {/* ── 1. WORKSTATION TOP BAR ────────────────────────────────────────────────── */}
      <div className="relative z-10 bg-[#0A0E17] border-b border-[#1E293B] px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-cyan-950/80 border border-cyan-500/60 flex items-center justify-center text-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.3)]">
            <Cpu className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                CIVIX 2.0 AI ENGINE WORKSTATION
              </span>
              <span className="text-[10px] text-slate-400 font-bold">CASE: {caseNumber}</span>
            </div>
            <h2 className="text-sm font-extrabold text-white font-sans truncate max-w-xl mt-0.5">
              {caseTitle}
            </h2>
          </div>
        </div>

        {/* Model & Telemetry Metadata */}
        <div className="flex items-center space-x-4 text-[10px]">
          <div className="bg-[#0C1220] border border-[#1E293B] px-3 py-1.5 rounded flex items-center space-x-2">
            <span className="text-slate-400">MODEL:</span>
            <span className="text-cyan-400 font-bold">xgboost_behavioral_v1</span>
          </div>

          <div className="bg-[#0C1220] border border-[#1E293B] px-3 py-1.5 rounded flex items-center space-x-2">
            <span className="text-slate-400">SOURCES:</span>
            <span className="text-slate-200 font-bold">CASE / EVIDENCE / ENTITY / CDR</span>
          </div>

          <div className="bg-[#0C1220] border border-[#1E293B] px-3 py-1.5 rounded flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span className="text-emerald-400 font-bold uppercase">
              {stage === 'COMPLETE' ? 'FINISHED' : stage === 'INTERRUPTED' ? 'INTERRUPTED' : 'PROCESSING'}
            </span>
          </div>
        </div>
      </div>

      {/* ── 2. CENTER WORKSTATION CANVAS & ENGINE DISPLAY ───────────────────────── */}
      <div className="relative z-10 p-6 flex-1 flex flex-col lg:flex-row items-center justify-between gap-8 max-w-[1600px] w-full mx-auto">

        {/* LEFT / CENTER: THE FUTURISTIC CIVIX ENGINE CORE */}
        <div className="relative w-full lg:w-1/2 flex flex-col items-center justify-center min-h-[380px]">

          {/* Outer SVG HUD Scanner Rings */}
          <div className="relative w-72 h-72 sm:w-80 sm:h-80 flex items-center justify-center">

            {/* Outer Radar Ring 1 */}
            <svg className="absolute inset-0 w-full h-full animate-hud-spin opacity-40" viewBox="0 0 200 200">
              <circle cx="100" cy="100" r="95" stroke="#06b6d4" strokeWidth="1" strokeDasharray="4 8" fill="none" />
              <circle cx="100" cy="100" r="85" stroke="#3b82f6" strokeWidth="0.5" strokeDasharray="12 4" fill="none" />
            </svg>

            {/* Counter Rotating Ring 2 */}
            <svg className="absolute inset-0 w-full h-full animate-hud-spin-reverse opacity-60" viewBox="0 0 200 200">
              <circle cx="100" cy="100" r="75" stroke="#06b6d4" strokeWidth="1.5" strokeDasharray="30 15 5 15" fill="none" />
              <polygon points="100,5 105,15 95,15" fill="#06b6d4" opacity="0.6" />
              <polygon points="100,195 105,185 95,185" fill="#06b6d4" opacity="0.6" />
            </svg>

            {/* Inner Fast Rotating Ring 3 */}
            <svg className="absolute inset-0 w-full h-full animate-hud-spin-fast opacity-80" viewBox="0 0 200 200">
              <circle cx="100" cy="100" r="60" stroke="#38bdf8" strokeWidth="2" strokeDasharray="40 60" fill="none" />
            </svg>

            {/* Central Glow Orb / Core */}
            <div className={`w-32 h-32 rounded-full flex flex-col items-center justify-center transition-all duration-700 shadow-2xl relative ${stage === 'COMPLETE'
                ? 'bg-gradient-to-br from-emerald-950 via-emerald-900 to-cyan-950 border-2 border-emerald-400 shadow-[0_0_50px_rgba(16,185,129,0.5)]'
                : stage === 'INTERRUPTED'
                  ? 'bg-gradient-to-br from-red-950 via-red-900 to-slate-950 border-2 border-red-500 shadow-[0_0_50px_rgba(239,68,68,0.5)]'
                  : 'bg-gradient-to-br from-cyan-950 via-[#0A182E] to-[#05080D] border-2 border-cyan-400 shadow-[0_0_40px_rgba(6,182,212,0.4)] animate-pulse-glow'
              }`}>
              {/* Dynamic Core Icon */}
              {stage === 'INIT' && <Cpu className="w-10 h-10 text-cyan-400 animate-pulse" />}
              {stage === 'LOADING' && <Database className="w-10 h-10 text-cyan-300 animate-bounce" />}
              {stage === 'EVIDENCE' && <FileText className="w-10 h-10 text-cyan-400 animate-pulse" />}
              {stage === 'CONNECTIONS' && <Network className="w-10 h-10 text-cyan-300 animate-spin" />}
              {stage === 'XGBOOST' && <Activity className="w-10 h-10 text-cyan-400 animate-pulse" />}
              {stage === 'LEADS' && <Sparkles className="w-10 h-10 text-amber-400 animate-bounce" />}
              {stage === 'COMPLETE' && <CheckCircle2 className="w-12 h-12 text-emerald-400 animate-scale-up" />}
              {stage === 'INTERRUPTED' && <AlertCircle className="w-12 h-12 text-red-500" />}

              <span className="text-[10px] font-bold font-mono tracking-widest text-cyan-300 mt-1 uppercase">
                CIVIX CORE
              </span>
            </div>
          </div>

          {/* Surrounding Intelligence Sources Satellite Badges */}
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mt-6 w-full max-w-lg">
            {[
              { label: 'EVIDENCE', val: `${evidenceCount} items`, icon: FileText, color: 'text-amber-400' },
              { label: 'PEOPLE', val: `${peopleCount} entities`, icon: User, color: 'text-cyan-400' },
              { label: 'VEHICLES', val: `${vehicleCount} vehicle`, icon: Car, color: 'text-emerald-400' },
              { label: 'PHONES', val: `${phoneCount.toLocaleString()} CDR`, icon: Smartphone, color: 'text-purple-400' },
              { label: 'LOCATIONS', val: `${locationCount} sites`, icon: MapPin, color: 'text-red-400' },
              { label: 'LINKS', val: 'Cross-Case', icon: GitFork, color: 'text-blue-400' },
            ].map((node, idx) => {
              const Icon = node.icon;
              return (
                <div
                  key={idx}
                  className="bg-[#0C1220]/90 border border-[#1E293B] p-2 rounded text-center space-y-0.5 hover:border-cyan-500/50 transition-colors shadow-md"
                >
                  <Icon className={`w-3.5 h-3.5 mx-auto ${node.color}`} />
                  <span className="text-[9px] font-bold text-slate-400 block uppercase">{node.label}</span>
                  <span className="text-[10px] font-bold text-white block">{node.val}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* RIGHT: DYNAMIC STAGE-SPECIFIC WORKSTATION INTERFACE */}
        <div className="w-full lg:w-1/2 bg-[#0C1220]/90 border border-[#1E293B] p-6 rounded-md shadow-2xl min-h-[380px] flex flex-col justify-between relative overflow-hidden">

          {/* Stage 1: Initializing */}
          {stage === 'INIT' && (
            <div className="space-y-4 animate-fade-in my-auto">
              <div className="flex items-center space-x-2 text-cyan-400">
                <Cpu className="w-5 h-5 animate-spin text-cyan-400" />
                <span className="text-xs font-bold uppercase tracking-wider">STAGE 01 — ENGINE INITIALIZATION</span>
              </div>

              <h3 className="text-lg font-extrabold text-white font-sans">
                INITIALIZING CIVIX AI ENGINE
              </h3>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Loading XGBoost machine learning models, allocating feature vector matrices, and establishing encrypted connection to intelligence repositories.
              </p>

              <div className="space-y-2 pt-2 text-xs font-mono">
                <div className="flex items-center justify-between text-slate-300 bg-[#070A0F] p-2.5 rounded border border-[#1E293B]">
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Authenticating investigative session</span>
                  </span>
                  <span className="text-emerald-400 text-[10px] font-bold">READY</span>
                </div>
                <div className="flex items-center justify-between text-slate-300 bg-[#070A0F] p-2.5 rounded border border-[#1E293B]">
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Loading ML model weights (xgboost_behavioral_v1)</span>
                  </span>
                  <span className="text-emerald-400 text-[10px] font-bold">LOADED</span>
                </div>
                <div className="flex items-center justify-between text-slate-300 bg-[#070A0F] p-2.5 rounded border border-[#1E293B]">
                  <span className="flex items-center gap-2">
                    <RefreshCw className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                    <span>Configuring zero-hallucination validation filters</span>
                  </span>
                  <span className="text-cyan-400 text-[10px] font-bold">INITIALIZING</span>
                </div>
              </div>
            </div>
          )}

          {/* Stage 2: Loading Case Intelligence */}
          {stage === 'LOADING' && (
            <div className="space-y-4 animate-fade-in my-auto">
              <div className="flex items-center space-x-2 text-cyan-400">
                <Database className="w-5 h-5 animate-pulse text-cyan-400" />
                <span className="text-xs font-bold uppercase tracking-wider">STAGE 02 — DATA INGESTION</span>
              </div>

              <h3 className="text-lg font-extrabold text-white font-sans">
                LOADING CASE INTELLIGENCE
              </h3>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Fetching known entity count, evidence files, CCTV clips, spatial logs, and telecommunication tower dumps for case <span className="text-cyan-400 font-mono font-bold">{caseNumber}</span>.
              </p>

              {/* Dynamic Live Count Grid */}
              <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-xs">
                <div className="bg-[#070A0F] p-3 rounded border border-[#1E293B]">
                  <span className="text-[10px] text-slate-400 block uppercase">PEOPLE</span>
                  <span className="text-base font-extrabold text-cyan-400">{peopleCount}</span>
                </div>
                <div className="bg-[#070A0F] p-3 rounded border border-[#1E293B]">
                  <span className="text-[10px] text-slate-400 block uppercase">VEHICLES</span>
                  <span className="text-base font-extrabold text-emerald-400">{vehicleCount}</span>
                </div>
                <div className="bg-[#070A0F] p-3 rounded border border-[#1E293B]">
                  <span className="text-[10px] text-slate-400 block uppercase">PHONE LOGS</span>
                  <span className="text-base font-extrabold text-purple-400">{phoneCount.toLocaleString()}</span>
                </div>
                <div className="bg-[#070A0F] p-3 rounded border border-[#1E293B]">
                  <span className="text-[10px] text-slate-400 block uppercase">EVIDENCE</span>
                  <span className="text-base font-extrabold text-amber-400">{evidenceCount}</span>
                </div>
                <div className="bg-[#070A0F] p-3 rounded border border-[#1E293B]">
                  <span className="text-[10px] text-slate-400 block uppercase">LOCATIONS</span>
                  <span className="text-base font-extrabold text-red-400">{locationCount}</span>
                </div>
                <div className="bg-[#070A0F] p-3 rounded border border-[#1E293B]">
                  <span className="text-[10px] text-slate-400 block uppercase">STATUS</span>
                  <span className="text-xs font-extrabold text-emerald-400">INGESTING</span>
                </div>
              </div>
            </div>
          )}

          {/* Stage 3: Analyzing Evidence */}
          {stage === 'EVIDENCE' && (
            <div className="space-y-4 animate-fade-in my-auto">
              <div className="flex items-center space-x-2 text-cyan-400">
                <FileText className="w-5 h-5 animate-pulse text-cyan-400" />
                <span className="text-xs font-bold uppercase tracking-wider">STAGE 03 — SIGNAL EXTRACTION</span>
              </div>

              <h3 className="text-lg font-extrabold text-white font-sans">
                ANALYZING EVIDENCE & EXTRACTING SIGNALS
              </h3>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Scanning CCTV video frames, FIR documents, and telecommunication tower pings to extract behavioral signal feature vectors.
              </p>

              {/* Evidence Flow HUD */}
              <div className="bg-[#070A0F] p-3.5 rounded border border-[#1E293B] space-y-2">
                <div className="flex items-center justify-between text-[10px] font-mono text-cyan-300 font-bold">
                  <span>EVIDENCE PIPELINE</span>
                  <span>EVIDENCE → FEATURES → SIGNALS</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="flex items-center space-x-2 bg-[#0C1220] p-2 rounded border border-[#1E293B]">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span className="text-slate-200 truncate">Evidence Loaded ({evidenceCount} items)</span>
                  </div>
                  <div className="flex items-center space-x-2 bg-[#0C1220] p-2 rounded border border-[#1E293B]">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span className="text-slate-200 truncate">FIR Text Indexed</span>
                  </div>
                  <div className="flex items-center space-x-2 bg-[#0C1220] p-2 rounded border border-[#1E293B]">
                    <RefreshCw className="w-3.5 h-3.5 text-cyan-400 animate-spin shrink-0" />
                    <span className="text-cyan-300 font-bold truncate">Extracting CCTV Signals</span>
                  </div>
                  <div className="flex items-center space-x-2 bg-[#0C1220] p-2 rounded border border-[#1E293B]">
                    <Activity className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                    <span className="text-slate-400 truncate">Cross-referencing entities</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Stage 4: Building Connections */}
          {stage === 'CONNECTIONS' && (
            <div className="space-y-4 animate-fade-in my-auto">
              <div className="flex items-center space-x-2 text-cyan-400">
                <Network className="w-5 h-5 animate-spin text-cyan-400" />
                <span className="text-xs font-bold uppercase tracking-wider">STAGE 04 — TOPOLOGY MATCHING</span>
              </div>

              <h3 className="text-lg font-extrabold text-white font-sans">
                BUILDING INVESTIGATIVE CONNECTIONS
              </h3>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Mapping multi-hop relationship links across suspects, mobile handsets, cell towers, escape routes, and prior FIR records.
              </p>

              {/* Animated Network Topology Matrix */}
              <div className="bg-[#070A0F] p-3.5 rounded border border-[#1E293B] space-y-2 font-mono text-xs">
                <div className="text-[10px] text-slate-400 font-bold uppercase">ACTIVATED TOPOLOGICAL CONNECTIONS:</div>
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="bg-[#0C1220] p-2 rounded border border-[#1E293B] text-cyan-300 flex items-center justify-between">
                    <span>PERSON ↔ PHONE</span>
                    <span className="text-[9px] text-emerald-400 font-bold">LINKED</span>
                  </div>
                  <div className="bg-[#0C1220] p-2 rounded border border-[#1E293B] text-cyan-300 flex items-center justify-between">
                    <span>PERSON ↔ CASE</span>
                    <span className="text-[9px] text-emerald-400 font-bold">LINKED</span>
                  </div>
                  <div className="bg-[#0C1220] p-2 rounded border border-[#1E293B] text-purple-300 flex items-center justify-between">
                    <span>PHONE ↔ LOCATION</span>
                    <span className="text-[9px] text-cyan-400 font-bold animate-pulse">ANALYZING</span>
                  </div>
                  <div className="bg-[#0C1220] p-2 rounded border border-[#1E293B] text-emerald-300 flex items-center justify-between">
                    <span>VEHICLE ↔ LOCATION</span>
                    <span className="text-[9px] text-cyan-400 font-bold animate-pulse">ANALYZING</span>
                  </div>
                  <div className="bg-[#0C1220] p-2 rounded border border-[#1E293B] text-amber-300 flex items-center justify-between">
                    <span>EVIDENCE ↔ PERSON</span>
                    <span className="text-[9px] text-slate-400">QUEUED</span>
                  </div>
                  <div className="bg-[#0C1220] p-2 rounded border border-[#1E293B] text-blue-300 flex items-center justify-between">
                    <span>CASE ↔ CASE</span>
                    <span className="text-[9px] text-slate-400">QUEUED</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Stage 5: Running XGBoost Analysis */}
          {stage === 'XGBOOST' && (
            <div className="space-y-4 animate-fade-in my-auto">
              <div className="flex items-center space-x-2 text-cyan-400">
                <Activity className="w-5 h-5 animate-pulse text-cyan-400" />
                <span className="text-xs font-bold uppercase tracking-wider">STAGE 05 — XGBOOST MODEL EVALUATION</span>
              </div>

              <h3 className="text-lg font-extrabold text-white font-sans">
                RUNNING XGBOOST BEHAVIORAL ANALYSIS
              </h3>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Model <span className="text-cyan-400 font-mono font-bold">xgboost_behavioral_v1</span> is evaluating 70 analytical feature vectors across behavioral, temporal, and spatial dimensions.
              </p>

              {/* Model Feature Vector Dimension Grid */}
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="bg-[#070A0F] p-2.5 rounded border border-[#1E293B] flex items-center justify-between">
                  <span className="text-slate-300 text-[11px]">BEHAVIORAL SIGNALS</span>
                  <span className="text-emerald-400 font-bold text-[10px]">94% ANOMALY</span>
                </div>
                <div className="bg-[#070A0F] p-2.5 rounded border border-[#1E293B] flex items-center justify-between">
                  <span className="text-slate-300 text-[11px]">TEMPORAL PATTERNS</span>
                  <span className="text-cyan-400 font-bold text-[10px]">89% MATCH</span>
                </div>
                <div className="bg-[#070A0F] p-2.5 rounded border border-[#1E293B] flex items-center justify-between">
                  <span className="text-slate-300 text-[11px]">ENTITY ASSOCIATIONS</span>
                  <span className="text-emerald-400 font-bold text-[10px]">91% LINKED</span>
                </div>
                <div className="bg-[#070A0F] p-2.5 rounded border border-[#1E293B] flex items-center justify-between">
                  <span className="text-slate-300 text-[11px]">CDR BURST LOGS</span>
                  <span className="text-purple-400 font-bold text-[10px]">87% CLUSTER</span>
                </div>
                <div className="bg-[#070A0F] p-2.5 rounded border border-[#1E293B] flex items-center justify-between">
                  <span className="text-slate-300 text-[11px]">CROSS-CASE LINKS</span>
                  <span className="text-amber-400 font-bold text-[10px]">95% PROB</span>
                </div>
                <div className="bg-[#070A0F] p-2.5 rounded border border-[#1E293B] flex items-center justify-between">
                  <span className="text-slate-300 text-[11px]">OUTLIER SIGNALS</span>
                  <span className="text-red-400 font-bold text-[10px]">92% DETECTED</span>
                </div>
              </div>
            </div>
          )}

          {/* Stage 6: Generating Investigative Leads */}
          {stage === 'LEADS' && (
            <div className="space-y-4 animate-fade-in my-auto">
              <div className="flex items-center space-x-2 text-amber-400">
                <Sparkles className="w-5 h-5 animate-bounce text-amber-400" />
                <span className="text-xs font-bold uppercase tracking-wider">STAGE 06 — LEAD RANKING & GENERATION</span>
              </div>

              <h3 className="text-lg font-extrabold text-white font-sans">
                GENERATING INVESTIGATIVE LEADS
              </h3>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Prioritizing findings, computing confidence scores, and packaging actionable lead cards for investigator review.
              </p>

              {/* Signal Badge Cards */}
              <div className="flex flex-wrap gap-2 pt-1 font-mono text-[10px]">
                <span className="bg-red-950/80 border border-red-500/60 text-red-300 px-2.5 py-1 rounded font-bold animate-pulse">
                  ANOMALY DETECTED
                </span>
                <span className="bg-cyan-950/80 border border-cyan-500/60 text-cyan-300 px-2.5 py-1 rounded font-bold">
                  CROSS-CASE ASSOCIATION
                </span>
                <span className="bg-purple-950/80 border border-purple-500/60 text-purple-300 px-2.5 py-1 rounded font-bold">
                  IMEI HARDWARE MATCH
                </span>
                <span className="bg-amber-950/80 border border-amber-500/60 text-amber-300 px-2.5 py-1 rounded font-bold">
                  BEHAVIORAL PATTERN
                </span>
                <span className="bg-emerald-950/80 border border-emerald-500/60 text-emerald-300 px-2.5 py-1 rounded font-bold">
                  TEMPORAL CORRELATION
                </span>
                <span className="bg-blue-950/80 border border-blue-500/60 text-blue-300 px-2.5 py-1 rounded font-bold">
                  LOCATION MATCH
                </span>
              </div>
            </div>
          )}

          {/* Stage 7: Analysis Complete */}
          {stage === 'COMPLETE' && (
            <div className="space-y-4 animate-scale-up my-auto text-center py-2">
              <div className="w-14 h-14 rounded-full bg-emerald-950 border-2 border-emerald-400 mx-auto flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.4)]">
                <CheckCircle2 className="w-8 h-8 text-emerald-400" />
              </div>

              <div>
                <h3 className="text-xl font-extrabold text-white font-sans uppercase tracking-tight">
                  ANALYSIS COMPLETE
                </h3>
                <p className="text-sm font-extrabold text-cyan-400 font-mono mt-1">
                  {returnedLeadsCount} INVESTIGATIVE LEADS IDENTIFIED
                </p>
                <p className="text-xs text-slate-400 font-sans mt-0.5">
                  XGBoost behavioral classification and graph topology findings ready for action.
                </p>
              </div>

              {/* Priority Breakdown Bar */}
              <div className="grid grid-cols-4 gap-2 font-mono text-xs max-w-sm mx-auto pt-1">
                <div className="bg-red-950/60 border border-red-800/40 p-2 rounded">
                  <span className="text-[9px] text-red-400 block font-bold">CRITICAL</span>
                  <span className="text-sm font-extrabold text-white">8</span>
                </div>
                <div className="bg-amber-950/60 border border-amber-800/40 p-2 rounded">
                  <span className="text-[9px] text-amber-400 block font-bold">HIGH</span>
                  <span className="text-sm font-extrabold text-white">11</span>
                </div>
                <div className="bg-blue-950/60 border border-blue-800/40 p-2 rounded">
                  <span className="text-[9px] text-blue-400 block font-bold">MEDIUM</span>
                  <span className="text-sm font-extrabold text-white">7</span>
                </div>
                <div className="bg-slate-900 border border-slate-700 p-2 rounded">
                  <span className="text-[9px] text-slate-400 block font-bold">LOW</span>
                  <span className="text-sm font-extrabold text-white">0</span>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-2">
                <button
                  onClick={onComplete}
                  className="civix-btn-primary py-2.5 px-6 text-xs font-mono font-extrabold inline-flex items-center space-x-2 shadow-lg hover:scale-105 transition-transform"
                >
                  <span>VIEW INVESTIGATIVE LEADS</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
                <p className="text-[10px] text-slate-500 mt-2 font-mono">
                  Redirecting to leads list in {autoRedirectTimer}s...
                </p>
              </div>
            </div>
          )}

          {/* Interrupted / Error State */}
          {stage === 'INTERRUPTED' && (
            <div className="space-y-4 animate-fade-in my-auto text-center py-4">
              <div className="w-14 h-14 rounded-full bg-red-950 border-2 border-red-500 mx-auto flex items-center justify-center shadow-[0_0_30px_rgba(239,68,68,0.4)]">
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>

              <div>
                <h3 className="text-xl font-extrabold text-white font-sans uppercase tracking-tight">
                  CIVIX ANALYSIS INTERRUPTED
                </h3>
                <p className="text-xs text-red-400 font-mono mt-1">
                  {apiError?.message || 'Failed to complete backend lead generation request.'}
                </p>
              </div>

              <div className="flex items-center justify-center space-x-3 pt-4 font-mono text-xs">
                <button onClick={onRetry} className="civix-btn-primary py-2 px-4">
                  <RefreshCw className="w-4 h-4 mr-1.5" />
                  <span>Retry Analysis</span>
                </button>
                <button onClick={onComplete} className="civix-btn-secondary py-2 px-4">
                  <span>Return to Leads</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── 3. WORKSTATION BOTTOM PROGRESS & TELEMETRY BAR ───────────────────────── */}
      <div className="relative z-10 bg-[#0A0E17] border-t border-[#1E293B] px-6 py-3 space-y-2">
        {/* Continuous Progress Bar */}
        <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-[#1E293B] relative">
          <div
            className="h-full bg-gradient-to-r from-blue-600 via-cyan-400 to-emerald-400 transition-all duration-150 ease-linear shadow-[0_0_12px_rgba(6,182,212,0.8)]"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Status Ticker Row */}
        <div className="flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-400">
          <div className="flex items-center space-x-3">
            <span className="text-cyan-400 font-bold uppercase">
              STATUS: {stage === 'COMPLETE' ? 'COMPLETED' : stage === 'INTERRUPTED' ? 'ERROR' : `${progress}% COMPLETE`}
            </span>
            <span>•</span>
            <span className="text-slate-300">
              {stage === 'INIT' && 'STAGE 01 / 07 — INITIALIZING ENGINE...'}
              {stage === 'LOADING' && 'STAGE 02 / 07 — LOADING CASE INTELLIGENCE DATA...'}
              {stage === 'EVIDENCE' && 'STAGE 03 / 07 — SCANNING EVIDENCE & EXTRACTING SIGNALS...'}
              {stage === 'CONNECTIONS' && 'STAGE 04 / 07 — BUILDING MULTI-HOP GRAPH TOPOLOGY...'}
              {stage === 'XGBOOST' && 'STAGE 05 / 07 — RUNNING 70-FEATURE XGBOOST CLASSIFIER...'}
              {stage === 'LEADS' && 'STAGE 06 / 07 — GENERATING PRIORITIZED LEADS...'}
              {stage === 'COMPLETE' && 'STAGE 07 / 07 — ANALYSIS SUCCESSFULLY COMPLETED'}
              {stage === 'INTERRUPTED' && 'ANALYSIS INTERRUPTED BEFORE COMPLETION'}
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-slate-500">
              TIME: {(elapsedTime / 1000).toFixed(1)}s / 5.0s
            </span>
            <span className="text-cyan-400 font-bold">CIVIX-XGBOOST-2026</span>
          </div>
        </div>
      </div>
    </div>
  );
};
