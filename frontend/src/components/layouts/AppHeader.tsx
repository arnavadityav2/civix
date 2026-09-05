import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Bell, 
  ChevronDown, 
  PhoneCall
} from 'lucide-react';

interface AppHeaderProps {
  onSearchClick?: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({ onSearchClick }) => {
  const navigate = useNavigate();

  function handleSearchClick() {
    navigate('/search');
    if (onSearchClick) onSearchClick();
  }

  // Ctrl+K shortcut routes to canonical SearchPage
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
    <header className="bg-[#090C12] border-b border-[#1E2430] sticky top-0 z-30 shadow-lg select-none">
      {/* Narrow gold institutional top strip */}
      <div className="h-0.5 bg-[#E6B325] w-full" />

      {/* Main Header Row */}
      <div className="px-4 py-2 flex items-center justify-between gap-3">

        {/* LEFT: Official Delhi Police Crest + CIVIX Identity */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          <div className="flex items-center space-x-2.5 cursor-pointer" onClick={() => navigate('/')}>
            <img 
              src="/assets/delhi_police_crest_cropped.png" 
              alt="Delhi Police Crest" 
              className="w-10 h-10 object-contain drop-shadow" 
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/assets/delhi_police_crest.png';
              }}
            />
            <div className="flex flex-col">
              <span className="font-extrabold text-white text-xs tracking-wider uppercase leading-none font-sans">
                DELHI POLICE
              </span>
              <span className="text-[#E6B325] font-bold text-[11px] leading-tight font-sans">
                दिल्ली पुलिस
              </span>
              <span className="text-[#E6B325] text-[8px] font-mono tracking-widest uppercase leading-none mt-0.5 opacity-90">
                SHANTI SEWA NYAYA
              </span>
            </div>
          </div>

          {/* Vertical Divider */}
          <div className="w-px h-8 bg-[#1E2430] mx-1" />

          {/* CIVIX Product Title */}
          <div className="flex flex-col">
            <div className="flex items-center space-x-1.5">
              <span className="font-black text-white text-base tracking-tight font-sans leading-none">
                CIVIX <span className="text-[#E6B325]">2.0</span>
              </span>
            </div>
            <div className="flex items-center space-x-1 text-[9px] text-slate-400 font-mono tracking-wide mt-0.5">
              <span className="hidden xl:inline">Investigative Intelligence Workstation</span>
              <span className="hidden xl:inline text-slate-600">|</span>
              <span>Government of India</span>
            </div>
          </div>
        </div>

        {/* CENTER: Global Search Bar */}
        <div className="flex-1 max-w-xl mx-2">
          <button
            id="header-search-btn"
            type="button"
            onClick={handleSearchClick}
            aria-label="Open global search (Ctrl+K)"
            className="relative flex items-center w-full bg-[#11141C] border border-[#1E2430] rounded-md px-3 py-1.5 text-xs text-slate-400 hover:border-blue-500 hover:bg-[#161922] cursor-pointer transition-colors group"
          >
            <Search className="w-3.5 h-3.5 text-slate-400 mr-2 flex-shrink-0 group-hover:text-blue-400 transition-colors" />
            <span className="flex-1 truncate text-left text-slate-400 text-xs">
              Search cases, people, vehicles, IMEI, locations, evidence...
            </span>
            <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-[#090C12] border border-[#1E2430] rounded">
              Ctrl + K
            </kbd>
          </button>
        </div>

        {/* RIGHT: Notifications + Avatar + EN Dropdown + Emergency 112 */}
        <div className="flex items-center space-x-3 flex-shrink-0">

          {/* Notification Bell */}
          <button
            onClick={() => navigate('/cases')}
            className="relative p-1.5 text-slate-400 hover:text-white hover:bg-[#161922] rounded transition-colors"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-0 right-0 w-3.5 h-3.5 bg-red-600 text-white font-mono text-[8px] font-bold rounded-full flex items-center justify-center border border-[#090C12]">
              12
            </span>
          </button>

          {/* User Profile Pill */}
          <div className="flex items-center space-x-2 bg-[#11141C] border border-[#1E2430] rounded-md px-2.5 py-1 cursor-pointer hover:border-slate-700 transition-colors">
            <div className="w-6 h-6 rounded bg-blue-600 text-white font-mono font-bold text-[10px] flex items-center justify-center">
              VS
            </div>
            <div className="hidden sm:flex flex-col text-left">
              <span className="text-[11px] font-bold text-white leading-tight">Vikram S.</span>
              <span className="text-[9px] text-slate-400 leading-none">Investigator</span>
            </div>
          </div>

          {/* Language Selector Dropdown matching reference */}
          <div className="flex items-center bg-[#11141C] border border-[#1E2430] rounded px-2.5 py-1 text-xs font-mono text-slate-300 cursor-pointer hover:border-slate-600">
            <span>EN</span>
            <ChevronDown className="w-3 h-3 text-slate-400 ml-1" />
          </div>

          {/* Emergency Response Button (112 Red Pill) */}
          <button 
            onClick={() => navigate('/cases')}
            className="flex items-center space-x-2 bg-[#DC2626] hover:bg-red-700 text-white px-3 py-1.5 rounded-md font-sans text-xs font-bold shadow-md transition-colors"
          >
            <PhoneCall className="w-4 h-4 fill-white" />
            <div className="flex flex-col leading-none text-left">
              <span className="text-sm font-extrabold leading-none">112</span>
              <span className="text-[8px] font-medium tracking-tight opacity-90 leading-none mt-0.5">
                Emergency Response
              </span>
            </div>
          </button>

        </div>
      </div>
    </header>
  );
};



