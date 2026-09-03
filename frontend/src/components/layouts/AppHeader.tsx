import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { EmblemLogo } from '../ui/EmblemLogo';
import { Search, Bell, HelpCircle, ChevronDown } from 'lucide-react';

interface AppHeaderProps {
  onSearchClick?: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({ onSearchClick }) => {
  const navigate = useNavigate();

  function handleSearchClick() {
    navigate('/search');
    if (onSearchClick) onSearchClick();
  }

  // Ctrl+K shortcut routes to the canonical SearchPage
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        navigate('/search');
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate]);

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      {/* Top Banner Row */}
      <div className="px-6 py-2.5 flex items-center justify-between">
        {/* Left: Branding & Government Identity */}
        <div className="flex items-center space-x-3">
          <EmblemLogo className="w-9 h-9 flex-shrink-0" />
          <div className="flex flex-col">
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-slate-900 text-lg tracking-tight font-sans">
                CIVIX 2.0
              </span>
              <span className="text-xs text-slate-500 font-medium pl-2 border-l border-slate-300">
                Investigative Intelligence Workstation
              </span>
            </div>
            <div className="flex items-center space-x-2 text-[11px] text-slate-600 font-medium">
              <span className="font-semibold text-slate-800">Government of India</span>
              <span className="text-slate-400">•</span>
              <span>Ministry of Home Affairs</span>
              <span className="text-slate-400">•</span>
              <span className="text-amber-800 font-semibold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-300">
                PROTOTYPE
              </span>
            </div>
          </div>
        </div>

        {/* Center: Global Search Bar — single canonical entry point → /search */}
        <div className="flex-1 max-w-md mx-8">
          <button
            id="header-search-btn"
            type="button"
            onClick={handleSearchClick}
            aria-label="Open global search (Ctrl+K)"
            className="relative flex items-center w-full bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-500 hover:border-slate-400 hover:bg-white cursor-pointer transition-colors shadow-2xs group"
          >
            <Search className="w-4 h-4 text-slate-400 mr-2 flex-shrink-0 group-hover:text-slate-600 transition-colors" />
            <span className="flex-1 truncate text-left">Search cases, entities, evidence...</span>
            <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-[10px] font-mono text-slate-500 bg-white border border-slate-300 rounded shadow-2xs">
              Ctrl + K
            </kbd>
          </button>
        </div>

        {/* Right: Investigator Context & Profile Quick Actions */}
        <div className="flex items-center space-x-4">
          {/* Workspace Context Selector */}
          <div className="hidden lg:flex flex-col items-end">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
              Investigator Context
            </span>
            <button className="flex items-center space-x-1 text-xs font-bold text-slate-900 hover:text-amber-800 transition-colors">
              <span>DELHI NCR INVESTIGATION WORKSPACE</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
            </button>
          </div>

          <div className="h-6 w-px bg-slate-200 hidden sm:block" />

          {/* Action Icons */}
          <div className="flex items-center space-x-2">
            <button className="relative p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded transition-colors" title="Notifications">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1 right-1 w-4 h-4 bg-red-600 text-white font-mono text-[9px] font-bold rounded-full flex items-center justify-center border border-white">
                12
              </span>
            </button>

            <button className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded transition-colors" title="Help & Documentation">
              <HelpCircle className="w-4 h-4" />
            </button>

            {/* Avatar Pill */}
            <div className="flex items-center space-x-2 pl-2">
              <div className="w-8 h-8 rounded bg-slate-900 text-white font-mono font-bold text-xs flex items-center justify-center border border-slate-800 shadow-2xs">
                VS
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Institutional Restrained Saffron Brand Strip */}
      <div className="h-1 bg-gradient-to-r from-amber-600 via-amber-500 to-slate-900 w-full" />
    </header>
  );
};
