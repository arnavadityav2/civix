import React, { useState, useEffect } from 'react';
import { cctvApi } from '../api/cctv';
import type { Camera, CameraDetail, CVTrack, CCTVPlateDetection } from '../api/cctv';
import { casesApi } from '../api/cases';
import type { CaseListItem } from '../types/api';
import { CameraMap } from '../components/cctv/CameraMap';
import { CameraGrid } from '../components/cctv/CameraGrid';
import { CameraInspector } from '../components/cctv/CameraInspector';
import { FeedViewer } from '../components/cctv/FeedViewer';
import { RefreshCw, Play, AlertTriangle, Layers, CreditCard } from 'lucide-react';

export const CCTVCommandCenterPage: React.FC = () => {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string>('');
  
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null);
  const [cameraDetail, setCameraDetail] = useState<CameraDetail | null>(null);
  
  const [isSyncing, setIsSyncing] = useState(false);

  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>('');
  const [tracks, setTracks] = useState<CVTrack[]>([]);
  const [plates, setPlates] = useState<CCTVPlateDetection[]>([]);
  const [isStartingJob, setIsStartingJob] = useState(false);

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

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (jobId && jobStatus !== 'COMPLETED' && jobStatus !== 'FAILED') {
      interval = setInterval(() => {
        cctvApi.getSearchJob(jobId)
          .then(data => {
            setJobStatus(data.status);
            if (data.status === 'COMPLETED') {
              fetchTracks(jobId);
            }
          })
          .catch(err => console.error(err));
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [jobId, jobStatus]);

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

  const fetchTracks = (id: string) => {
    cctvApi.getJobTracks(id)
      .then(data => setTracks(data))
      .catch(err => console.error(err));

    cctvApi.getJobPlates(id)
      .then(data => setPlates(data))
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

  const startJob = () => {
    if (!selectedCameraId || !selectedCaseId) return;
    setIsStartingJob(true);
    setJobId(null);
    setTracks([]);
    setPlates([]);
    
    cctvApi.startSearchJob({
      case_id: selectedCaseId,
      camera_ids: [selectedCameraId],
      start_time: new Date().toISOString(),
      end_time: new Date().toISOString()
    }).then(data => {
      setJobId(data.job_id);
      setJobStatus(data.status);
    }).catch(err => {
      console.error(err);
      alert(err.response?.data?.detail || 'Failed to start job.');
    }).finally(() => {
      setIsStartingJob(false);
    });
  };

  const liveCount = cameras.filter(c => c.status === 'LIVE' || c.status === 'REGISTERED_ONLY').length;

  return (
    <div className="min-h-screen bg-[#f9f9ff] text-slate-900 font-sans p-4 sm:p-5 space-y-4">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-white border border-slate-200 rounded px-4 py-3 shadow-sm">
        <div>
          <h1 className="text-lg font-bold text-[#1a3a6c] tracking-tight">CCTV Command Center</h1>
          <p className="text-slate-500 text-[11px]">Public Camera Network & Vehicle Intelligence</p>
        </div>
        
        <div className="mt-2 sm:mt-0 flex items-center space-x-3 w-full sm:w-auto justify-between sm:justify-end">
          <div className="flex items-center space-x-2">
            <span className="text-[10px] uppercase font-bold text-slate-400">Case Context:</span>
            <select 
              className="border border-slate-300 rounded text-xs py-1 px-2.5 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#1a3a6c] shadow-sm max-w-xs"
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
            >
              <option value="">-- Select Active Case --</option>
              {cases.map(c => (
                <option key={c.case_id} value={c.case_id}>{c.case_number} - {c.title}</option>
              ))}
            </select>
          </div>

          <button 
            onClick={syncRegistry}
            disabled={isSyncing}
            className="flex items-center bg-slate-100 hover:bg-slate-200 border border-slate-300 text-slate-700 px-2.5 py-1 rounded text-xs font-semibold shadow-sm transition-colors"
          >
            <RefreshCw size={12} className={`mr-1 text-slate-500 ${isSyncing ? 'animate-spin' : ''}`} />
            {isSyncing ? 'Syncing...' : 'Sync Registry'}
          </button>
        </div>
      </div>

      {/* Metric Cards Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="civix-panel px-3.5 py-2.5">
          <p className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Registered Cameras</p>
          <p className="text-lg font-bold text-slate-800 mt-0.5">{cameras.length}</p>
        </div>
        <div className="civix-panel px-3.5 py-2.5">
          <p className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Live / Reachable</p>
          <p className="text-lg font-bold text-emerald-700 mt-0.5">{liveCount}</p>
        </div>
        <div className="civix-panel px-3.5 py-2.5">
          <p className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Verified Sources</p>
          <p className="text-lg font-bold text-slate-800 mt-0.5">2</p>
        </div>
        <div className="civix-panel px-3.5 py-2.5">
          <p className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Selected Camera</p>
          <p className="text-xs font-semibold text-slate-800 truncate mt-1">
            {cameraDetail ? cameraDetail.camera.display_name : 'None Selected'}
          </p>
        </div>
      </div>

      {/* Main Split Screen Workspace */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-stretch">
        {/* Left Column: Interactive Map */}
        <div className="xl:col-span-7 civix-panel p-3 flex flex-col h-[500px]">
          <div className="flex items-center justify-between px-1 mb-2">
            <span className="text-xs font-bold uppercase text-slate-500 tracking-wider flex items-center">
              <Layers size={13} className="mr-1.5 text-slate-400" />
              Camera Network Map
            </span>
            <span className="text-[10px] font-mono text-slate-400">OpenStreetMap Free Tile Layer</span>
          </div>
          <div className="flex-1 w-full h-full min-h-0 rounded overflow-hidden">
            <CameraMap 
              cameras={cameras} 
              selectedCameraId={selectedCameraId}
              onCameraSelect={setSelectedCameraId}
            />
          </div>
        </div>

        {/* Right Column: Inspector & Feed Viewer */}
        <div className="xl:col-span-5 flex flex-col space-y-3 h-[500px]">
          {/* Camera Inspector Box */}
          <div className="civix-panel p-3 flex-shrink-0">
            <h2 className="text-xs font-bold uppercase text-slate-500 tracking-wider mb-1.5">Camera Inspector</h2>
            <CameraInspector cameraData={cameraDetail} />
          </div>

          {/* Large Feed Viewer Box */}
          <div className="civix-panel p-3 flex-1 flex flex-col min-h-0">
            <h2 className="text-xs font-bold uppercase text-slate-500 tracking-wider mb-1.5">Feed Stream Viewer</h2>
            
            <FeedViewer cameraData={cameraDetail} />

            {/* Launch Search Control Bar */}
            <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between flex-shrink-0">
              <button
                onClick={startJob}
                disabled={!selectedCameraId || !selectedCaseId || isStartingJob}
                className="flex items-center bg-[#1a3a6c] hover:bg-[#132c54] text-white px-3 py-1.5 rounded text-xs font-semibold shadow transition-colors disabled:bg-slate-300 disabled:text-slate-500 cursor-pointer"
              >
                <Play size={13} className="mr-1.5 fill-current" />
                {isStartingJob ? 'Initiating Search...' : 'Start Vehicle Search'}
              </button>

              {(!selectedCameraId || !selectedCaseId) && (
                <div className="flex items-center text-[10px] text-amber-700 font-medium bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  <AlertTriangle size={11} className="mr-1 text-amber-600" />
                  {!selectedCaseId ? 'Select Case first' : 'Select a camera pin'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Directory Grid & Search Tracking */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4 items-stretch">
        {/* Camera Directory Grid */}
        <div className="xl:col-span-8 min-h-[320px]">
          <CameraGrid 
            cameras={cameras}
            selectedCameraId={selectedCameraId}
            onCameraSelect={setSelectedCameraId}
          />
        </div>

        {/* CV Search Job Track Status Panel */}
        <div className="xl:col-span-4 civix-panel p-3 min-h-[320px] flex flex-col">
          <div className="flex items-center justify-between mb-2 border-b border-slate-100 pb-1.5">
            <h2 className="text-xs font-bold uppercase text-slate-500 tracking-wider">Search Job Output</h2>
            {jobStatus && (
              <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${
                jobStatus === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 
                jobStatus === 'FAILED' ? 'bg-red-50 text-red-700 border-red-200' : 
                'bg-amber-50 text-amber-700 border-amber-200 animate-pulse'
              }`}>
                {jobStatus}
              </span>
            )}
          </div>

          <div className="flex-1 overflow-y-auto bg-slate-50/70 rounded border border-slate-200 p-2.5 space-y-3">
            {jobId ? (
              (tracks.length > 0 || plates.length > 0) ? (
                <div className="space-y-3">
                  {/* Plate OCR Signals */}
                  {plates.length > 0 && (
                    <div>
                      <p className="text-[10px] uppercase font-bold text-slate-500 mb-1.5 flex items-center">
                        <CreditCard size={11} className="mr-1 text-slate-400" />
                        Plate Signals ({plates.length})
                      </p>
                      <div className="space-y-2">
                        {plates.map(plate => (
                          <div key={plate.plate_detection_id} className="bg-white border border-slate-200 rounded p-2.5 shadow-sm space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                                {plate.normalized_plate}
                              </span>
                              <span className="text-[9px] font-bold px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded uppercase border border-blue-200">
                                OCR CANDIDATE
                              </span>
                            </div>
                            <div className="grid grid-cols-2 text-[10px] text-slate-500 pt-1 border-t border-slate-100">
                              <div>
                                <span className="text-slate-400">Raw OCR: </span>
                                <span className="font-mono text-slate-700">{plate.raw_ocr_text}</span>
                              </div>
                              <div className="text-right">
                                <span className="text-slate-400">Confidence: </span>
                                <span className={`font-bold ${
                                  plate.confidence_category === 'HIGH' ? 'text-emerald-700' :
                                  plate.confidence_category === 'MEDIUM' ? 'text-amber-700' : 'text-red-700'
                                }`}>
                                  {plate.confidence_category} ({(plate.ocr_confidence * 100).toFixed(0)}%)
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Vehicle Tracks */}
                  {tracks.length > 0 && (
                    <div>
                      <p className="text-[10px] uppercase font-bold text-slate-500 mb-1.5">
                        Vehicle Tracks ({tracks.length})
                      </p>
                      <div className="space-y-2">
                        {tracks.map(track => (
                          <div key={track.track_id} className="bg-white border border-slate-200 rounded p-2 shadow-sm flex items-center justify-between">
                            <div>
                              <p className="text-xs font-semibold text-slate-800">Vehicle Track Detected</p>
                              <p className="text-[10px] font-mono text-slate-500 mt-0.5">ID: {track.track_id.split('-')[0]}</p>
                              <p className="text-[10px] text-slate-400">{new Date(track.first_seen).toLocaleTimeString()}</p>
                            </div>
                            <span className="text-[9px] font-bold px-2 py-0.5 bg-slate-100 text-slate-600 rounded uppercase">
                              Track Crop
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs text-center p-3">
                  {jobStatus === 'COMPLETED' ? (
                    <span>No vehicle tracks or plate signals identified in selected interval.</span>
                  ) : (
                    <span className="animate-pulse font-medium text-slate-600">Processing frames with YOLOv8 & OCR engine...</span>
                  )}
                </div>
              )
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 text-xs text-center p-3">
                <p className="font-medium text-slate-500 mb-1">No Active Search Job</p>
                <p className="text-[10px] text-slate-400">Select a camera pin and an active case context, then click "Start Vehicle Search".</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
