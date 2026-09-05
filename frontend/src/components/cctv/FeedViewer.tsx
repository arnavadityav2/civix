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
      <div className="w-full h-full min-h-[260px] bg-[#161922] border border-[#1E2430] rounded-lg flex flex-col items-center justify-center text-slate-400">
        <Video size={40} className="mb-2 text-blue-400 opacity-60" />
        <p className="text-xs font-semibold text-slate-300">Select a camera pin on the map to inspect live feed stream.</p>
      </div>
    );
  }

  const { camera, feeds } = cameraData;
  const isAvailable = camera.status === 'LIVE' || camera.status === 'REGISTERED_ONLY';
  const feedUrl = feeds && feeds.length > 0 ? feeds[0].feed_url : null;
  const isVideo = feedUrl?.toLowerCase().includes('.mp4') || feedUrl?.toLowerCase().includes('.webm');

  if (!isAvailable || !feedUrl) {
    return (
      <div className="w-full h-full min-h-[260px] bg-[#161922] border border-[#1E2430] rounded-lg flex flex-col items-center justify-center text-slate-400 relative overflow-hidden">
        <div className="absolute top-3 right-3 bg-red-950/80 text-red-400 text-[10px] font-extrabold px-2.5 py-0.5 rounded border border-red-600/40 uppercase">
          Feed Unavailable
        </div>
        <AlertCircle size={36} className="mb-2 text-amber-500" />
        <p className="text-xs font-bold text-white">Current feed stream unavailable.</p>
      </div>
    );
  }

  return (
    <div className="relative w-full flex-1 min-h-[260px] rounded-lg overflow-hidden border border-[#1E2430] bg-black flex items-center justify-center shadow-inner group">
      {isVideo ? (
        loadError ? (
          <div className="flex flex-col items-center justify-center p-4 text-center text-slate-400 z-0">
            <AlertCircle size={32} className="mb-2 text-amber-500" />
            <p className="text-xs font-bold text-white">Unable to load feed stream directly</p>
            <p className="text-[10px] text-slate-400 mt-1 max-w-xs truncate">{feedUrl}</p>
            <a 
              href={feedUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="mt-3 text-xs font-bold text-white bg-[#161922] border border-[#1E2430] hover:border-slate-500 px-3 py-1.5 rounded-lg transition-colors"
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
      
      {/* Live Stream HUD Overlay Badges */}
      <div className="absolute top-3 left-3 flex items-center space-x-2 z-10 pointer-events-none">
        <div className="bg-black/75 backdrop-blur-md text-white text-[10px] font-bold px-2.5 py-0.5 rounded border border-white/15 uppercase tracking-wider flex items-center shadow">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse mr-1.5"></span>
          {isVideo ? 'LIVE STREAM' : 'LIVE FRAME'}
        </div>
      </div>
      
      <div className="absolute bottom-3 right-3 z-10 pointer-events-none">
        <div className="bg-black/75 backdrop-blur-md text-slate-300 text-[10px] px-2.5 py-0.5 rounded border border-white/15 font-mono shadow">
          TfL Open Data Stream
        </div>
      </div>
    </div>
  );
};
