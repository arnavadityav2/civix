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
  Layers
} from 'lucide-react';

export const VisualAnalysisPage: React.FC = () => {
  const { cameraId } = useParams<{ cameraId: string }>();
  const navigate = useNavigate();

  const [cameraDetail, setCameraDetail] = useState<CameraDetail | null>(null);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('');

  const [viewMode, setViewMode] = useState<'analyzed' | 'original'>('analyzed');
  const [analysisStatus, setAnalysisStatus] = useState<'IDLE' | 'STARTING' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'FAILED' | 'CANCELLED'>('IDLE');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [jobId, setJobId] = useState<string | null>(null);
  const [currentFrame, setCurrentFrame] = useState<LiveInferenceFrame | null>(null);
  const [detectionEvents, setDetectionEvents] = useState<string[]>([]);

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
        if (data.length > 0) setSelectedCaseId(data[0].case_id);
      })
      .catch(err => console.error(err));

    return () => {
      stopStreams();
    };
  }, [cameraId]);

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

    try {
      const res = await cctvApi.startSearchJob({
        case_id: selectedCaseId,
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
            setCurrentFrame(liveRes.latest_frame);
            if (liveRes.latest_frame.events && liveRes.latest_frame.events.length > 0) {
              setDetectionEvents(prev => [...liveRes.latest_frame!.events, ...prev].slice(0, 15));
            }
          }
          if (['COMPLETED', 'FAILED', 'CANCELLED'].includes(liveRes.status)) {
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
          }
        } catch (err) {
          console.error("Live frame fetch error:", err);
        }
      }, 200);

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

  const camera = cameraDetail?.camera;
  const feedUrl = cameraDetail?.feeds && cameraDetail.feeds.length > 0 ? cameraDetail.feeds[0].feed_url : null;

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
                YOLOv8 Visual Intelligence Workspace
              </h1>
              <span className="bg-red-600 text-white font-mono text-[9px] font-bold px-2 py-0.5 rounded uppercase shadow">
                Unwrapped Real Inference Engine
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium mt-0.5">
              {camera ? `${camera.display_name} (${camera.camera_code}) — ${camera.city}` : 'Loading camera details...'}
            </p>
          </div>
        </div>

        <div className="mt-3 md:mt-0 flex items-center space-x-3 w-full md:w-auto justify-between md:justify-end">
          {/* Active Case Selector */}
          <div className="flex items-center space-x-2 bg-[#161922] border border-[#1E2430] px-3 py-1.5 rounded-lg">
            <span className="text-[10px] uppercase font-extrabold text-[#E6B325] tracking-wider whitespace-nowrap">Case Context:</span>
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
                <span>Stop Analysis</span>
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
                <Cpu className="w-4 h-4" />
              )}
              <span>{analysisStatus === 'STARTING' ? 'Initializing Pipeline...' : 'Run YOLOv8 Analysis'}</span>
            </button>
          )}
        </div>
      </div>

      {/* ── ERROR STATE BANNER ─────────────────────────────────────────────── */}
      {analysisStatus === 'FAILED' && (
        <div className="bg-red-950/60 border border-red-600/60 rounded-xl px-4 py-3 flex items-center justify-between shadow-md">
          <div className="flex items-center space-x-3 text-red-200">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
            <div>
              <span className="text-xs font-black uppercase tracking-wider text-red-400">ANALYSIS FAILED / UNAVAILABLE</span>
              <p className="text-xs text-red-300 font-medium">{errorMessage || 'The computer-vision engine could not decode or process the selected video feed.'}</p>
            </div>
          </div>
          <button
            onClick={handleRunAnalysis}
            className="text-xs font-extrabold bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-md transition-colors cursor-pointer"
          >
            RETRY
          </button>
        </div>
      )}

      {/* ── ANALYSIS STATUS BAR ────────────────────────────────────────────── */}
      <div className="bg-[#11141C] border border-[#1E2430] rounded-xl px-4 py-2.5 flex items-center justify-between shadow">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Engine Status:</span>
            <span className={`px-2.5 py-0.5 rounded text-[10px] font-black uppercase tracking-wider border ${
              analysisStatus === 'COMPLETED' ? 'bg-emerald-950 text-emerald-400 border-emerald-600/50' :
              analysisStatus === 'RUNNING' ? 'bg-[#E6B325]/20 text-[#E6B325] border-[#E6B325]/50 animate-pulse' :
              analysisStatus === 'PAUSED' ? 'bg-amber-950 text-amber-400 border-amber-600/50' :
              analysisStatus === 'FAILED' ? 'bg-red-950 text-red-400 border-red-600/50' :
              'bg-blue-950 text-blue-400 border-blue-600/50'
            }`}>
              {analysisStatus === 'RUNNING' && currentFrame ? `RUNNING • FRAME ${currentFrame.frame_index} (${currentFrame.source_timestamp.toFixed(1)}s)` : 
               analysisStatus === 'PAUSED' ? 'INFERENCE PAUSED' :
               analysisStatus === 'COMPLETED' ? `ANALYSIS COMPLETED ${jobId ? `(JOB: ${jobId.split('-')[0]})` : ''}` :
               analysisStatus === 'FAILED' ? 'ANALYSIS FAILED' :
               'READY FOR INFERENCE'}
            </span>
          </div>

          {currentFrame && (
            <div className="flex items-center space-x-3 text-[10px] font-mono text-slate-400 border-l border-[#1E2430] pl-3">
              <span>FPS: <strong className="text-white">{currentFrame.inference_fps}</strong></span>
              <span>TIME/FRAME: <strong className="text-white">{currentFrame.inference_duration_ms} ms</strong></span>
              <span>ANALYZED: <strong className="text-white">{currentFrame.frames_analyzed}</strong></span>
            </div>
          )}
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center space-x-1 bg-[#161922] p-1 rounded-lg border border-[#1E2430]">
          <button
            onClick={() => setViewMode('original')}
            className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
              viewMode === 'original' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            ORIGINAL FEED
          </button>
          <button
            onClick={() => setViewMode('analyzed')}
            className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
              viewMode === 'analyzed' ? 'bg-red-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            YOLOv8 OVERLAY
          </button>
        </div>
      </div>

      {/* ── MAIN VIDEO & DETECTION OVERLAY SECTION ───────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
        
        {/* Large Video Display (8 cols) */}
        <div className="lg:col-span-8 bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 flex flex-col shadow-lg">
          <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden border border-[#1E2430] flex items-center justify-center">
            {feedUrl ? (
              <video
                src={feedUrl}
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

            {/* HUD Overlay Text */}
            <div className="absolute top-3 left-3 bg-black/85 backdrop-blur-md px-3 py-1.5 rounded-md border border-white/15 text-[10px] font-mono space-y-0.5 z-20">
              <div className="text-white font-bold flex items-center">
                <span className={`w-2 h-2 rounded-full mr-2 ${analysisStatus === 'RUNNING' ? 'bg-red-500 animate-pulse' : 'bg-slate-500'}`} />
                {camera?.display_name || 'CAM-DEL-01'}
              </div>
              <div className="text-slate-400">
                {currentFrame ? `${currentFrame.model_name} (v${currentFrame.model_version}) • ${currentFrame.frame_width}x${currentFrame.frame_height}` : 'YOLOv8 Engine • Standby'}
              </div>
            </div>

            {/* Telemetry Tag Bottom Right */}
            {currentFrame && (
              <div className="absolute bottom-3 right-3 bg-black/85 backdrop-blur-md px-2.5 py-1 rounded border border-white/15 text-[9px] font-mono text-slate-300 z-20">
                FRAME: {currentFrame.frame_index} | PTS: {currentFrame.source_timestamp.toFixed(2)}s | INFERENCE: {currentFrame.inference_duration_ms}ms
              </div>
            )}
          </div>
        </div>

        {/* Right Telemetry & Metrics Panel (4 cols) */}
        <div className="lg:col-span-4 space-y-3.5 flex flex-col justify-between">
          
          {/* Real Counters Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 shadow">
              <div className="flex items-center justify-between text-emerald-400 mb-1">
                <User size={18} />
                <span className="text-[9px] font-mono font-bold bg-emerald-950 px-1.5 py-0.5 rounded border border-emerald-600/40">CURRENT</span>
              </div>
              <p className="text-[10px] text-slate-400 font-extrabold uppercase">Persons Detected</p>
              <p className="text-2xl font-black text-white mt-0.5">
                {currentFrame?.current_frame_counts?.person ?? 0}
              </p>
            </div>

            <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 shadow">
              <div className="flex items-center justify-between text-blue-400 mb-1">
                <Car size={18} />
                <span className="text-[9px] font-mono font-bold bg-blue-950 px-1.5 py-0.5 rounded border border-blue-600/40">CURRENT</span>
              </div>
              <p className="text-[10px] text-slate-400 font-extrabold uppercase">Vehicles Detected</p>
              <p className="text-2xl font-black text-white mt-0.5">
                {(currentFrame?.current_frame_counts?.car ?? 0) + 
                 (currentFrame?.current_frame_counts?.bus ?? 0) + 
                 (currentFrame?.current_frame_counts?.truck ?? 0)}
              </p>
            </div>

            <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 shadow">
              <div className="flex items-center justify-between text-amber-400 mb-1">
                <Bike size={18} />
                <span className="text-[9px] font-mono font-bold bg-amber-950 px-1.5 py-0.5 rounded border border-amber-600/40">CURRENT</span>
              </div>
              <p className="text-[10px] text-slate-400 font-extrabold uppercase">Motorcycles</p>
              <p className="text-2xl font-black text-white mt-0.5">
                {currentFrame?.current_frame_counts?.motorcycle ?? 0}
              </p>
            </div>

            <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 shadow">
              <div className="flex items-center justify-between text-purple-400 mb-1">
                <Layers size={18} />
                <span className="text-[9px] font-mono font-bold bg-purple-950 px-1.5 py-0.5 rounded border border-purple-600/40">TRACKED</span>
              </div>
              <p className="text-[10px] text-slate-400 font-extrabold uppercase">Tracked Objects</p>
              <p className="text-2xl font-black text-white mt-0.5">
                {currentFrame?.total_tracked_objects ?? 0}
              </p>
            </div>
          </div>

          {/* Engine Model Transparency & ANPR Status */}
          <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 space-y-2 shadow">
            <h3 className="text-xs font-black text-white uppercase tracking-wider border-b border-[#1E2430] pb-1.5 flex items-center justify-between">
              <span>Model Telemetry</span>
              <span className="text-[9px] font-mono text-slate-400">YOLOv8 Engine</span>
            </h3>
            
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-[#161922] p-2 rounded border border-[#1E2430]">
                <span className="text-[9px] text-slate-400 font-bold block uppercase">MODEL VERSION</span>
                <span className="font-mono text-white font-bold">{currentFrame?.model_version || '8.4.138'}</span>
              </div>
              <div className="bg-[#161922] p-2 rounded border border-[#1E2430]">
                <span className="text-[9px] text-slate-400 font-bold block uppercase">EXECUTION DEVICE</span>
                <span className="font-mono text-emerald-400 font-bold">{currentFrame?.device || 'CPU'}</span>
              </div>
              <div className="bg-[#161922] p-2 rounded border border-[#1E2430]">
                <span className="text-[9px] text-slate-400 font-bold block uppercase">SOURCE RESOLUTION</span>
                <span className="font-mono text-white font-bold">{currentFrame ? `${currentFrame.frame_width}x${currentFrame.frame_height}` : 'N/A'}</span>
              </div>
              <div className="bg-[#161922] p-2 rounded border border-[#1E2430]">
                <span className="text-[9px] text-slate-400 font-bold block uppercase">ANPR / OCR ENGINE</span>
                <span className="font-mono text-slate-400 font-bold text-[10px]">NOT AVAILABLE</span>
              </div>
            </div>
          </div>

          {/* Real Detection Events Log */}
          <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 flex-1 flex flex-col shadow">
            <h3 className="text-xs font-black text-white uppercase tracking-wider mb-2 flex items-center border-b border-[#1E2430] pb-2">
              <Activity size={14} className="text-blue-400 mr-2" />
              Real Inference Events ({detectionEvents.length})
            </h3>

            <div className="space-y-1.5 overflow-y-auto max-h-[160px] pr-1">
              {detectionEvents.length > 0 ? (
                detectionEvents.map((evt, i) => (
                  <div key={i} className="bg-[#161922] border border-[#1E2430] rounded px-2.5 py-1.5 flex items-center justify-between text-xs">
                    <span className="text-slate-200 font-medium">{evt}</span>
                    <span className="text-[9px] font-mono text-slate-500">
                      {currentFrame ? `${currentFrame.source_timestamp.toFixed(1)}s` : ''}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 italic py-3 text-center">
                  {analysisStatus === 'RUNNING' ? 'Awaiting detection events from model...' : 'Start YOLOv8 analysis to record events.'}
                </p>
              )}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
