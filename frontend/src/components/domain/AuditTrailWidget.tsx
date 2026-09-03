import React from 'react';
import { Panel } from '../ui/Panel';
import { ArrowRight, Clock } from 'lucide-react';

interface AuditItem {
  id: string;
  time: string;
  tag: string;
  message: string;
}

export const AuditTrailWidget: React.FC = () => {
  const auditLogs: AuditItem[] = [
    {
      id: '1',
      time: '13:42',
      tag: 'CASE-2026-0142',
      message: 'New deterministic assertion established via corporate registrar ingestion.',
    },
    {
      id: '2',
      time: '12:58',
      tag: 'SYSTEM',
      message: 'Evidence ingestion completed for active workspace.',
    },
    {
      id: '3',
      time: '11:21',
      tag: 'CASE-2026-0138',
      message: 'Investigator updated case clearance context.',
    },
  ];


  return (
    <Panel
      title="AUDIT TRAIL"
      headerAction={
        <button className="text-xs font-semibold text-blue-700 hover:text-blue-900 flex items-center space-x-1">
          <span>View Full Audit Log</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      }
      className="h-full"
    >
      <div className="space-y-3 relative before:absolute before:inset-0 before:left-2 before:w-0.5 before:bg-slate-200">
        {auditLogs.map((item) => (
          <div key={item.id} className="relative flex items-start space-x-3 pl-6">
            <div className="absolute left-0 top-1 w-4 h-4 rounded-full bg-white border-2 border-slate-700 flex items-center justify-center">
              <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <span className="text-[11px] font-mono font-semibold text-slate-500 flex items-center">
                  <Clock className="w-3 h-3 mr-1 inline text-slate-400" />
                  {item.time}
                </span>
                <span className="text-[10px] font-mono font-bold bg-slate-100 text-slate-800 px-1.5 py-0.5 rounded border border-slate-200">
                  {item.tag}
                </span>
              </div>
              <p className="text-xs text-slate-800 mt-1 leading-snug font-sans">
                {item.message}
              </p>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
};
