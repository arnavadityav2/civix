import React, { useRef, useEffect, useState } from 'react';
import type { CameraDetail } from '../../api/cctv';
import { AlertCircle, Video } from 'lucide-react';

interface FeedViewerProps {
  cameraData: CameraDetail | null;
}

export const FeedViewer: React.FC<FeedViewerProps> = ({ cameraData }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    setLoadError(false);
    if (videoRef.current) {
      videoRef.current.load();
      videoRef.current.play().catch(() => {
        // Autoplay policy fallback
      });
    }
  }, [cameraData]);

  if (!cameraData) {
    return (
      <div className="w-full h-full min-h-[260px] bg-slate-100 border border-slate-200 rounded flex flex-col items-center justify-center text-slate-500">
        <Video size={44} className="mb-2 text-slate-300" />
        <p className="text-xs font-medium text-slate-400">Select a camera pin to inspect feed stream.</p>
      </div>
    );
  }

  const { camera, feeds } = cameraData;
  const isAvailable = camera.status === 'LIVE' || camera.status === 'REGISTERED_ONLY';
  const feedUrl = feeds && feeds.length > 0 ? feeds[0].feed_url : null;
  const isVideo = feedUrl?.toLowerCase().includes('.mp4') || feedUrl?.toLowerCase().includes('.webm');

  if (!isAvailable || !feedUrl) {
    return (
      <div className="w-full h-full min-h-[260px] bg-slate-100 border border-slate-200 rounded flex flex-col items-center justify-center text-slate-500 relative overflow-hidden">
        <div className="absolute top-2 right-2 bg-amber-100 text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded border border-amber-200 uppercase">
          Feed Unavailable
        </div>
        <AlertCircle size={36} className="mb-2 text-amber-400" />
        <p className="text-xs font-medium">Current feed stream unavailable.</p>
      </div>
    );
  }

  return (
    <div className="relative w-full flex-1 min-h-[260px] rounded overflow-hidden border border-slate-800 bg-slate-950 flex items-center justify-center shadow-inner group">
      {isVideo ? (
        loadError ? (
          <div className="flex flex-col items-center justify-center p-4 text-center text-slate-400 z-0">
            <AlertCircle size={32} className="mb-2 text-amber-400" />
            <p className="text-xs font-medium text-slate-300">Unable to load feed stream directly</p>
            <p className="text-[10px] text-slate-500 mt-1 max-w-xs truncate">{feedUrl}</p>
            <a 
              href={feedUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="mt-3 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-medium rounded border border-slate-700 transition-colors z-20"
            >
              Open Direct Media Stream
            </a>
          </div>
        ) : (
          <video 
            key={feedUrl}
            ref={videoRef}
            src={feedUrl} 
            controls 
            autoPlay 
            muted 
            loop 
            playsInline
            preload="auto"
            className="w-full h-full object-contain z-0"
            onError={() => setLoadError(true)}
          />
        )
      ) : (
        <img 
          key={feedUrl}
          src={feedUrl} 
          alt={`${camera.display_name} feed`} 
          className="w-full h-full object-contain z-0"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiMwZjE3MmEiLz48dGV4dCB4PSI5NGEzYjgiIGR5PSIuM2VtIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5GZWVkIEltYWdlIFVuYXZhaWxhYmxlPC90ZXh0Pjwvc3ZnPg==';
          }}
        />
      )}
      
      <div className="absolute top-2.5 left-2.5 flex items-center space-x-2 z-10 pointer-events-none">
        <div className="bg-black/70 backdrop-blur-sm text-white text-[10px] font-bold px-2 py-0.5 rounded border border-white/20 uppercase tracking-wider flex items-center">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-1.5"></span>
          {isVideo ? 'CURRENT FEED' : 'CURRENT FRAME'}
        </div>
      </div>
      
      <div className="absolute bottom-2.5 right-2.5 z-10 pointer-events-none">
        <div className="bg-black/75 backdrop-blur-sm text-slate-300 text-[10px] px-2 py-0.5 rounded border border-white/10 font-mono">
          Transport for London
        </div>
      </div>
    </div>
  );
};
