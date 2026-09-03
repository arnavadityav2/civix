import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useCaseSelection } from '../../context/CaseSelectionContext';
import { 
  Plus, 
  LayoutDashboard, 
  Briefcase, 
  Users, 
  FileText, 
  GitFork, 
  Sparkles, 
  Search, 
  Eye, 
  Clock, 
  Navigation, 
  DollarSign, 
  Video, 
  MessageSquare, 
  ShieldAlert, 
  Settings,
  LogOut,
  ChevronRight
} from 'lucide-react';

interface AppSidebarProps {
  onNewCaseClick?: () => void;
}

export const AppSidebar: React.FC<AppSidebarProps> = ({ onNewCaseClick }) => {
  const location = useLocation();
  const { selectedCaseId } = useCaseSelection();

  const mainNav = [
    { label: 'Command Center', icon: LayoutDashboard, path: '/', exact: true },
    { label: 'Cases', icon: Briefcase, path: '/cases', exact: false },
    { label: 'Entities', icon: Users, path: '/entities', exact: false },
    { label: 'Evidence', icon: FileText, path: '/evidence', exact: false },
    { 
      label: 'Investigative Graph', 
      icon: GitFork, 
      path: selectedCaseId ? `/cases/${selectedCaseId}/graph` : '/cases', 
      exact: false,
      isActiveOverride: () => location.pathname.includes('/graph') 
    },
    { label: 'Investigative Leads', icon: Sparkles, path: '/leads', exact: false },
  ];

  // Analysis tools — Global Search is live, others are phase-gated
  const toolsNavLive = [
    { label: 'Global Search', icon: Search, path: '/search', badge: 'READY' },
    { label: 'CCTV Analysis', icon: Video, path: '/cctv', badge: 'PHASE A' },
  ];
  const toolsNavFuture = [
    { label: 'Surveillance', icon: Eye, badge: 'PHASE 3' },
    { label: 'Timeline', icon: Clock, badge: 'PHASE 3' },
    { label: 'Movement Analysis', icon: Navigation, badge: 'PHASE 3' },
    { label: 'Financial Flow', icon: DollarSign, badge: 'PHASE 3' },
    { label: 'Ask CIVIX', icon: MessageSquare, badge: 'AI' },
  ];

  const systemNav = [
    { label: 'Audit Log', icon: ShieldAlert },
    { label: 'Settings', icon: Settings },
  ];

  function isActive(path: string, exact: boolean, override?: () => boolean) {
    if (override) return override();
    if (exact) return location.pathname === path;
    return location.pathname.startsWith(path);
  }

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col flex-shrink-0 min-h-[calc(100vh-61px)] shadow-2xs">
      {/* Top Primary Action */}
      <div className="p-4 border-b border-slate-100">
        <NavLink
          to="/cases"
          onClick={onNewCaseClick}
          className="w-full bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs py-2.5 px-4 rounded flex items-center justify-center space-x-2 transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4 text-amber-500" />
          <span>New Case</span>
        </NavLink>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto py-3 px-3 space-y-6">
        {/* INVESTIGATIONS Section */}
        <div>
          <h4 className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">
            INVESTIGATIONS
          </h4>
          <div className="space-y-1">
            {mainNav.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path, item.exact, (item as any).isActiveOverride);
              return (
                <NavLink
                  key={item.label}
                  to={item.path}
                  className={`flex items-center justify-between px-3 py-2 rounded text-xs font-semibold transition-colors ${
                    active
                      ? 'bg-blue-50 text-blue-900 border-l-2 border-blue-700'
                      : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className={`w-4 h-4 ${active ? 'text-blue-700' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {active && <ChevronRight className="w-3.5 h-3.5 text-blue-700" />}
                </NavLink>
              );
            })}
          </div>
        </div>

        {/* ANALYSIS Section */}
        <div>
          <h4 className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">
            ANALYSIS
          </h4>
          <div className="space-y-0.5">
            {/* Live tools — full NavLink */}
            {toolsNavLive.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path, false);
              return (
                <NavLink
                  key={item.label}
                  to={item.path}
                  className={`flex items-center justify-between px-3 py-1.5 rounded text-xs font-semibold transition-colors ${
                    active
                      ? 'bg-blue-50 text-blue-900 border-l-2 border-blue-700'
                      : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className={`w-3.5 h-3.5 ${active ? 'text-blue-700' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {item.badge}
                  </span>
                </NavLink>
              );
            })}
            {/* Phase-gated — non-navigable */}
            {toolsNavFuture.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  className="flex items-center justify-between px-3 py-1.5 rounded text-xs text-slate-500 cursor-default"
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon className="w-3.5 h-3.5 text-slate-300" />
                    <span className="text-slate-400">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-400 border border-slate-200">
                      {item.badge}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* SYSTEM Section */}
        <div>
          <h4 className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">
            SYSTEM
          </h4>

          <div className="space-y-0.5">
            {systemNav.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  className="flex items-center space-x-2.5 px-3 py-1.5 rounded text-xs text-slate-600 hover:bg-slate-50 cursor-pointer transition-colors"
                >
                  <Icon className="w-3.5 h-3.5 text-slate-400" />
                  <span>{item.label}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* User Footer Profile */}
      <div className="p-3 border-t border-slate-200 bg-slate-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-7 h-7 rounded bg-slate-900 text-white font-mono text-[11px] font-bold flex items-center justify-center border border-slate-800">
              VS
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-bold text-slate-900 leading-tight">Vikram Singh</span>
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">INVESTIGATOR</span>
            </div>
          </div>
          <button className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded transition-colors" title="Logout">
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
};


