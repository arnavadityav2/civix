import React from 'react';
import { useLocation } from 'react-router-dom';
import { AppHeader } from './AppHeader';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const location = useLocation();
  const path = location.pathname;

  // Dedicated full-screen interactive workstation tools
  const isWorkspacePage = (
    path.includes('/graph') ||
    path.includes('/cases/') ||
    path.includes('/cctv') ||
    path.includes('/spatial') ||
    path.includes('/telecom') ||
    path.includes('/biometric') ||
    path.includes('/evidence')
  );

  // Pages with fixed non-scrollable canvas bounds (Cytoscape graph canvas, CCTV video grid)
  const isFixedCanvasPage = path.includes('/graph');

  return (
    <div className="h-screen bg-[#07090E] text-white flex flex-col font-sans select-none overflow-hidden">
      {/* 1. Institutional Top Header */}
      <AppHeader />

      {/* 2. Main Layout Body (Middle flex container) */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Main Workspace Area */}
        {isWorkspacePage ? (
          <main className={`flex-1 flex flex-col min-h-0 ${isFixedCanvasPage ? 'overflow-hidden' : 'overflow-y-auto'} bg-[#0b0f19]`}>
            {children}
          </main>
        ) : (
          <main className="flex-1 overflow-y-auto bg-[#07090E]">
            <div className="max-w-[1850px] w-full mx-auto px-5 py-3.5">
              {children}
            </div>
          </main>
        )}
      </div>

      {/* 3. LOWER INSTITUTIONAL IDENTITY FOOTER (hidden on workstation tools) */}
      {!isWorkspacePage && (
        <footer className="relative flex-shrink-0 border-t border-[#1E2430] overflow-hidden bg-[#07090E] z-30">
          {/* Status Bar */}
          <div className="bg-[#05070A] px-5 py-1.5 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-white">CIVIX 2.0</span>
              <span>|</span>
              <span>Confidential – Delhi Police Use Only</span>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-slate-300">All Systems Operational</span>
              </div>
              <span>|</span>
              <span>Version 2.0.0</span>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
};
