import React from 'react';

interface GraphWorkspaceShellProps {
  header: React.ReactNode;
  leftExplorer?: React.ReactNode;
  centerCanvas: React.ReactNode;
  rightDossier?: React.ReactNode;
  bottomBar?: React.ReactNode;
}

export const GraphWorkspaceShell: React.FC<GraphWorkspaceShellProps> = ({
  header,
  leftExplorer,
  centerCanvas,
  rightDossier,
  bottomBar,
}) => {
  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#0b0f19] text-slate-200 antialiased font-sans">
      {/* ── Top Header ── */}
      {header}

      {/* ── Main Workspace Body (~15% Left, ~70% Center, ~15% Right) ── */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Explorer (optional / collapsible) */}
        {leftExplorer && (
          <aside className="w-72 shrink-0 border-r border-[#1e2d4a] bg-[#0d1322] flex flex-col z-10">
            {leftExplorer}
          </aside>
        )}

        {/* Center Main Canvas Area (Dominant Workspace Area ~70%) */}
        <main className="flex-1 flex flex-col relative overflow-hidden bg-graph-grid">
          {centerCanvas}
        </main>

        {/* Right Entity Dossier Panel (optional / collapsible) */}
        {rightDossier && (
          <aside className="w-80 shrink-0 border-l border-[#1e2d4a] bg-[#0d1322] flex flex-col z-10">
            {rightDossier}
          </aside>
        )}
      </div>

      {/* ── Bottom Panel (Graph Insights, Timeline, Trail) ── */}
      {bottomBar && (
        <footer className="border-t border-[#1e2d4a] bg-[#0b0f19] shrink-0 z-20">
          {bottomBar}
        </footer>
      )}
    </div>
  );
};
