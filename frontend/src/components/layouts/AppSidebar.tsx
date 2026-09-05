import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useCaseSelection } from '../../context/CaseSelectionContext';
import { 
  LayoutDashboard, 
  Briefcase, 
  FileText, 
  GitFork, 
  Search, 
  Eye, 
  Clock, 
  Navigation, 
  MapPin,
  DollarSign, 
  Video, 
  MessageSquare, 
  Database,
  Bell,
  UserCog,
  Settings,
  Radio,
  Fingerprint
} from 'lucide-react';

export const AppSidebar: React.FC = () => {
  const location = useLocation();
  const { selectedCaseId } = useCaseSelection();

  const mainNav = [
    { label: 'Dashboard', icon: LayoutDashboard, path: '/', exact: true },
    { label: 'Cases', icon: Briefcase, path: '/cases', exact: false },
    { label: 'CDR & Tower Dump', icon: Radio, path: '/telecom', exact: false },
    { label: 'Evidence', icon: FileText, path: '/evidence', exact: false },
    { 
      label: 'Investigative Graph', 
      icon: GitFork, 
      path: selectedCaseId ? `/cases/${selectedCaseId}/graph` : '/cases', 
      exact: false,
      isActiveOverride: () => location.pathname.includes('/graph') 
    },
    { label: 'Biometric & Facial', icon: Fingerprint, path: '/cctv', exact: false },
  ];

  const toolsNav = [
    { label: 'Global Search', icon: Search, path: '/search' },
    { label: 'Spatial Intelligence', icon: MapPin, path: '/spatial' },
    { label: 'CCTV Analysis', icon: Video, path: '/cctv' },
    { label: 'Surveillance', icon: Eye, path: '/spatial' },
    { label: 'Timeline', icon: Clock, path: '/spatial' },
    { label: 'Movement Analysis', icon: Navigation, path: '/spatial' },
    { label: 'Financial Flow', icon: DollarSign, path: '/cases' },
    { label: 'Ask CIVIX', icon: MessageSquare, path: '/search', badge: 'AI', badgeColor: 'bg-[#E6B325] text-black' },
  ];

  const systemNav = [
    { label: 'Data Sources', icon: Database, path: '/cases' },
    { label: 'Notifications', icon: Bell, path: '/cases', badge: '12', badgeColor: 'bg-red-600 text-white' },
    { label: 'User Management', icon: UserCog, path: '/cases' },
    { label: 'Settings', icon: Settings, path: '/cases' },
  ];

  function isActive(path: string, exact: boolean, override?: () => boolean) {
    if (override) return override();
    if (exact) return location.pathname === path;
    return location.pathname.startsWith(path);
  }

  return (
    <aside 
      className="w-56 bg-[#090C12] border-r border-[#1E2430] flex flex-col flex-shrink-0 select-none relative"
      style={{ minHeight: 'calc(100vh - 58px - 88px)' }}
    >
      {/* Navigation */}
      <div className="flex-1 overflow-y-auto py-3 px-3 space-y-4">

        {/* INVESTIGATIONS */}
        <div>
          <h4 className="text-[10px] font-mono font-bold text-slate-400 tracking-wider uppercase mb-1.5 px-2">
            INVESTIGATIONS
          </h4>
          <div className="space-y-0.5">
            {mainNav.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path, item.exact, (item as any).isActiveOverride);
              return (
                <NavLink
                  key={item.label}
                  to={item.path}
                  className={`flex items-center justify-between px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                    active
                      ? 'bg-[#E6B325] text-black font-bold shadow-sm'
                      : 'text-slate-300 hover:bg-[#161922] hover:text-white'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className={`w-3.5 h-3.5 ${active ? 'text-black' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                </NavLink>
              );
            })}
          </div>
        </div>

        {/* ANALYSIS */}
        <div>
          <h4 className="text-[10px] font-mono font-bold text-slate-400 tracking-wider uppercase mb-1.5 px-2">
            ANALYSIS
          </h4>
          <div className="space-y-0.5">
            {toolsNav.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path, false);
              return (
                <NavLink
                  key={item.label}
                  to={item.path}
                  className={`flex items-center justify-between px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                    active
                      ? 'bg-[#161922] text-blue-400'
                      : 'text-slate-300 hover:bg-[#161922] hover:text-white'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className={`w-3.5 h-3.5 ${active ? 'text-blue-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </div>
        </div>

        {/* SYSTEM */}
        <div>
          <h4 className="text-[10px] font-mono font-bold text-slate-400 tracking-wider uppercase mb-1.5 px-2">
            SYSTEM
          </h4>
          <div className="space-y-0.5">
            {systemNav.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.label}
                  to={item.path}
                  className="flex items-center justify-between px-3 py-1.5 rounded-md text-xs font-semibold text-slate-300 hover:bg-[#161922] hover:text-white transition-all"
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className="w-3.5 h-3.5 text-slate-400" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-full ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </div>
        </div>
      </div>

      {/* Bottom Sidebar Watermark / Motto */}
      <div className="p-3 border-t border-[#1E2430] bg-[#07090E] relative overflow-hidden flex flex-col justify-end min-h-[90px]">
        <img 
          src="/assets/sidebar_watermark.png" 
          alt="Watermark" 
          className="absolute right-0 bottom-0 w-28 opacity-25 pointer-events-none"
        />
        <div className="relative z-10">
          <div className="text-[#E6B325] font-extrabold text-sm tracking-widest font-sans leading-tight">
            कर्तव्य
          </div>
          <div className="text-[#E6B325] font-extrabold text-sm tracking-widest font-sans leading-tight">
            सेवा
          </div>
          <div className="text-[#E6B325] font-extrabold text-sm tracking-widest font-sans leading-tight">
            सुरक्षा
          </div>
        </div>
      </div>
    </aside>
  );
};

