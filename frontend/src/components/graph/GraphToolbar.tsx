import React from 'react';
import { 
  Compass, 
  GitFork, 
  Route, 
  Focus, 
  Link2, 
  RefreshCw, 
  RotateCcw, 
  Maximize2, 
  Minimize2,
  Database,
  FileText,
  EyeOff
} from 'lucide-react';
import type { WorkspaceMode } from '../../types/graph';

interface GraphToolbarProps {
  mode: WorkspaceMode;
  onModeChange: (mode: WorkspaceMode) => void;
  hopDepth: number;
  onHopDepthChange: (depth: number) => void;
  focusNodeName?: string | null;
  focusHopDepth?: number;
  onFocusHopDepthChange?: (depth: number) => void;
  onExitFocus?: () => void;
  onReLayout: () => void;
  onReset: () => void;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
  isNeo4jLive?: boolean;
  isEvidenceVisible?: boolean;
  evidenceCount?: number;
  onToggleEvidence?: () => void;
}

export const GraphToolbar: React.FC<GraphToolbarProps> = ({
  mode,
  onModeChange,
  hopDepth,
  onHopDepthChange,
  focusNodeName,
  focusHopDepth = 1,
  onFocusHopDepthChange,
  onExitFocus,
  onReLayout,
  onReset,
  isFullscreen,
  onToggleFullscreen,
  isNeo4jLive = true,
  isEvidenceVisible = false,
  evidenceCount = 0,
  onToggleEvidence,
}) => {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-[#0d1322] border-b border-[#1e2d4a] shrink-0 z-20 text-slate-200">
      
      {/* ── SIGNATURE CIVIX FOCUS MODE ACTIVE HUD BANNER ── */}
      {mode === 'FOCUS' ? (
        <div className="flex items-center gap-3 bg-cyan-950/90 border border-cyan-500/80 px-3 py-1 rounded-lg shadow-lg">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-xs font-mono font-black text-cyan-300 uppercase tracking-wider">
              FOCUS MODE ACTIVE:
            </span>
            <span className="text-xs font-black text-white bg-black/60 px-2.5 py-0.5 rounded border border-cyan-500/40">
              {focusNodeName || 'SELECTED ENTITY'}
            </span>
          </div>

          <div className="h-4 w-px bg-cyan-500/40" />

          {/* 1 HOP / 2 HOPS / 3 HOPS Complexity Controls */}
          <div className="flex items-center gap-1 font-mono text-xs">
            <span className="text-[10px] text-slate-300 font-bold uppercase mr-1">NEIGHBORHOOD:</span>
            {[1, 2, 3].map((h) => {
              const isActive = focusHopDepth === h;
              return (
                <button
                  key={h}
                  onClick={() => onFocusHopDepthChange && onFocusHopDepthChange(h)}
                  className={`px-3 py-1 rounded text-xs font-mono font-black transition-all cursor-pointer ${
                    isActive
                      ? 'bg-cyan-500 text-black shadow-md ring-2 ring-cyan-400/60 scale-105'
                      : 'bg-black/60 hover:bg-cyan-900/60 text-cyan-300 border border-cyan-500/40'
                  }`}
                >
                  {h} {h === 1 ? 'HOP' : 'HOPS'}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => (onExitFocus ? onExitFocus() : onModeChange('EXPLORE'))}
            className="ml-2 px-3 py-1 text-xs font-bold text-slate-200 hover:text-white bg-black/60 hover:bg-red-950/80 border border-slate-700 hover:border-red-500/60 rounded transition-colors flex items-center gap-1 cursor-pointer"
            title="Exit Focus Mode back to full network"
          >
            <EyeOff className="w-3.5 h-3.5 text-red-400" />
            <span>Exit Focus</span>
          </button>
        </div>
      ) : (
        /* Left: Primary Workspace Modes */
        <div className="flex items-center gap-1.5 bg-[#0b0f19] border border-[#1e2d4a] p-1 rounded">
          <button
            onClick={() => onModeChange('EXPLORE')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold transition-colors ${
              mode === 'EXPLORE'
                ? 'bg-cyan-950/80 border border-cyan-500/60 text-cyan-400 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-[#131b2e]'
            }`}
            title="Default exploration mode"
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Explore</span>
          </button>

          <button
            onClick={() => onModeChange('SEE_THREAD')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold transition-colors ${
              mode === 'SEE_THREAD'
                ? 'bg-cyan-950/80 border border-cyan-500/60 text-cyan-400 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-[#131b2e]'
            }`}
            title="Isolate focused investigative network thread"
          >
            <GitFork className="w-3.5 h-3.5" />
            <span>See Thread</span>
          </button>

          <button
            onClick={() => onModeChange('FIND_PATH')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold transition-colors ${
              mode === 'FIND_PATH'
                ? 'bg-cyan-950/80 border border-cyan-500/60 text-cyan-400 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-[#131b2e]'
            }`}
            title="Find shortest multi-hop path between entities"
          >
            <Route className="w-3.5 h-3.5" />
            <span>Find Path</span>
          </button>

          <button
            onClick={() => onModeChange('FOCUS')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold transition-colors ${
              mode === 'FOCUS'
                ? 'bg-cyan-950/80 border border-cyan-500/60 text-cyan-400 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-[#131b2e]'
            }`}
            title="Signature Focus Mode: Disappear everything except selected entity network"
          >
            <Focus className="w-3.5 h-3.5" />
            <span>Focus Mode</span>
          </button>

          <button
            onClick={() => onModeChange('CONNECT_ENTITY')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold transition-colors ${
              mode === 'CONNECT_ENTITY'
                ? 'bg-amber-950/80 border border-amber-500/60 text-amber-400 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-[#131b2e]'
            }`}
            title="Propose a new relationship between two entities"
          >
            <Link2 className="w-3.5 h-3.5" />
            <span>Connect Entity</span>
          </button>

          {/* Top-Left Dynamic Evidence Toggle Button */}
          {onToggleEvidence && (
            <button
              onClick={onToggleEvidence}
              className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-semibold font-mono transition-all border ml-1 ${
                isEvidenceVisible
                  ? 'bg-cyan-950/90 border-cyan-500 text-cyan-300 shadow-sm'
                  : 'bg-[#131b2e] border-slate-700 hover:border-cyan-500/60 text-slate-300 hover:text-white'
              }`}
              title={isEvidenceVisible ? 'Hide evidence nodes without changing layout' : 'Show evidence nodes without changing layout'}
            >
              {isEvidenceVisible ? (
                <EyeOff className="w-3.5 h-3.5 text-cyan-400" />
              ) : (
                <FileText className="w-3.5 h-3.5 text-cyan-400" />
              )}
              <span>{isEvidenceVisible ? `Hide Evidence (${evidenceCount})` : `Show Evidence (${evidenceCount})`}</span>
            </button>
          )}
        </div>
      )}

      {/* Center: Hop Depth Selector */}
      <div className="flex items-center gap-3 border-l border-r border-[#1e2d4a] px-3 py-0.5">
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Hop Depth:</span>
          <div className="flex items-center gap-1 bg-[#0b0f19] border border-[#1e2d4a] p-0.5 rounded">
            {[1, 2, 3, 4, 5].map((depth) => (
              <button
                key={depth}
                onClick={() => onHopDepthChange(depth)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold transition-colors ${
                  hopDepth === depth
                    ? 'bg-cyan-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#131b2e]'
                }`}
              >
                {depth}H
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Layout Controls & Projection Status Indicator */}
      <div className="flex items-center gap-3">
        {/* Projection Status Indicator */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0b0f19] border border-[#1e2d4a] text-xs font-mono">
          <Database className={`w-3.5 h-3.5 ${isNeo4jLive ? 'text-emerald-400' : 'text-amber-400'}`} />
          <span className="text-[11px] text-slate-300">
            {isNeo4jLive ? (
              <>Graph Status: <span className="text-emerald-400 font-bold">Live (from Neo4j)</span></>
            ) : (
              <>Graph Status: <span className="text-amber-400 font-bold">PostgreSQL Fallback</span></>
            )}
          </span>
        </div>

        {/* Explicit User-Controlled RE-LAYOUT Button */}
        <button
          onClick={onReLayout}
          className="flex items-center gap-1.5 bg-[#131b2e] border border-[#1e2d4a] hover:border-cyan-500/50 text-slate-300 hover:text-white text-xs px-2.5 py-1 rounded font-semibold transition-colors"
          title="Explicitly recalculate graph node layout (preserves mental map otherwise)"
        >
          <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
          <span>RE-LAYOUT</span>
        </button>

        {/* Reset Camera View Button */}
        <button
          onClick={onReset}
          className="p-1.5 bg-[#131b2e] border border-[#1e2d4a] hover:border-slate-500 text-slate-400 hover:text-white rounded transition-colors"
          title="Reset canvas camera zoom & pan"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        {/* Toggle Fullscreen Button */}
        <button
          onClick={onToggleFullscreen}
          className="p-1.5 bg-[#131b2e] border border-[#1e2d4a] hover:border-slate-500 text-slate-400 hover:text-white rounded transition-colors"
          title="Toggle Fullscreen"
        >
          {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>
  );
};
