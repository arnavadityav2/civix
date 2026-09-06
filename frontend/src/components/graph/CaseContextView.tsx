import React from 'react';
import { 
  Briefcase, 
  ShieldCheck, 
  MapPin, 
  Calendar, 
  UserCheck, 
  FileText, 
  Layers, 
  Users, 
  GitFork,
  Scale
} from 'lucide-react';
import type { CaseListItem, CaseEntityRoleListItem } from '../../types/api';

interface CaseContextViewProps {
  caseData?: CaseListItem;
  caseEntities?: CaseEntityRoleListItem[];
  onSelectEntity?: (entityId: string) => void;
}

export const CaseContextView: React.FC<CaseContextViewProps> = ({
  caseData,
  caseEntities = [],
  onSelectEntity,
}) => {
  if (!caseData) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-slate-500 font-mono text-xs select-none">
        <Briefcase className="w-8 h-8 text-slate-600 mb-2 stroke-1" />
        <span>LOADING CASE CONTEXT...</span>
      </div>
    );
  }

  const suspectCount = caseEntities.filter((e) => e.role === 'SUSPECT' || e.role === 'ACCUSED').length;
  const officerCount = caseEntities.filter((e) => e.role === 'INVESTIGATING_OFFICER' || e.role === 'OFFICER_IN_CHARGE').length;

  return (
    <div className="h-full w-full bg-[#0b0f19] overflow-y-auto p-6 text-slate-200 font-sans select-none antialiased space-y-6">
      {/* Workstation Header (No giant hero banner) */}
      <div className="p-4 rounded bg-[#0d1322] border border-[#1e2d4a] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded bg-cyan-950 border border-cyan-500/60 flex items-center justify-center text-cyan-400 font-bold shrink-0">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                {caseData.case_number}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-500/60 text-emerald-400 font-bold uppercase">
                {caseData.status}
              </span>
            </div>
            <h1 className="text-lg font-bold text-white leading-tight mt-0.5">
              {caseData.title}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
          {caseData.police_station && (
            <div className="flex items-center gap-1.5 bg-[#131b2e] px-2.5 py-1 rounded border border-[#1e2d4a]">
              <MapPin className="w-3.5 h-3.5 text-cyan-400" />
              <span>{caseData.police_station}, {caseData.district || 'Delhi'}</span>
            </div>
          )}
          {caseData.opened_at && (
            <div className="flex items-center gap-1.5 bg-[#131b2e] px-2.5 py-1 rounded border border-[#1e2d4a]">
              <Calendar className="w-3.5 h-3.5 text-cyan-400" />
              <span>{new Date(caseData.opened_at).toLocaleDateString()}</span>
            </div>
          )}
        </div>
      </div>

      {/* Case Metadata Breakdown Grid */}
      <div className="grid grid-cols-4 gap-4 text-xs">
        <div className="p-3 rounded bg-[#0d1322] border border-[#1e2d4a] space-y-1">
          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">JURISDICTION</span>
          <p className="font-bold text-white font-mono">{caseData.jurisdiction || 'Delhi PS'}</p>
        </div>
        <div className="p-3 rounded bg-[#0d1322] border border-[#1e2d4a] space-y-1">
          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">INVESTIGATING UNIT</span>
          <p className="font-bold text-white font-mono">{caseData.investigating_unit || 'Dwarka Crime Unit'}</p>
        </div>
        <div className="p-3 rounded bg-[#0d1322] border border-[#1e2d4a] space-y-1">
          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">CASE TYPE</span>
          <p className="font-bold text-cyan-400 font-mono">{caseData.case_type || 'INVESTIGATION'}</p>
        </div>
        <div className="p-3 rounded bg-[#0d1322] border border-[#1e2d4a] space-y-1">
          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">FIR NUMBER</span>
          <p className="font-bold text-white font-mono">{caseData.fir_number || 'CIV-FIR-2012-001'}</p>
        </div>
      </div>

      {/* Linked Case Entities Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Users className="w-4 h-4 text-cyan-400" />
            <span>AUTHORITATIVE CASE ENTITY ROLES ({caseEntities.length})</span>
          </h2>
          <span className="text-[10px] font-mono text-slate-400 bg-[#0d1322] px-2 py-0.5 rounded border border-[#1e2d4a]">
            SOURCE: civix.case_entity_role
          </span>
        </div>

        <div className="bg-[#0d1322] border border-[#1e2d4a] rounded overflow-hidden">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-[#0b0f19] border-b border-[#1e2d4a] font-mono text-[10px] text-slate-400 uppercase tracking-wider">
                <th className="p-3">Entity Name</th>
                <th className="p-3">Entity Type</th>
                <th className="p-3">Assigned Role</th>
                <th className="p-3">Role Basis</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#162035]">
              {caseEntities.length === 0 ? (
                <tr>
                  <td colSpan={4} className="p-4 text-center text-slate-500 font-mono text-xs italic">
                    No active entity roles linked to this case.
                  </td>
                </tr>
              ) : (
                caseEntities.map((ent) => (
                  <tr
                    key={ent.role_id}
                    onClick={() => onSelectEntity && onSelectEntity(ent.entity_id)}
                    className="hover:bg-[#131b2e] cursor-pointer transition-colors"
                  >
                    <td className="p-3 font-semibold text-white">{ent.display_name}</td>
                    <td className="p-3 font-mono text-cyan-400 text-[11px]">{ent.entity_type}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                        ent.role === 'SUSPECT' || ent.role === 'ACCUSED'
                          ? 'bg-rose-950/80 border-rose-500/60 text-rose-300'
                          : ent.role === 'INVESTIGATING_OFFICER'
                          ? 'bg-cyan-950/80 border-cyan-500/60 text-cyan-300'
                          : 'bg-[#131b2e] border-slate-700 text-slate-300'
                      }`}>
                        {ent.role}
                      </span>
                    </td>
                    <td className="p-3 font-mono text-slate-400 text-[11px]">{ent.role_basis || 'Direct Record'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
