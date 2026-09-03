import React from 'react';
import { AppHeader } from './AppHeader';
import { AppSidebar } from './AppSidebar';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Institutional Top Header */}
      <AppHeader />

      {/* Main Layout Body */}
      <div className="flex-1 flex">
        {/* Left Sidebar */}
        <AppSidebar />

        {/* Main Workspace Area */}
        <main className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-[1600px] mx-auto">
            {children}
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 px-6 py-2 text-center text-xs text-slate-500 font-mono">
        CIVIX 2.0 — LAW ENFORCEMENT INTELLIGENCE PLATFORM — STRICT RLS & DOMAIN ISOLATION ENFORCED
      </footer>
    </div>
  );
};
