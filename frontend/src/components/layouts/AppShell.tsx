import React from 'react';
import { useLocation } from 'react-router-dom';
import { AppHeader } from './AppHeader';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const location = useLocation();
  const isDashboard = location.pathname === '/';

  return (
    <div className="h-screen bg-[#07090E] text-white flex flex-col font-sans select-none overflow-hidden">
      {/* 1. Institutional Top Header (Fixed at top of screen) */}
      <AppHeader />

      {/* 2. Main Layout Body (Middle flex container) */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Main Workspace Area (Full width) */}
        <main className="flex-1 overflow-y-auto bg-[#07090E]">
          <div className="max-w-[1850px] w-full mx-auto px-5 py-3.5">
            {children}
          </div>
        </main>
      </div>

      {/* 3. LOWER INSTITUTIONAL IDENTITY FOOTER */}
      <footer className="relative flex-shrink-0 border-t border-[#1E2430] overflow-hidden bg-[#07090E] z-30">
        {/* Photographic Police Parade Lineup & Parliament Banner — Rendered ONLY on Main Dashboard Landing Page */}
        {isDashboard && (
          <div className="relative w-full overflow-hidden bg-black flex items-center justify-center border-b border-[#1E2430]">
            <img 
              src="/assets/lower_identity_banner_cropped.png" 
              alt="Delhi Police Parade & Parliament" 
              className="w-full max-h-[75px] sm:max-h-[85px] object-cover sm:object-contain opacity-100"
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/assets/police_officers_parade.jpg';
              }}
            />
          </div>
        )}

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
    </div>
  );
};
