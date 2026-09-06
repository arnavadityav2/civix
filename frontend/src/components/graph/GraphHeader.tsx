import React from 'react';
import { 
  Shield, 
  Search, 
  Bell, 
  User as UserIcon, 
  ChevronDown, 
  PhoneCall, 
  Star, 
  Network, 
  FileText, 
  Layers, 
  Brain, 
  BarChart3 
} from 'lucide-react';
import type { CaseListItem } from '../../types/api';

interface GraphHeaderProps {
  caseData?: CaseListItem | null;
  counts?: {
    entities: number;
    relationships: number;
    cases: number;
    events: number;
    evidence: number;
    leads: number;
  };
  activeTab: 'GRAPH' | 'CASE_CONTEXT' | 'INTELLIGENCE' | 'REPORTS';
  onTabChange: (tab: 'GRAPH' | 'CASE_CONTEXT' | 'INTELLIGENCE' | 'REPORTS') => void;
  isEvidenceVisible?: boolean;
  onToggleEvidence?: () => void;
}

export const GraphHeader: React.FC<GraphHeaderProps> = ({
  caseData,
  counts = { entities: 0, relationships: 0, cases: 0, events: 0, evidence: 0, leads: 0 },
  activeTab,
  onTabChange,
  isEvidenceVisible = false,
  onToggleEvidence,
}) => {
  const isGolden = caseData?.case_number?.startsWith('CIV-2012') || caseData?.case_number?.startsWith('CIV-2024') || caseData?.case_number?.startsWith('CIV-2026');

  return (
    <header className="bg-[#0b0f19] border-b border-[#1e2d4a] flex flex-col shrink-0 text-slate-200">
      {/* ── Compact Case Identity & Intelligence Counts Strip ── */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#0d1322] border-b border-[#162035]">
        {/* Left: Real Case Metadata */}
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 rounded">
            CASE / {caseData?.case_number || 'CIV-2012-001'}
          </span>
          <h1 className="text-sm font-bold text-white tracking-wide uppercase">
            {caseData?.title || 'DWARKA SECTOR 23 CASH VAN ROBBERY'}
          </h1>
          {isGolden && (
            <span className="flex items-center gap-1 text-[10px] font-bold bg-amber-950/80 border border-amber-500/60 text-amber-400 px-2 py-0.5 rounded tracking-wider">
              <Star className="w-3 h-3 fill-amber-400" /> GOLDEN CASE
            </span>
          )}
          <div className="flex items-center gap-2 text-xs text-slate-400 ml-2 font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block"></span>
            <span>{caseData?.status || 'Active'}</span>
            <span>•</span>
            <span>{caseData?.opened_at ? new Date(caseData.opened_at).toLocaleDateString() : '12 Apr 2012'}</span>
            <span>•</span>
            <span>{caseData?.jurisdiction || 'South West District, Delhi'}</span>
          </div>
        </div>

        {/* Right: Dynamic Intelligence Counts Strip */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-[#131b2e] border border-[#1e2d4a] px-2.5 py-1 rounded text-xs">
            <span className="font-bold text-cyan-400 font-mono">{counts.entities}</span>
            <span className="text-slate-400 text-[11px]">Entities</span>
          </div>
          <div className="flex items-center gap-1.5 bg-[#131b2e] border border-[#1e2d4a] px-2.5 py-1 rounded text-xs">
            <span className="font-bold text-cyan-400 font-mono">{counts.relationships}</span>
            <span className="text-slate-400 text-[11px]">Relationships</span>
          </div>
          <div className="flex items-center gap-1.5 bg-[#131b2e] border border-[#1e2d4a] px-2.5 py-1 rounded text-xs">
            <span className="font-bold text-blue-400 font-mono">{counts.cases}</span>
            <span className="text-slate-400 text-[11px]">Cases</span>
          </div>
          <div className="flex items-center gap-1.5 bg-[#131b2e] border border-[#1e2d4a] px-2.5 py-1 rounded text-xs">
            <span className="font-bold text-emerald-400 font-mono">{counts.events}</span>
            <span className="text-slate-400 text-[11px]">Events</span>
          </div>
          {onToggleEvidence ? (
            <button
              onClick={onToggleEvidence}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs border transition-colors ${
                isEvidenceVisible
                  ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300'
                  : 'bg-[#131b2e] border-[#1e2d4a] text-slate-400 hover:text-slate-200 hover:border-cyan-500/40'
              }`}
              title={isEvidenceVisible ? 'Click to hide evidence nodes' : 'Click to show evidence nodes'}
            >
              <span className="font-bold text-amber-400 font-mono">{counts.evidence}</span>
              <span className="text-[11px]">Evidence</span>
            </button>
          ) : (
            <div className="flex items-center gap-1.5 bg-[#131b2e] border border-[#1e2d4a] px-2.5 py-1 rounded text-xs">
              <span className="font-bold text-amber-400 font-mono">{counts.evidence}</span>
              <span className="text-slate-400 text-[11px]">Evidence</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 bg-[#131b2e] border border-[#1e2d4a] px-2.5 py-1 rounded text-xs">
            <span className="font-bold text-rose-400 font-mono">{counts.leads}</span>
            <span className="text-slate-400 text-[11px]">Leads</span>
          </div>
        </div>
      </div>

      {/* ── Primary Workspace Context Navigation Tabs ── */}
      <div className="flex items-center px-4 bg-[#090d16] border-t border-[#162035]">
        <button
          onClick={() => onTabChange('GRAPH')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === 'GRAPH'
              ? 'border-cyan-500 text-cyan-400 bg-[#111827]'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Network className="w-3.5 h-3.5" />
          <span>GRAPH & PROVENANCE</span>
        </button>

        <button
          onClick={() => onTabChange('CASE_CONTEXT')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === 'CASE_CONTEXT'
              ? 'border-cyan-500 text-cyan-400 bg-[#111827]'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>CASE CONTEXT</span>
        </button>

        <button
          onClick={() => onTabChange('INTELLIGENCE')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === 'INTELLIGENCE'
              ? 'border-cyan-500 text-cyan-400 bg-[#111827]'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Brain className="w-3.5 h-3.5" />
          <span>INTELLIGENCE</span>
        </button>

        <button
          onClick={() => onTabChange('REPORTS')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold border-b-2 transition-colors ${
            activeTab === 'REPORTS'
              ? 'border-cyan-500 text-cyan-400 bg-[#111827]'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>REPORTS</span>
        </button>
      </div>
    </header>
  );
};
