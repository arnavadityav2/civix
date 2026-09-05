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
  Search as SearchIcon,
  Map as MapIcon,
  Activity
} from 'lucide-react';

export const CCTVCommandCenterPage: React.FC = () => {
  const navigate = useNavigate();

  const [cameras, setCameras] = useState<Camera[]>([]);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('');
  
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null);
  const [cameraDetail, setCameraDetail] = useState<CameraDetail | null>(null);
  
  const [isSyncing, setIsSyncing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterMode, setFilterMode] = useState<'all' | 'live' | 'reachable' | 'offline'>('all');

  useEffect(() => {
    fetchCameras();
    fetchCases();
  }, []);

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
    navigate(`/cctv/analysis/${selectedCameraId}`);
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
    <div className="space-y-4 max-w-[1850px] mx-auto pb-8 select-none font-sans text-white">
      
      {/* ── 1. CIVIX CCTV WORKSTATION HEADER BANNER ───────────────────────────── */}
      <div className="bg-[#11141C] border border-[#1E2430] rounded-xl px-5 py-3 flex flex-col md:flex-row justify-between items-start md:items-center shadow-lg">
        <div className="flex items-center space-x-3.5">
          <div className="p-2.5 bg-red-600/20 border border-red-500/40 rounded-xl text-red-500 shadow-md">
            <CameraIcon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-black text-white tracking-tight uppercase">
                CCTV ANALYSIS
              </h1>
            </div>
            <p className="text-xs text-slate-400 font-semibold tracking-wide mt-0.5">
              Video Intelligence. Identify. Correlate. Investigate.
            </p>
          </div>
        </div>

        <div className="mt-3 md:mt-0 flex flex-wrap md:flex-nowrap items-center space-x-3 w-full md:w-auto justify-between md:justify-end">
          
          {/* Active Case Context Selector */}
          <div className="flex items-center space-x-2 bg-[#161922] border border-[#1E2430] px-3 py-1.5 rounded-lg shadow-sm">
            <FolderOpen className="w-4 h-4 text-[#E6B325]" />
            <div className="flex flex-col">
              <span className="text-[9px] uppercase font-black text-[#E6B325] tracking-wider leading-none">CASE CONTEXT</span>
              <select 
                className="bg-transparent text-xs font-bold text-white focus:outline-none cursor-pointer max-w-[260px] truncate"
                value={selectedCaseId}
                onChange={(e) => setSelectedCaseId(e.target.value)}
              >
                <option value="" className="bg-[#11141C] text-slate-300">-- Select Active Case --</option>
                {cases.map(c => (
                  <option key={c.case_id} value={c.case_id} className="bg-[#11141C] text-white">
                    {c.case_number} - {c.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Sync Registry Button */}
          <button 
            onClick={syncRegistry}
            disabled={isSyncing}
            className="flex items-center space-x-1.5 text-xs font-bold text-slate-200 hover:text-white bg-[#161922] border border-[#1E2430] hover:border-slate-500 px-3.5 py-2 rounded-lg transition-colors shadow cursor-pointer"
          >
            <RefreshCw size={13} className={`text-slate-400 ${isSyncing ? 'animate-spin' : ''}`} />
            <span>{isSyncing ? 'Syncing...' : 'Sync Registry'}</span>
          </button>

          {/* Motto Tagline */}
          <div className="hidden xl:flex flex-col text-right pl-3 border-l border-[#1E2430]">
            <span className="text-[10px] font-black tracking-widest text-slate-300">A SAFER DELHI</span>
            <span className="text-[10px] font-black tracking-widest text-[#E6B325]">A STRONGER INDIA</span>
          </div>

        </div>
      </div>

      {/* ── 2. MAIN 3-COLUMN CCTV WORKSTATION LAYOUT ────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        
        {/* ── COLUMN 1: CAMERA SOURCES RAIL (3 Cols) ───────────────────────── */}
        <div className="lg:col-span-3 bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 flex flex-col shadow-lg">
          
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[#1E2430] pb-2.5 mb-3">
            <div className="flex items-center space-x-2">
              <CameraIcon className="w-4 h-4 text-blue-400" />
              <h2 className="text-xs font-black text-white uppercase tracking-wider">CAMERA SOURCES</h2>
            </div>
            <span className="text-[10px] font-mono font-bold text-slate-400 bg-[#161922] px-2 py-0.5 rounded border border-[#1E2430]">
              {cameras.length} Cameras
            </span>
          </div>

          {/* Search Bar */}
          <div className="relative mb-3">
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
          <div className="flex items-center space-x-1.5 mb-3 overflow-x-auto pb-1 text-[10px] font-bold">
            <button 
              onClick={() => setFilterMode('all')}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                filterMode === 'all' ? 'bg-blue-600 text-white' : 'bg-[#161922] text-slate-400 hover:text-white border border-[#1E2430]'
              }`}
            >
              All <span className="font-mono text-[9px] opacity-80">{cameras.length}</span>
            </button>
            <button 
              onClick={() => setFilterMode('live')}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                filterMode === 'live' ? 'bg-emerald-600 text-white' : 'bg-[#161922] text-slate-400 hover:text-white border border-[#1E2430]'
              }`}
            >
              Live <span className="font-mono text-[9px] opacity-80">{liveCount}</span>
            </button>
            <button 
              onClick={() => setFilterMode('reachable')}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                filterMode === 'reachable' ? 'bg-[#E6B325] text-black font-extrabold' : 'bg-[#161922] text-slate-400 hover:text-white border border-[#1E2430]'
              }`}
            >
              Reachable <span className="font-mono text-[9px] opacity-80">{liveCount}</span>
            </button>
            <button 
              onClick={() => setFilterMode('offline')}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                filterMode === 'offline' ? 'bg-red-600 text-white' : 'bg-[#161922] text-slate-400 hover:text-white border border-[#1E2430]'
              }`}
            >
              Offline <span className="font-mono text-[9px] opacity-80">{offlineCount}</span>
            </button>
          </div>

          {/* Scrollable Camera Cards Container (Strictly internal scroll!) */}
          <div className="max-h-[620px] overflow-y-auto space-y-2.5 pr-1 custom-scrollbar">
            {filteredCameras.map((cam) => {
              const isSelected = cam.camera_id === selectedCameraId;
              const isLive = cam.status === 'LIVE' || cam.status === 'REGISTERED_ONLY';
              
              return (
                <div 
                  key={cam.camera_id}
                  onClick={() => setSelectedCameraId(cam.camera_id)}
                  className={`p-2.5 rounded-xl border cursor-pointer transition-all flex items-center space-x-3 shadow ${
                    isSelected 
                      ? 'bg-[#161922] border-[#E6B325] ring-1 ring-[#E6B325]/40 shadow-lg' 
                      : 'bg-[#161922]/70 border-[#1E2430] hover:border-slate-600 hover:bg-[#161922]'
                  }`}
                >
                  {/* Camera Thumbnail Preview */}
                  <div className="w-16 h-12 rounded-lg bg-black overflow-hidden flex-shrink-0 relative border border-[#1E2430]">
                    <img 
                      src={`/assets/tile_cctv_bg.jpg`} 
                      alt={cam.display_name} 
                      className="w-full h-full object-cover opacity-80"
                    />
                    <div className="absolute top-1 left-1 w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  </div>

                  {/* Camera Meta */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="font-extrabold text-xs text-white truncate" title={cam.display_name}>
                        {cam.display_name}
                      </h4>
                      {isLive && (
                        <span className="text-[8px] font-black text-emerald-400 bg-emerald-950 px-1.5 py-0.2 rounded border border-emerald-600/40 uppercase">
                          LIVE
                        </span>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-400 font-mono mt-0.5 truncate">{cam.camera_code}</p>
                    <div className="flex items-center text-[9px] text-slate-400 mt-1 space-x-1">
                      <MapPin size={10} className="text-blue-400 flex-shrink-0" />
                      <span className="truncate">{cam.city}</span>
                    </div>
                  </div>
                </div>
              );
            })}

            {filteredCameras.length === 0 && (
              <div className="py-8 text-center text-slate-500 text-xs font-semibold">
                No camera sources matching search filter.
              </div>
            )}
          </div>

        </div>

        {/* ── COLUMN 2: SELECTED CAMERA WORKSPACE (6 Cols) ──────────────────── */}
        <div className="lg:col-span-6 space-y-3.5 flex flex-col">
          
          {/* Selected Camera Stream Viewport */}
          <div className="bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 shadow-lg flex flex-col">
            
            {/* Top Stream Status Bar */}
            <div className="flex items-center justify-between border-b border-[#1E2430] pb-2 mb-2.5 text-xs">
              <div className="flex items-center space-x-2 truncate">
                <span className="flex items-center text-emerald-400 font-bold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-600/40 text-[10px]">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-1.5" />
                  LIVE FEED
                </span>
                <span className="font-mono text-slate-300 font-bold">{camera ? camera.camera_code : 'CAM-DEL-01'}</span>
                <span className="text-slate-500">|</span>
                <span className="font-extrabold text-white truncate">{camera ? camera.display_name : 'Connaught Place Inner Circle Junction'}</span>
              </div>

              <div className="hidden sm:flex items-center text-[10px] text-slate-400 font-mono space-x-2 flex-shrink-0">
                <MapPin size={11} className="text-blue-400" />
                <span>{camera ? `${camera.city}` : 'Delhi, Central Delhi'}</span>
                <span>Fri 04 Sep 2026 19:52:17 IST</span>
              </div>
            </div>

            {/* Large Feed Viewer Box */}
            <div className="relative w-full aspect-video rounded-lg overflow-hidden border border-[#1E2430] bg-black shadow-inner">
              <FeedViewer cameraData={cameraDetail} />
            </div>

          </div>

          {/* Bottom Grid: Recent Clips & Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-3.5">
            
            {/* Recent Clips (8 cols) */}
            <div className="md:col-span-8 bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 shadow">
              <div className="flex items-center justify-between mb-2.5 border-b border-[#1E2430] pb-1.5">
                <div className="flex items-center space-x-2">
                  <Activity size={14} className="text-blue-400" />
                  <h3 className="text-xs font-black text-white uppercase tracking-wider">RECENT CLIPS</h3>
                </div>
                <button className="text-[10px] font-bold text-blue-400 hover:text-blue-300 flex items-center">
                  View All Clips <ChevronRight size={12} />
                </button>
              </div>

              <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                {[
                  { time: '19:48:12', tag: 'Vehicle Movement', status: 'blue' },
                  { time: '19:45:03', tag: 'High Footfall', status: 'emerald' },
                  { time: '19:41:27', tag: 'Suspected Vehicle', status: 'red' },
                  { time: '19:38:11', tag: 'Group Detected', status: 'amber' },
                  { time: '19:32:46', tag: 'Unusual Activity', status: 'red' }
                ].map((clip, i) => (
                  <div key={i} className="bg-[#161922] border border-[#1E2430] rounded-lg p-1.5 flex flex-col justify-between hover:border-slate-500 cursor-pointer transition-colors shadow">
                    <div className="w-full h-12 bg-black rounded overflow-hidden relative border border-[#1E2430] mb-1.5">
                      <img src="/assets/tile_cctv_bg.jpg" alt="Clip" className="w-full h-full object-cover opacity-70" />
                      <span className="absolute bottom-1 left-1 font-mono text-[8px] font-bold text-white bg-black/80 px-1 rounded">
                        {clip.time}
                      </span>
                    </div>
                    <p className="text-[9px] font-extrabold text-slate-300 truncate">{clip.tag}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions (4 cols) */}
            <div className="md:col-span-4 bg-[#11141C] border border-[#1E2430] rounded-xl p-3.5 shadow">
              <h3 className="text-xs font-black text-white uppercase tracking-wider mb-2.5 border-b border-[#1E2430] pb-1.5 flex items-center">
                <span className="text-[#E6B325] mr-1.5">⚡</span>
                QUICK ACTIONS
              </h3>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <button className="flex flex-col items-center justify-center p-2.5 bg-[#161922] border border-[#1E2430] hover:border-slate-500 rounded-lg text-slate-200 hover:text-white transition-colors cursor-pointer text-center">
                  <CaptureIcon size={16} className="text-blue-400 mb-1" />
                  <span className="text-[10px] font-extrabold">Capture Frame</span>
                </button>
                <button className="flex flex-col items-center justify-center p-2.5 bg-[#161922] border border-[#1E2430] hover:border-slate-500 rounded-lg text-slate-200 hover:text-white transition-colors cursor-pointer text-center">
                  <Flag size={16} className="text-[#E6B325] mb-1" />
                  <span className="text-[10px] font-extrabold">Mark Event</span>
                </button>
                <button className="flex flex-col items-center justify-center p-2.5 bg-[#161922] border border-[#1E2430] hover:border-slate-500 rounded-lg text-slate-200 hover:text-white transition-colors cursor-pointer text-center">
                  <SearchIcon size={16} className="text-emerald-400 mb-1" />
                  <span className="text-[10px] font-extrabold">Search Feed</span>
                </button>
                <button className="flex flex-col items-center justify-center p-2.5 bg-[#161922] border border-[#1E2430] hover:border-slate-500 rounded-lg text-slate-200 hover:text-white transition-colors cursor-pointer text-center">
                  <MapIcon size={16} className="text-cyan-400 mb-1" />
                  <span className="text-[10px] font-extrabold">View on Map</span>
                </button>
              </div>
            </div>

          </div>

        </div>

        {/* ── COLUMN 3: CAMERA DETAILS & RUN VISUAL ANALYSIS (3 Cols) ───────── */}
        <div className="lg:col-span-3 bg-[#11141C] border border-[#1E2430] rounded-xl p-4 flex flex-col justify-between shadow-lg space-y-4">
          
          {/* Metadata Top Header */}
          <div>
            <div className="flex items-center justify-between border-b border-[#1E2430] pb-2.5 mb-3">
              <div className="flex items-center space-x-2">
                <CameraIcon className="w-4 h-4 text-blue-400" />
                <h2 className="text-xs font-black text-white uppercase tracking-wider">CAMERA DETAILS</h2>
              </div>
              <span className="text-[9px] font-black text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-600/40 uppercase">
                LIVE
              </span>
            </div>

            {/* Title & Location */}
            <div className="mb-4">
              <h3 className="text-sm font-extrabold text-white leading-tight">
                {camera ? camera.display_name : 'Connaught Place Inner Circle Junction'}
              </h3>
              <div className="flex items-center text-xs text-slate-400 mt-1 space-x-1">
                <MapPin size={12} className="text-blue-400 flex-shrink-0" />
                <span>{camera ? `${camera.city}` : 'Delhi, Central Delhi'}</span>
              </div>
            </div>

            {/* Key-Value Details Table */}
            <div className="space-y-2.5 text-xs border-t border-[#1E2430] pt-3">
              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Camera ID</span>
                <span className="font-mono font-bold text-white bg-[#161922] px-2 py-0.5 rounded border border-[#1E2430]">
                  {camera ? camera.camera_code : 'CAM-DEL-01'}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Coordinates</span>
                <span className="font-mono text-slate-200">
                  {camera ? `${camera.latitude.toFixed(4)}, ${camera.longitude.toFixed(4)}` : '28.6315, 77.2167'}
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Area</span>
                <span className="text-slate-200 font-bold">{camera ? camera.display_name.split(' ')[0] : 'Connaught Place'}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Operator</span>
                <span className="text-slate-200">TfL Open Data</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Feed Status</span>
                <span className="text-emerald-400 font-extrabold flex items-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5" />
                  Live · Reachable
                </span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Last Sync</span>
                <span className="text-slate-300">3 Sep 2026, 14:32</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Source</span>
                <span className="text-slate-300">Delhi Police / TfL</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-slate-400 font-semibold">Type</span>
                <span className="text-slate-300">Traffic / Surveillance</span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-[#1E2430]">
              <button className="text-xs text-blue-400 hover:text-blue-300 flex items-center font-bold">
                <ExternalLink size={12} className="mr-1.5" />
                Open Data & Licensing
                <ChevronRight size={13} className="ml-auto" />
              </button>
            </div>
          </div>

          {/* ── PRIMARY ACTION BUTTON: RUN VISUAL ANALYSIS ──────────────────── */}
          <div className="pt-3 border-t border-[#1E2430]">
            <button
              onClick={handleRunAnalysis}
              className="w-full bg-red-600 hover:bg-red-700 active:bg-red-800 text-white p-3.5 rounded-xl transition-all shadow-xl hover:shadow-red-600/30 flex flex-col items-center justify-center cursor-pointer group border border-red-500/50"
            >
              <div className="flex items-center space-x-2 mb-1">
                <Play className="w-5 h-5 fill-current text-white group-hover:scale-110 transition-transform" />
                <span className="text-base font-black uppercase tracking-wider">Run Visual Analysis</span>
              </div>
              <span className="text-[10px] text-red-100 font-bold font-mono uppercase tracking-widest opacity-90">
                YOLOv8 – Detect People, Vehicles & More
              </span>
            </button>
          </div>

        </div>

      </div>

    </div>
  );
};
