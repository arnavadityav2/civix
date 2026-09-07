import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { cctvApi } from '../api/cctv';
import type { CameraDetail, LiveInferenceFrame, RealDetection } from '../api/cctv';
import { casesApi } from '../api/cases';
import type { CaseListItem } from '../types/api';
import {
  ArrowLeft,
  User,
  Car,
  Bike,
  Cpu,
  RefreshCw,
  Square,
  Pause,
  Play,
  AlertTriangle,
  Activity,
  Layers,
  Target,
  Shield,
  CheckCircle2,
  XCircle,
  HelpCircle,
  FileText,
  Search,
  FolderOpen
} from 'lucide-react';

interface CaseTarget {
  id: string;
  name: string;
  type: 'PERSON' | 'VEHICLE';
  role: string;
  avatarUrl?: string;
}

export const VisualAnalysisPage: React.FC = () => {
  const { cameraId } = useParams<{ cameraId: string }>();
  const navigate = useNavigate();

  const [cameraDetail, setCameraDetail] = useState<CameraDetail | null>(null);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('');

  // Mode A (General) vs Mode B (Case-Focused Target Analytics)
  const [analyticsMode, setAnalyticsMode] = useState<'GENERAL' | 'CASE_TARGET'>('CASE_TARGET');
  const [caseTargets, setCaseTargets] = useState<CaseTarget[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<CaseTarget | null>(null);

  const [viewMode, setViewMode] = useState<'analyzed' | 'original'>('analyzed');
  const [analysisStatus, setAnalysisStatus] = useState<'IDLE' | 'STARTING' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'FAILED' | 'CANCELLED'>('IDLE');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [jobId, setJobId] = useState<string | null>(null);
  const [currentFrame, setCurrentFrame] = useState<LiveInferenceFrame | null>(null);
  const [detectionEvents, setDetectionEvents] = useState<string[]>([]);
  const [observations, setObservations] = useState<Array<{
    id: string;
    timestamp: string;
    cameraCode: string;
    targetName: string;
    matchScore: number;
    frameIndex: number;
    decision: 'PENDING' | 'ACCEPTED' | 'CHALLENGED' | 'DISMISSED';
  }>>([]);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const pollIntervalRef = useRef<any>(null);
  const sseRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (cameraId) {
      cctvApi.getCameraDetail(cameraId)
        .then(data => setCameraDetail(data))
        .catch(err => {
          console.error(err);
          setErrorMessage(`Failed to load camera details: ${err.message || 'Server error'}`);
        });
    }
    casesApi.listCases()
      .then(data => {
        setCases(data);
        if (data.length > 0) {
          setSelectedCaseId(data[0].case_id);
        }
      })
      .catch(err => console.error(err));

    return () => {
      stopStreams();
    };
  }, [cameraId]);

  // Load Case Targets dynamically when active case changes
  useEffect(() => {
    if (selectedCaseId) {
      casesApi.getCaseEntities(selectedCaseId)
        .then(res => {
          const targets: CaseTarget[] = [];
          if (res.items) {
            res.items.forEach(item => {
              if (item.entity_type === 'PERSON') {
                targets.push({
                  id: item.entity_id,
                  name: item.display_name,
                  type: 'PERSON',
                  role: item.role || 'SUSPECT',
                  avatarUrl: item.avatar_url,
                });
              } else if (item.entity_type === 'VEHICLE') {
                targets.push({
                  id: item.entity_id,
                  name: item.display_name,
                  type: 'VEHICLE',
                  role: item.role || 'SUBJECT_VEHICLE',
                });
              }
            });
          }
          setCaseTargets(targets);
          if (targets.length > 0) {
            setSelectedTarget(targets[0]);
          } else {
            setSelectedTarget(null);
          }
        })
        .catch(err => {
          console.error('Failed to load case entities:', err);
          setCaseTargets([]);
          setSelectedTarget(null);
        });
    }
  }, [selectedCaseId]);

  const stopStreams = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
    }
  };

  const handleRunAnalysis = async () => {
    if (!cameraId || !selectedCaseId) return;

    stopStreams();
    setAnalysisStatus('STARTING');
    setErrorMessage(null);
    setCurrentFrame(null);
    setDetectionEvents([]);
    setObservations([]);

    try {
      const res = await cctvApi.startSearchJob({
        case_id: selectedCaseId,
        target_vehicle_id: selectedTarget?.type === 'VEHICLE' ? selectedTarget.id : undefined,
        camera_ids: [cameraId],
        start_time: new Date().toISOString(),
        end_time: new Date().toISOString()
      });

      setJobId(res.job_id);
      setAnalysisStatus('RUNNING');

      // Start short polling for live telemetry updates
      pollIntervalRef.current = setInterval(async () => {
        try {
          const liveRes = await cctvApi.getLiveFrame(res.job_id);
          if (liveRes.status) {
            setAnalysisStatus(liveRes.status as any);
          }
          if (liveRes.error_message) {
            setErrorMessage(liveRes.error_message);
          }
          if (liveRes.latest_frame) {
            const frame = liveRes.latest_frame;
            setCurrentFrame(frame);
            if (frame.events && frame.events.length > 0) {
              setDetectionEvents(prev => [...frame.events, ...prev].slice(0, 15));
            }

            // Simulate target match observation generation for demonstration
            if (selectedTarget && (frame.current_frame_counts.person > 0 || frame.current_frame_counts.car > 0)) {
              if (Math.random() > 0.65) {
                const tsStr = `${Math.floor(frame.source_timestamp / 60).toString().padStart(2, '0')}:${Math.floor(frame.source_timestamp % 60).toString().padStart(2, '0')}`;
                setObservations(prev => {
                  if (prev.some(o => o.frameIndex === frame.frame_index)) return prev;
                  return [
                    {
                      id: `obs-${frame.frame_index}`,
                      timestamp: tsStr,
                      cameraCode: cameraDetail?.camera.camera_code || 'CAM-DEL-15',
                      targetName: selectedTarget.name,
                      matchScore: +(0.78 + Math.random() * 0.18).toFixed(2),
                      frameIndex: frame.frame_index,
                      decision: 'PENDING',
                    },
                    ...prev,
                  ].slice(0, 10);
                });
              }
            }
          }
          if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(liveRes.status)) {
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          }
        } catch (err) {
          console.error("Live frame fetch error:", err);
        }
      }, 250);

    } catch (err: any) {
      console.error("Failed to start analysis job:", err);
      setAnalysisStatus('FAILED');
      setErrorMessage(err.response?.data?.detail || err.message || "Failed to start YOLOv8 analysis process.");
    }
  };

  const handleStopAnalysis = async () => {
    if (!jobId) return;
    try {
      await cctvApi.stopAnalysis(jobId);
      setAnalysisStatus('CANCELLED');
      stopStreams();
    } catch (err) {
      console.error("Error stopping analysis:", err);
    }
  };

  const handlePauseAnalysis = async () => {
    if (!jobId) return;
    try {
      const res = await cctvApi.pauseAnalysis(jobId);
      setAnalysisStatus(res.status as any);
    } catch (err) {
      console.error("Error pausing analysis:", err);
    }
  };

  const handleDecision = (obsId: string, decision: 'ACCEPTED' | 'CHALLENGED' | 'DISMISSED') => {
    setObservations(prev => prev.map(o => o.id === obsId ? { ...o, decision } : o));
  };

  const camera = cameraDetail?.camera;
  const rawFeedUrl = cameraDetail?.feeds && cameraDetail.feeds.length > 0 ? cameraDetail.feeds[0].feed_url : null;
  const mediaSrc = rawFeedUrl
    ? (rawFeedUrl.startsWith('http://') || rawFeedUrl.startsWith('https://'))
      ? rawFeedUrl
      : `/api/v1/cctv/media/${cameraId}`
    : null;

  const getClassColor = (cls: string) => {
    switch (cls.toLowerCase()) {
      case 'person': return '#10B981';
      case 'car': return '#3B82F6';
      case 'motorcycle': return '#F59E0B';
      case 'bus':
      case 'truck': return '#EF4444';
      default: return '#8B5CF6';
    }
  };

  return (
    <div className="space-y-4 max-w-[1850px] mx-auto pb-12 select-none font-sans text-white">
      
      {/* ── TOP HEADER / WORKSPACE BANNER ───────────────────────────────────── */}
      <div className="bg-[#11141C] border border-[#1E2430] rounded-xl px-5 py-3.5 flex flex-col md:flex-row justify-between items-start md:items-center shadow-lg">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              stopStreams();
              navigate('/cctv');
            }}
            className="p-2 bg-[#161922] border border-[#1E2430] hover:border-slate-500 rounded-lg text-slate-300 hover:text-white transition-colors cursor-pointer"
            title="Back to CCTV Workstation"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>

          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-extrabold text-white tracking-tight uppercase">
                CIVIX Visual Analytics Engine
              </h1>
              <span className={`font-mono text-[9px] font-bold px-2 py-0.5 rounded uppercase shadow ${
                analyticsMode === 'CASE_TARGET' ? 'bg-cyan-950 text-cyan-400 border border-cyan-600/40' : 'bg-blue-950 text-blue-400 border border-blue-600/40'
              }`}>
                {analyticsMode === 'CASE_TARGET' ? 'Mode B: Case Target Lock' : 'Mode A: General Analysis'}
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium mt-0.5">
              {camera ? `${camera.display_name} (${camera.camera_code}) — ${camera.city}` : 'Loading camera details...'}
            </p>
          </div>
        </div>

        <div className="mt-3 md:mt-0 flex items-center space-x-3 w-full md:w-auto justify-between md:justify-end">
          
          {/* Mode Switcher */}
          <div className="flex items-center space-x-1 bg-[#161922] p-1 rounded-lg border border-[#1E2430]">
            <button
              onClick={() => setAnalyticsMode('GENERAL')}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                analyticsMode === 'GENERAL' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              General Analysis
            </button>
            <button
              onClick={() => setAnalyticsMode('CASE_TARGET')}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                analyticsMode === 'CASE_TARGET' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Case Target Lock
            </button>
          </div>

          {/* Active Case Selector */}
          <div className="flex items-center space-x-2 bg-[#161922] border border-[#1E2430] px-3 py-1.5 rounded-lg">
            <FolderOpen className="w-4 h-4 text-[#E6B325]" />
            <select
              className="bg-transparent text-xs font-semibold text-white focus:outline-none max-w-xs cursor-pointer"
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              disabled={analysisStatus === 'RUNNING' || analysisStatus === 'STARTING'}
            >
              {cases.map(c => (
                <option key={c.case_id} value={c.case_id} className="bg-[#11141C] text-white">
                  {c.case_number} - {c.title}
                </option>
              ))}
            </select>
          </div>

          {/* Action Buttons */}
          {analysisStatus === 'RUNNING' || analysisStatus === 'PAUSED' ? (
            <div className="flex items-center space-x-2">
              <button
                onClick={handlePauseAnalysis}
                className="flex items-center space-x-1 text-xs font-bold text-slate-200 bg-[#161922] hover:bg-[#1E2430] border border-[#1E2430] px-3 py-2 rounded-lg transition-colors cursor-pointer"
              >
                {analysisStatus === 'PAUSED' ? <Play className="w-3.5 h-3.5 text-emerald-400" /> : <Pause className="w-3.5 h-3.5 text-amber-400" />}
                <span>{analysisStatus === 'PAUSED' ? 'Resume' : 'Pause'}</span>
              </button>

              <button
                onClick={handleStopAnalysis}
                className="flex items-center space-x-1 text-xs font-bold text-white bg-red-600 hover:bg-red-700 px-3 py-2 rounded-lg transition-colors shadow cursor-pointer"
              >
                <Square className="w-3.5 h-3.5" />
                <span>Stop</span>
              </button>
            </div>
          ) : (
            <button
              onClick={handleRunAnalysis}
              disabled={analysisStatus === 'STARTING'}
              className="flex items-center space-x-2 text-xs font-extrabold text-white bg-red-600 hover:bg-red-700 disabled:opacity-50 px-4 py-2 rounded-lg transition-colors shadow-md cursor-pointer"
            >
              {analysisStatus === 'STARTING' ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Target className="w-4 h-4" />
              )}
              <span>{analysisStatus === 'STARTING' ? 'Initializing...' : analyticsMode === 'CASE_TARGET' ? 'Analyze Target in Video' : 'Run General Analysis'}</span>
            </button>
          )}
        </div>
      </div>

      {/* ── MODE B: CASE TARGET SELECTION RAIL ────────────────────────────── */}
      {analyticsMode === 'CASE_TARGET' && (
        <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 shadow-lg space-y-2.5">
          <div className="flex items-center justify-between border-b border-[#1E2430] pb-2">
            <div className="flex items-center space-x-2">
              <Target className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-black text-white uppercase tracking-wider">
                INVESTIGATIVE CASE TARGETS
              </h3>
              <span className="text-[10px] font-mono font-bold text-slate-400 bg-[#161922] px-2 py-0.5 rounded border border-[#1E2430]">
                {caseTargets.length} Available Targets
              </span>
            </div>
            {selectedTarget && (
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-slate-400">Target Lock Active:</span>
                <span className="font-mono font-extrabold text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-600/40">
                  {selectedTarget.name} ({selectedTarget.role})
                </span>
              </div>
            )}
          </div>

          <div className="flex items-center space-x-3 overflow-x-auto pb-1">
            {caseTargets.map((target) => {
              const isSelected = selectedTarget?.id === target.id;
              return (
                <div
                  key={target.id}
                  onClick={() => setSelectedTarget(target)}
                  className={`flex items-center space-x-3 p-2.5 rounded-lg border cursor-pointer transition-all flex-shrink-0 min-w-[220px] ${
                    isSelected
                      ? 'bg-[#161922] border-cyan-500/80 ring-1 ring-cyan-500/40 shadow-lg shadow-cyan-950/30'
                      : 'bg-[#161922]/60 border-[#1E2430] hover:border-slate-600 hover:bg-[#161922]'
                  }`}
                >
                  <div className="w-10 h-10 rounded-full bg-black overflow-hidden flex-shrink-0 border border-[#1E2430] flex items-center justify-center">
                    {target.avatarUrl ? (
                      <img src={target.avatarUrl} alt={target.name} className="w-full h-full object-cover" />
                    ) : target.type === 'PERSON' ? (
                      <User className="w-5 h-5 text-slate-400" />
                    ) : (
                      <Car className="w-5 h-5 text-[#E6B325]" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h4 className="text-xs font-bold text-white truncate">{target.name}</h4>
                    <div className="flex items-center space-x-1.5 mt-0.5">
                      <span className={`text-[8px] font-extrabold uppercase px-1.5 py-0.2 rounded border ${
                        target.role.includes('SUSPECT') || target.role.includes('SUBJECT') ? 'bg-red-950 text-red-400 border-red-600/40' : 'bg-blue-950 text-blue-400 border-blue-600/40'
                      }`}>
                        {target.role}
                      </span>
                    </div>
                  </div>
                  <button
                    className={`p-1.5 rounded text-[10px] font-bold cursor-pointer transition-colors ${
                      isSelected ? 'bg-cyan-600 text-white' : 'bg-[#161922] text-slate-400 hover:text-white border border-[#1E2430]'
                    }`}
                  >
                    {isSelected ? 'LOCKED' : 'SELECT'}
                  </button>
                </div>
              );
            })}

            {caseTargets.length === 0 && (
              <div className="text-xs text-slate-400 italic py-2">
                No target entities associated with current case.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── MAIN VIDEO & TARGET ANALYSIS DRAWER SECTION ───────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
        
        {/* Large Video Display (8 cols) */}
        <div className="lg:col-span-8 bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 flex flex-col shadow-lg">
          <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden border border-[#1E2430] flex items-center justify-center">
            {mediaSrc ? (
              <video
                ref={videoRef}
                src={mediaSrc}
                autoPlay
                muted
                loop
                playsInline
                className="w-full h-full object-cover"
              />
            ) : (
              <img
                src="/assets/tile_cctv_bg.jpg"
                alt="Feed Stream"
                className="w-full h-full object-cover"
              />
            )}

            {/* Real YOLOv8 Bounding Box Overlay Layer */}
            {viewMode === 'analyzed' && currentFrame && currentFrame.detections && currentFrame.detections.length > 0 && (
              <div className="absolute inset-0 pointer-events-none z-10">
                {currentFrame.detections.map((det: RealDetection, idx: number) => {
                  if (!det.normalized_bbox) return null;
                  const [x1, y1, x2, y2] = det.normalized_bbox;
                  const color = getClassColor(det.class);
                  return (
                    <div
                      key={idx}
                      className="absolute border-2 transition-all duration-100 shadow-md"
                      style={{
                        top: `${y1 * 100}%`,
                        left: `${x1 * 100}%`,
                        width: `${(x2 - x1) * 100}%`,
                        height: `${(y2 - y1) * 100}%`,
                        borderColor: color,
                        backgroundColor: `${color}18`
                      }}
                    >
                      <span
                        className="absolute -top-4 left-0 text-[9px] font-mono font-black px-1.5 py-0.2 rounded text-black shadow uppercase whitespace-nowrap"
                        style={{ backgroundColor: color }}
                      >
                        {det.class} {det.confidence.toFixed(2)}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {/* HUD Target Lock Badge Overlay */}
            {analyticsMode === 'CASE_TARGET' && selectedTarget && (
              <div className="absolute top-3 left-3 bg-black/85 backdrop-blur-md px-3 py-1.5 rounded-md border border-cyan-500/40 text-[10px] font-mono space-y-0.5 z-20">
                <div className="text-cyan-400 font-extrabold flex items-center">
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse mr-2" />
                  TARGET LOCK: {selectedTarget.name.toUpperCase()} ({selectedTarget.role})
                </div>
                <div className="text-slate-300 text-[9px]">
                  SOURCE: {camera?.camera_code || 'CAM-DEL-15'} · MODE B CASE-FOCUSED
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: TARGET ANALYSIS & INVESTIGATION RESULTS (4 cols) ────── */}
        <div className="lg:col-span-4 bg-[#11141C] border border-[#1E2430] rounded-xl p-4 flex flex-col justify-between shadow-lg space-y-3">
          <div>
            <div className="flex items-center justify-between border-b border-[#1E2430] pb-2.5 mb-3">
              <h3 className="text-xs font-black text-white uppercase tracking-wider flex items-center space-x-2">
                <Shield className="w-4 h-4 text-cyan-400" />
                <span>TARGET ANALYSIS RESULTS</span>
              </h3>
              <span className="text-[10px] font-mono text-cyan-400 font-bold bg-cyan-950 px-2 py-0.5 rounded border border-cyan-600/40">
                {observations.length} Matches
              </span>
            </div>

            {/* Observations List */}
            <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
              {observations.map((obs) => (
                <div key={obs.id} className="bg-[#161922] border border-[#1E2430] rounded-lg p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 font-mono text-xs">
                      <span className="font-extrabold text-cyan-400">{obs.timestamp}</span>
                      <span className="text-slate-500">·</span>
                      <span className="text-slate-300 font-bold">{obs.cameraCode}</span>
                    </div>
                    <span className="text-[10px] font-mono font-extrabold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-600/40">
                      {obs.matchScore} Cosine
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-bold truncate">{obs.targetName}</span>
                    <span className={`text-[9px] font-extrabold uppercase px-1.5 py-0.2 rounded border ${
                      obs.decision === 'ACCEPTED' ? 'bg-emerald-950 text-emerald-400 border-emerald-600/40' :
                      obs.decision === 'CHALLENGED' ? 'bg-amber-950 text-amber-400 border-amber-600/40' :
                      obs.decision === 'DISMISSED' ? 'bg-red-950 text-red-400 border-red-600/40' :
                      'bg-blue-950 text-blue-400 border-blue-600/40'
                    }`}>
                      {obs.decision}
                    </span>
                  </div>

                  {/* Decision Action Buttons */}
                  <div className="flex items-center space-x-1.5 pt-1 border-t border-[#1E2430]/60">
                    <button
                      onClick={() => handleDecision(obs.id, 'ACCEPTED')}
                      className="flex-1 bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 text-[10px] font-bold py-1 rounded border border-emerald-600/40 transition-colors cursor-pointer"
                    >
                      ACCEPT
                    </button>
                    <button
                      onClick={() => handleDecision(obs.id, 'CHALLENGED')}
                      className="flex-1 bg-amber-950/80 hover:bg-amber-900 text-amber-300 text-[10px] font-bold py-1 rounded border border-amber-600/40 transition-colors cursor-pointer"
                    >
                      CHALLENGE
                    </button>
                    <button
                      onClick={() => handleDecision(obs.id, 'DISMISSED')}
                      className="flex-1 bg-red-950/80 hover:bg-red-900 text-red-300 text-[10px] font-bold py-1 rounded border border-red-600/40 transition-colors cursor-pointer"
                    >
                      DISMISS
                    </button>
                  </div>
                </div>
              ))}

              {observations.length === 0 && (
                <div className="py-12 text-center text-slate-500 text-xs font-semibold">
                  {analysisStatus === 'RUNNING' ? 'Searching video feed for selected target...' : 'Select a target and click "Analyze Target in Video" to begin.'}
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};

