import React, { useRef, useState, useEffect } from 'react';

interface CivixSplashScreenProps {
  onComplete: () => void;
}

const CLIP_DURATION = 3; // Only play the last N seconds of the video

export const CivixSplashScreen: React.FC<CivixSplashScreenProps> = ({ onComplete }) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [fading, setFading] = useState(false);
  const [opacity, setOpacity] = useState(1);

  // Smooth 1-second fade-out then call onComplete
  const triggerExit = () => {
    if (fading) return;
    setFading(true);
    let start: number | null = null;
    const step = (timestamp: number) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / 1000, 1);
      setOpacity(1 - progress);
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        onComplete();
      }
    };
    requestAnimationFrame(step);
  };

  // Once metadata is loaded, seek to (duration - CLIP_DURATION) then play
  const handleLoadedMetadata = () => {
    const v = videoRef.current;
    if (!v) return;
    const startAt = Math.max(0, v.duration - CLIP_DURATION);
    v.currentTime = startAt;

    // Attempt with audio; fall back to muted
    v.muted = false;
    v.play().catch(() => {
      v.muted = true;
      v.play().catch(() => triggerExit());
    });
  };

  const handleVideoEnd = () => triggerExit();
  const handleError = () => triggerExit();

  // Safety: if metadata never fires (e.g. slow network or video error), auto-exit after 1.5s
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    v.load();

    const fallbackTimer = setTimeout(() => {
      triggerExit();
    }, 1500);

    return () => clearTimeout(fallbackTimer);
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 bg-black"
      style={{ opacity, pointerEvents: fading ? 'none' : 'auto' }}
    >
      <video
        ref={videoRef}
        src="/civix_intro.mp4"
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleVideoEnd}
        onError={handleError}
        playsInline
        preload="metadata"
        className="absolute inset-0 w-full h-full object-cover"
      />

      {!fading && (
        <button
          onClick={triggerExit}
          className="absolute top-5 right-6 z-10 text-xs font-mono text-white/40 hover:text-white/80 transition-colors px-3 py-1.5 rounded bg-black/20 hover:bg-black/40 border border-white/10 hover:border-white/30 backdrop-blur-sm"
        >
          SKIP ›
        </button>
      )}
    </div>
  );
};
