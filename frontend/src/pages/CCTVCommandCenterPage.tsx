import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { cctvApi } from '../api/cctv';
import type { Camera, CameraDetail } from '../api/cctv';
import { casesApi } from '../api/cases';
import type { CaseListItem } from '../types/api';
import { FeedViewer } from '../components/cctv/FeedViewer';
import { 
  RefreshCw, 
  Search, 
  Camera as CameraIcon, 
  MapPin, 
  Play, 
  ExternalLink,
  ChevronRight,
  FolderOpen,
  Camera as CaptureIcon,
  Flag,
  FilePlus,
  Download,
  Users,
  Car,
  FileText,
  Boxes,
  Maximize2,
  Volume2,
  RotateCcw,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Zap,
  Clock
} from 'lucide-react';

export const CCTVCommandCenterPage: React.FC = () => {
  const navigate = useNavigate();

  const [cameras, setCameras] = useState<Camera[]>([]);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('');
  const [selectedCase, setSelectedCase] = useState<CaseListItem | null>(null);
  
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null);
  const [cameraDetail, setCameraDetail] = useState<CameraDetail | null>(null);
  
  const [isSyncing, setIsSyncing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMode, setFilterMode] = useState<'all' | 'live' | 'reachable' | 'offline'>('all');
  const [activeTab, setActiveTab] = useState<'detections' | 'events' | 'map' | 'logs'>('detections');
  const [aiCorrelationStatus, setAiCorrelationStatus] = useState<'PENDING' | 'ACCEPTED' | 'CHALLENGED' | 'DISMISSED'>('PENDING');

  useEffect(() => {
    fetchCameras();
    fetchCases();
  }, []);

  useEffect(() => {
    if (selectedCaseId) {
      const match = cases.find(c => c.case_id === selectedCaseId);
      setSelectedCase(match || null);
    } else {
      setSelectedCase(null);
    }
  }, [selectedCaseId, cases]);

  useEffect(() => {
    if (selectedCameraId) {
      cctvApi.getCameraDetail(selectedCameraId)
        .then(data => setCameraDetail(data))
        .catch(err => console.error(err));
    } else {
      setCameraDetail(null);
    }
  }, [selectedCameraId]);

  const fetchCameras = () => {
    cctvApi.listCameras()
      .then(data => {
        setCameras(data);
        if (data.length > 0 && !selectedCameraId) {
          setSelectedCameraId(data[0].camera_id);
        }
      })
      .catch(err => console.error(err));
  };

  const fetchCases = () => {
    casesApi.listCases()
      .then(data => {
        setCases(data);
        if (data.length > 0 && !selectedCaseId) {
          setSelectedCaseId(data[0].case_id);
        }
      })
      .catch(err => console.error(err));
  };

  const syncRegistry = () => {
    setIsSyncing(true);
    cctvApi.syncRegistry()
      .then(() => {
        fetchCameras();
      })
      .catch(err => {
        console.error(err);
        alert('Failed to sync registry.');
      })
      .finally(() => setIsSyncing(false));
  };

  const handleRunAnalysis = () => {
    if (!selectedCameraId) return;
    navigate(`/cctv/analysis/${selectedCameraId}${selectedCaseId ? `?case_id=${selectedCaseId}` : ''}`);
  };

  // Filtering cameras
  const filteredCameras = cameras.filter(c => {
    const matchesSearch = c.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.camera_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.city.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (!matchesSearch) return false;

    if (filterMode === 'live') return c.status === 'LIVE' || c.status === 'REGISTERED_ONLY';
    if (filterMode === 'reachable') return c.status === 'LIVE' || c.status === 'REGISTERED_ONLY';
    if (filterMode === 'offline') return c.status === 'OFFLINE' || c.status === 'DISCONNECTED';
    return true;
  });

  const liveCount = cameras.filter(c => c.status === 'LIVE' || c.status === 'REGISTERED_ONLY').length;
  const offlineCount = cameras.length - liveCount;

  // Selected camera details helper
  const camera = cameraDetail?.camera;

  return (
    <div className="space-y-3.5 max-w-[1920px] mx-auto pb-8 select-none font-sans text-white bg-[#0A0C10] p-3 rounded-xl min-h-screen">
      
      {/* ── 1. GLOBAL WORKSTATION HEADER ────────────────────────────────────────── */}
      <div className="bg-[#11141C] border border-[#1E2430] rounded-xl px-5 py-2.5 flex flex-col md:flex-row justify-between items-start md:items-center shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="p-2.5 bg-blue-600/20 border border-blue-500/40 rounded-xl text-blue-400 shadow-md">
            <CameraIcon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-black text-white tracking-tight uppercase">
                CCTV INTELLIGENCE
              </h1>
            </div>
            <p className="text-xs text-slate-400 font-semibold tracking-wide">
              Video Intelligence. Identify. Correlate. Investigate.
            </p>
          </div>
        </div>

        <div className="mt-2 md:mt-0 flex items-center space-x-4">
          <div className="text-right">
            <div className="text-[11px] font-black tracking-widest text-slate-300 uppercase">"SAFER CITIES</div>
            <div className="text-[11px] font-black tracking-widest text-[#E6B325] uppercase">STRONGER COMMUNITIES"</div>
          </div>
        </div>
      </div>



      {/* ── 3. MAIN 3-COLUMN CCTV WORKSTATION LAYOUT ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-start">
        
        {/* ── COLUMN 1: CAMERA SOURCES RAIL (3 Cols) ───────────────────────── */}
        <div className="lg:col-span-3 bg-[#11141C] border border-[#1E2430] rounded-xl p-3 flex flex-col shadow-lg">
          
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#1E2430] pb-2 mb-2.5">
            <div className="flex items-center space-x-2">
              <CameraIcon className="w-4 h-4 text-blue-400" />
              <h2 className="text-xs font-black text-white uppercase tracking-wider">CAMERA SOURCES</h2>
              <span className="text-[10px] font-mono text-slate-400">({cameras.length})</span>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative mb-2.5">
            <input 
              type="text" 
              placeholder="Search cameras, locations or area..."
              className="w-full bg-[#161922] border border-[#1E2430] focus:border-slate-500 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none transition-colors"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
            <Search className="absolute left-2.5 top-2 text-slate-400" size={13} />
          </div>

          {/* Filter Pills */}
          <div className="flex items-center space-x-1 mb-2.5 text-[10px] font-bold">
            <button 
              onClick={() => setFilterMode('all')}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterMode === 'all' ? 'bg-blue-600 text-white' : 'bg-[#161922] text-slate-400 hover:text-white border border-[#1E2430]'
              }`}
            >
              All {cameras.length}
            </button>
            <button 
              onClick={() => setFilterMode('live')}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterMode === 'live' ? 'bg-emerald-600 text-white' : 'bg-[#161922] text-slate-400 hover:text-white border border-[#1E2430]'
              }`}
            >
              Live {liveCount}
            </button>
            <button 
              onClick={() => setFilterMode('reachable')}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterMode === 'reachable' ? 'bg-teal-600 text-white' : 'bg-[#161922] text-slate-400 hover:text-white border border-[#1E2430]'
              }`}
            >
              Reachable 24
            </button>
            <button 
              onClick={() => setFilterMode('offline')}
              className={`px-2.5 py-1 rounded transition-colors ${
                filterMode === 'offline' ? 'bg-red-600 text-white' : 'bg-[#161922] text-slate-400 hover:text-white border border-[#1E2430]'
              }`}
            >
              Offline {offlineCount}
            </button>
          </div>

          {/* Camera List */}
          <div className="max-h-[640px] overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {filteredCameras.map((cam) => {
              const isSelected = cam.camera_id === selectedCameraId;
              const isLive = cam.status === 'LIVE' || cam.status === 'REGISTERED_ONLY';
              
              return (
                <div 
                  key={cam.camera_id}
                  onClick={() => setSelectedCameraId(cam.camera_id)}
                  className={`p-2 rounded-xl border cursor-pointer transition-all flex items-center space-x-3 ${
                    isSelected 
                      ? 'bg-[#161922] border-blue-500 ring-1 ring-blue-500/40 shadow-lg' 
                      : 'bg-[#161922]/70 border-[#1E2430] hover:border-slate-600 hover:bg-[#161922]'
                  }`}
                >
                  <div className="w-16 h-11 rounded-lg bg-black overflow-hidden flex-shrink-0 relative border border-[#1E2430]">
                    <img 
                      src={`/assets/tile_cctv_bg.jpg`} 
                      alt={cam.display_name} 
                      className="w-full h-full object-cover opacity-80"
                    />
                    <div className="absolute top-1 left-1 w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="font-extrabold text-xs text-white truncate" title={cam.display_name}>
                        {cam.camera_code}
                      </h4>
                      {isLive && (
                        <span className="text-[8px] font-black text-emerald-400 bg-emerald-950 px-1 py-0.2 rounded border border-emerald-600/40 uppercase">
                          LIVE
                        </span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-300 truncate mt-0.5">{cam.display_name}</p>
                    <div className="flex items-center text-[9px] text-slate-400 mt-0.5 space-x-1">
                      <MapPin size={10} className="text-blue-400 flex-shrink-0" />
                      <span className="truncate">{cam.city}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

        </div>

        {/* ── COLUMN 2: SELECTED CAMERA WORKSPACE & DETECTIONS (6 Cols) ───────── */}
        <div className="lg:col-span-6 space-y-3 flex flex-col">
          
          {/* Main Feed Video Viewport */}
          <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-3 shadow-lg flex flex-col">
            
            {/* Stream Header */}
            <div className="flex items-center justify-between border-b border-[#1E2430] pb-2 mb-2 text-xs">
              <div className="flex items-center space-x-2 truncate">
                <span className="flex items-center text-emerald-400 font-bold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-600/40 text-[10px]">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse mr-1" />
                  LIVE
                </span>
                <span className="font-mono text-white font-extrabold">{camera ? camera.camera_code : 'CAM-DEL-15'}</span>
                <span className="text-slate-500">|</span>
                <span className="font-bold text-slate-200 truncate">{camera ? camera.display_name : 'Akshardham Temple Flyover Loop'}</span>
              </div>

              <div className="flex items-center text-[10px] text-slate-400 font-mono space-x-2 flex-shrink-0">
                <MapPin size={11} className="text-blue-400" />
                <span>Delhi</span>
                <span>04 Sep 2026 19:52:17 IST</span>
                <button className="text-slate-400 hover:text-white ml-1">
                  <Maximize2 size={13} />
                </button>
              </div>
            </div>

            {/* Video Box - Expanded Viewport */}
            <div className="relative w-full min-h-[460px] lg:min-h-[520px] aspect-video rounded-lg overflow-hidden border border-[#1E2430] bg-black shadow-inner">
              <FeedViewer cameraData={cameraDetail} />
              
              {/* Overlay Watermarks & Bounding Box Simulations matching visual lock */}
              <div className="absolute top-3 left-3 bg-black/60 backdrop-blur-sm border border-slate-700/60 px-2.5 py-1 rounded text-[10px] font-mono text-white pointer-events-none">
                <div className="font-bold">{camera ? camera.display_name : 'Akshardham Temple Flyover'}</div>
                <div className="text-slate-400 text-[9px]">{camera ? camera.camera_code : 'CAM-DEL-15'}</div>
                <div className="text-slate-400 text-[9px]">04-09-2026 19:52:17</div>
              </div>

              <div className="absolute top-3 right-3 bg-black/70 backdrop-blur-sm border border-yellow-500/40 px-2.5 py-1 rounded text-[10px] font-mono text-white font-bold text-right pointer-events-none">
                <div className="text-[#E6B325]">DELHI POLICE</div>
                <div className="text-slate-300 text-[8px]">CCTV NETWORK</div>
              </div>

              {/* Bounding Boxes */}
              <div className="absolute top-[42%] left-[37%] border-2 border-cyan-400 bg-cyan-500/10 px-2 py-1 rounded text-[9px] font-mono font-bold text-cyan-300 shadow-md">
                VEHICLE_12
              </div>
              <div className="absolute top-[48%] left-[50%] border-2 border-emerald-400 bg-emerald-500/10 px-2 py-1 rounded text-[9px] font-mono font-bold text-emerald-300 shadow-md">
                PERSON_04
              </div>

              {/* Video Player Controls Bar */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-2.5 flex items-center justify-between text-xs text-white">
                <div className="flex items-center space-x-3">
                  <button className="hover:text-blue-400"><Play size={16} fill="white" /></button>
                  <button className="hover:text-blue-400"><RotateCcw size={14} /></button>
                  <button className="hover:text-blue-400"><RotateCw size={14} /></button>
                  <span className="font-mono text-[11px] text-slate-300">19:52:17 / 23:00:00</span>
                </div>
                <div className="flex items-center space-x-3">
                  <button className="hover:text-blue-400"><Volume2 size={14} /></button>
                  <span className="font-mono text-[10px] bg-slate-800 px-1.5 py-0.5 rounded">1x</span>
                  <button className="hover:text-blue-400"><Maximize2 size={14} /></button>
                </div>
              </div>

            </div>

          </div>

          {/* 2 Sub-Panels: Investigation Clips & AI Correlations */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
            
            {/* Investigation Clips Sub-Panel (7 cols) */}
            <div className="md:col-span-7 bg-[#11141C] border border-[#1E2430] rounded-xl p-3 shadow">
              <div className="flex items-center justify-between mb-2 pb-1 border-b border-[#1E2430]">
                <h3 className="text-xs font-black text-white uppercase tracking-wider">INVESTIGATION CLIPS (12)</h3>
                <button className="text-[10px] font-bold text-blue-400 hover:text-blue-300 flex items-center">
                  View All Clips <ChevronRight size={11} />
                </button>
              </div>

              <div className="grid grid-cols-5 gap-1.5">
                {[
                  { time: '19:48:12', clip: 'CLIP-0192', tag: 'Vehicle Detected' },
                  { time: '19:45:03', clip: 'CLIP-0187', tag: 'Person Detected' },
                  { time: '19:41:27', clip: 'CLIP-0176', tag: 'Suspicious Activity' },
                  { time: '19:38:11', clip: 'CLIP-0169', tag: 'Vehicle Follow' },
                  { time: '19:32:46', clip: 'CLIP-0154', tag: 'Group Detected' },
                ].map((item, idx) => (
                  <div key={idx} className="bg-[#161922] border border-[#1E2430] hover:border-slate-500 rounded p-1 flex flex-col justify-between cursor-pointer transition-colors">
                    <div className="w-full h-10 bg-black rounded overflow-hidden relative border border-slate-800 mb-1">
                      <img src="/assets/tile_cctv_bg.jpg" alt="Clip" className="w-full h-full object-cover opacity-70" />
                      <span className="absolute bottom-0.5 left-0.5 font-mono text-[7px] font-bold text-white bg-black/80 px-1 rounded">
                        {item.time}
                      </span>
                    </div>
                    <div className="text-[8px] font-mono text-slate-400 font-bold">{item.clip}</div>
                    <div className="text-[8px] font-extrabold text-slate-200 truncate">{item.tag}</div>
                    <button className="mt-1 w-full bg-blue-600/30 hover:bg-blue-600 text-blue-300 hover:text-white text-[8px] font-bold py-0.5 rounded text-center transition-colors">
                      Open Clip
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Correlations Sub-Panel (5 cols) */}
            <div className="md:col-span-5 bg-[#11141C] border border-[#1E2430] rounded-xl p-3 shadow flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2 pb-1 border-b border-[#1E2430]">
                <div className="flex items-center space-x-1.5">
                  <Zap size={13} className="text-[#E6B325]" />
                  <h3 className="text-xs font-black text-white uppercase tracking-wider">AI CORRELATIONS</h3>
                </div>
                <span className="text-[9px] font-extrabold text-red-400 bg-red-950 px-1.5 py-0.2 rounded border border-red-600/40">
                  ⚡ 1 HIGH PRIORITY
                </span>
              </div>

              {/* Person Card */}
              <div className="bg-[#161922] border border-[#1E2430] rounded-lg p-2 flex space-x-2.5 items-center">
                <div className="w-14 h-14 bg-black rounded-lg border border-emerald-500/40 overflow-hidden flex-shrink-0 relative">
                  <img src="/assets/tile_cctv_bg.jpg" alt="Target" className="w-full h-full object-cover" />
                  <span className="absolute bottom-0 left-0 right-0 bg-emerald-600/90 text-white text-[7px] font-black text-center py-0.2">
                    0.81 MATCH
                  </span>
                </div>
                <div className="flex-1 min-w-0 text-[10px]">
                  <div className="font-black text-white text-xs">PERSON_04</div>
                  <div className="text-emerald-400 font-bold">Potential Match</div>
                  <div className="text-slate-400 text-[9px]">Similarity: <span className="text-white font-mono font-bold">0.81</span></div>
                  <div className="text-slate-400 text-[9px] truncate">Seen at: CAM-DEL-15 19:52:17</div>
                  <div className="text-slate-400 text-[9px] truncate">Related: CIV-2012-001</div>
                </div>
              </div>

              {/* Investigator Decision Buttons */}
              <div className="grid grid-cols-3 gap-1.5 mt-2">
                <button 
                  onClick={() => setAiCorrelationStatus('ACCEPTED')}
                  className={`text-[9px] font-bold py-1 px-1.5 rounded text-center transition-colors flex items-center justify-center space-x-1 ${
                    aiCorrelationStatus === 'ACCEPTED' 
                      ? 'bg-emerald-600 text-white font-black' 
                      : 'bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-600/50 text-emerald-300'
                  }`}
                >
                  <CheckCircle2 size={10} />
                  <span>Accept</span>
                </button>
                <button 
                  onClick={() => setAiCorrelationStatus('CHALLENGED')}
                  className={`text-[9px] font-bold py-1 px-1.5 rounded text-center transition-colors flex items-center justify-center space-x-1 ${
                    aiCorrelationStatus === 'CHALLENGED' 
                      ? 'bg-amber-600 text-white font-black' 
                      : 'bg-amber-950/80 hover:bg-amber-900 border border-amber-600/50 text-amber-300'
                  }`}
                >
                  <AlertTriangle size={10} />
                  <span>Challenge</span>
                </button>
                <button 
                  onClick={() => setAiCorrelationStatus('DISMISSED')}
                  className={`text-[9px] font-bold py-1 px-1.5 rounded text-center transition-colors flex items-center justify-center space-x-1 ${
                    aiCorrelationStatus === 'DISMISSED' 
                      ? 'bg-red-600 text-white font-black' 
                      : 'bg-red-950/80 hover:bg-red-900 border border-red-600/50 text-red-300'
                  }`}
                >
                  <XCircle size={10} />
                  <span>Dismiss</span>
                </button>
              </div>

            </div>

          </div>

        </div>

        {/* ── COLUMN 3: CAMERA DETAILS & ANALYSIS PANEL (3 Cols) ──────────────── */}
        <div className="lg:col-span-3 bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 flex flex-col justify-between shadow-lg space-y-3">
          
          <div>
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1E2430] pb-2 mb-2.5">
              <h2 className="text-xs font-black text-white uppercase tracking-wider">ANALYSIS & DETAILS</h2>
              <span className="text-[9px] font-black text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-600/40 uppercase">
                LIVE
              </span>
            </div>

            {/* Title & Location */}
            <div className="mb-3">
              <h3 className="text-sm font-black text-white leading-tight">
                {camera ? camera.display_name : 'Akshardham Temple Flyover Loop'}
              </h3>
              <div className="flex items-center text-xs text-slate-400 mt-1 space-x-1">
                <MapPin size={11} className="text-blue-400 flex-shrink-0" />
                <span>Delhi, East Delhi</span>
              </div>
            </div>

            {/* Metadata Table */}
            <div className="space-y-1.5 text-[11px] border-t border-[#1E2430] pt-2.5">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Camera ID</span>
                <span className="font-mono font-bold text-white bg-[#161922] px-1.5 py-0.5 rounded border border-[#1E2430]">
                  {camera ? camera.camera_code : 'CAM-DEL-15'}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400">Coordinates</span>
                <span className="font-mono text-slate-200 text-[10px]">
                  {camera ? `${camera.latitude.toFixed(4)}, ${camera.longitude.toFixed(4)}` : '28.6127, 77.2773'}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400">Area</span>
                <span className="text-slate-200 font-bold">Akshardham</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400">Operator</span>
                <span className="text-slate-300">TfL Open Data</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400">Feed Status</span>
                <span className="text-emerald-400 font-extrabold flex items-center text-[10px]">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1" />
                  Live · Reachable
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400">Last Sync</span>
                <span className="text-slate-300 text-[10px]">3 Sep 2026, 14:32</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400">Source</span>
                <span className="text-slate-300 text-[10px]">Delhi Police / TfL</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400">Type</span>
                <span className="text-slate-300 text-[10px]">Traffic / Surveillance</span>
              </div>
            </div>



          </div>

          {/* Primary Action & Quick Actions */}
          <div className="space-y-3 pt-2 border-t border-[#1E2430]">
            
            {/* Run Visual Analysis Red Button */}
            <button
              onClick={handleRunAnalysis}
              className="w-full bg-red-600 hover:bg-red-700 active:bg-red-800 text-white p-3 rounded-xl transition-all shadow-xl hover:shadow-red-600/30 flex flex-col items-center justify-center cursor-pointer group border border-red-500/50"
            >
              <div className="flex items-center space-x-2 mb-0.5">
                <Play className="w-4 h-4 fill-current text-white group-hover:scale-110 transition-transform" />
                <span className="text-sm font-black uppercase tracking-wider">RUN VISUAL ANALYSIS</span>
              </div>
              <span className="text-[9px] text-red-100 font-bold font-mono uppercase tracking-widest opacity-90">
                YOLOv8 – Detect People, Vehicles & More
              </span>
            </button>

            {/* Quick Actions Grid (4 Grid Buttons) */}
            <div>
              <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1.5">QUICK ACTIONS</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button className="flex flex-col items-center justify-center p-2 bg-[#161922] border border-[#1E2430] hover:border-slate-500 rounded-lg text-slate-200 hover:text-white transition-colors cursor-pointer text-center">
                  <CaptureIcon size={15} className="text-blue-400 mb-1" />
                  <span className="text-[9px] font-extrabold">Capture Frame</span>
                </button>
                <button className="flex flex-col items-center justify-center p-2 bg-[#161922] border border-[#1E2430] hover:border-slate-500 rounded-lg text-slate-200 hover:text-white transition-colors cursor-pointer text-center">
                  <Flag size={15} className="text-[#E6B325] mb-1" />
                  <span className="text-[9px] font-extrabold">Mark Event</span>
                </button>
                <button className="flex flex-col items-center justify-center p-2 bg-[#161922] border border-[#1E2430] hover:border-slate-500 rounded-lg text-slate-200 hover:text-white transition-colors cursor-pointer text-center">
                  <FilePlus size={15} className="text-emerald-400 mb-1" />
                  <span className="text-[9px] font-extrabold">Create Evidence</span>
                </button>
                <button className="flex flex-col items-center justify-center p-2 bg-[#161922] border border-[#1E2430] hover:border-slate-500 rounded-lg text-slate-200 hover:text-white transition-colors cursor-pointer text-center">
                  <Download size={15} className="text-cyan-400 mb-1" />
                  <span className="text-[9px] font-extrabold">Export Clip</span>
                </button>
              </div>
            </div>

          </div>

        </div>

      </div>

    </div>
  );
};
