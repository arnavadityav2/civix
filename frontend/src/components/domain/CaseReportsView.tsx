import React, { useState } from 'react';
import type { CaseListItem } from '../../types/api';
import { FileText, Download, Printer, Shield, CheckCircle2, AlertTriangle, FileSpreadsheet, Lock } from 'lucide-react';

interface CaseReportsViewProps {
  caseId: string;
  caseData?: CaseListItem | null;
}

export const CaseReportsView: React.FC<CaseReportsViewProps> = ({ caseId, caseData }) => {
  const [isExporting, setIsExporting] = useState(false);

  const handleExportPDF = () => {
    setIsExporting(true);
    setTimeout(() => {
      window.print();
      setIsExporting(false);
    }, 500);
  };

  return (
    <div className="space-y-6 font-mono text-slate-100">
      {/* Report Action Toolbar */}
      <div className="bg-[#0C1220] border border-[#1E293B] p-4 rounded-md flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-950/60 border border-blue-800/50 rounded text-cyan-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
              Official Case Investigation Intelligence Report
            </h2>
            <p className="text-xs text-slate-400 font-sans">
              Delhi Police Command Center • Executive Dossier Export Format
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleExportPDF}
            disabled={isExporting}
            className="civix-btn-primary py-2 px-4 text-xs font-mono font-bold flex items-center space-x-2 shadow-md cursor-pointer"
          >
            <Printer className="w-4 h-4" />
            <span>{isExporting ? 'Preparing Print...' : 'Print / Export PDF Dossier'}</span>
          </button>
        </div>
      </div>

      {/* Main Printable Intelligence Dossier Document */}
      <div className="bg-[#0A0E17] border border-[#1E293B] rounded-md p-8 space-y-8 shadow-2xl">
        {/* Document Header */}
        <div className="border-b border-[#1E293B] pb-6 flex items-start justify-between">
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <span className="bg-red-950/80 text-red-400 border border-red-800/60 text-[9px] font-bold px-2 py-0.5 rounded uppercase tracking-widest">
                RESTRICTED • POLICE USE ONLY
              </span>
              <span className="text-xs font-bold text-slate-400">
                CASE FILE #{caseData?.case_number || caseId}
              </span>
            </div>

            <h1 className="text-2xl font-extrabold text-white font-sans tracking-tight">
              {caseData?.title || 'Case Intelligence Dossier'}
            </h1>

            <p className="text-xs text-slate-400 font-sans">
              Jurisdiction: <strong className="text-slate-200">{caseData?.jurisdiction || 'Delhi NCR'}</strong> • Police Station: <strong className="text-slate-200">{caseData?.police_station || 'Dwarka PS'}</strong>
            </p>
          </div>

          <div className="text-right font-mono text-xs space-y-1 text-slate-400">
            <p className="font-bold text-white uppercase">DELHI POLICE HEADQUARTERS</p>
            <p>Intelligence Division</p>
            <p className="text-[10px] text-cyan-400 mt-2">Generated: 07 Sept 2026</p>
          </div>
        </div>

        {/* Executive Summary Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#0C1220] p-4 rounded border border-[#1E293B] space-y-1">
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block">CASE STATUS</span>
            <span className="text-sm font-bold text-green-400 uppercase">{caseData?.status || 'ACTIVE'}</span>
          </div>

          <div className="bg-[#0C1220] p-4 rounded border border-[#1E293B] space-y-1">
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block">PRIORITY LEVEL</span>
            <span className="text-sm font-bold text-red-400 uppercase">{caseData?.priority || 'CRITICAL'}</span>
          </div>

          <div className="bg-[#0C1220] p-4 rounded border border-[#1E293B] space-y-1">
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block">INVESTIGATION UNIT</span>
            <span className="text-sm font-bold text-slate-200 font-sans truncate block">{caseData?.police_station || 'Dwarka PS Crime Branch'}</span>
          </div>
        </div>

        {/* Operational Synopsis */}
        <div className="space-y-2 border-b border-[#1E293B] pb-6">
          <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center space-x-2">
            <Shield className="w-4 h-4" />
            <span>1. Operational Synopsis & Background</span>
          </h3>
          <p className="text-xs text-slate-300 font-sans leading-relaxed bg-[#0C1220] p-4 rounded border border-[#1E293B]">
            {caseData?.investigating_unit || 'Armed cash-van robbery in Dwarka Sector 23, New Delhi. Multiple suspects intercepted the vehicle, looted cash consignments, and fled using a stolen getaway vehicle. Case involves CDR tower dumps, CCTV spatial correlation, and multi-entity graph analysis.'}
          </p>
        </div>

        {/* Linked Intelligence Breakdown */}
        <div className="space-y-4 border-b border-[#1E293B] pb-6">
          <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-green-400" />
            <span>2. Comprehensive Case Metrics</span>
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="p-3 bg-[#0C1220] border border-[#1E293B] rounded">
              <span className="text-slate-400 text-[10px] block">PERSON ENTITIES</span>
              <strong className="text-white text-base">8 Linked</strong>
            </div>

            <div className="p-3 bg-[#0C1220] border border-[#1E293B] rounded">
              <span className="text-slate-400 text-[10px] block">TELECOM CDR RECORDS</span>
              <strong className="text-white text-base">15,030 Phone Numbers</strong>
            </div>

            <div className="p-3 bg-[#0C1220] border border-[#1E293B] rounded">
              <span className="text-slate-400 text-[10px] block">EVIDENCE ARTIFACTS</span>
              <strong className="text-white text-base">35 Items</strong>
            </div>

            <div className="p-3 bg-[#0C1220] border border-[#1E293B] rounded">
              <span className="text-slate-400 text-[10px] block">SPATIAL LOCATIONS</span>
              <strong className="text-white text-base">17 Event Nodes</strong>
            </div>
          </div>
        </div>

        {/* Security & Confidentiality Footer */}
        <div className="pt-4 flex items-center justify-between text-[10px] text-slate-500 font-mono border-t border-[#1E293B]">
          <div className="flex items-center space-x-1.5">
            <Lock className="w-3 h-3 text-amber-500" />
            <span>OFFICIAL DEMO CASE REPORT • DELHI POLICE INTEL WORKSTATION</span>
          </div>
          <span>PAGE 1 OF 1</span>
        </div>
      </div>
    </div>
  );
};
