import React from 'react';
import { Panel } from '../ui/Panel';
import { ArrowRight, Clock } from 'lucide-react';

interface AuditItem {
  id: string;
  time: string;
  tag: string;
  tagType: 'case' | 'system' | 'signal';
  message: string;
}

export const AuditTrailWidget: React.FC = () => {
  const auditLogs: AuditItem[] = [
    {
      id: '1',
      time: '13:42',
      tag: 'CASE-2026-0142',
      tagType: 'case',
      message: 'New deterministic assertion established via corporate registrar ingestion.',
    },
    {
      id: '2',
      time: '12:58',
      tag: 'SYSTEM',
      tagType: 'system',
      message: 'Evidence ingestion completed for active workspace.',
    },
    {
      id: '3',
      time: '11:21',
      tag: 'CASE-2026-0138',
      tagType: 'case',
      message: 'Investigator updated case clearance context.',
    },
  ];

  const tagStyles: Record<string, string> = {
    case:   'bg-civix-blue-subtle text-civix-blue-light border-civix-blue-muted',
    system: 'bg-civix-surface-3 text-civix-text-secondary border-civix-border',
    signal: 'bg-civix-red-subtle text-civix-red-light border-civix-red-muted',
  };

  return (
    <Panel
      title="AUDIT TRAIL"
      headerAction={
        <button className="text-[11px] font-semibold text-civix-blue-light hover:text-civix-text-primary flex items-center space-x-1 transition-colors font-mono">
          <span>View Full Audit Log</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      }
      className="h-full"
    >
      {/* Timeline: uses left border line instead of white pseudo-element */}
      <div className="space-y-4 relative">
        <div className="absolute left-2 top-2 bottom-2 w-px bg-civix-border-strong" />
        {auditLogs.map((item) => (
          <div key={item.id} className="relative flex items-start space-x-3 pl-6">
            {/* Timeline dot */}
            <div className="absolute left-0 top-1 w-4 h-4 rounded-full bg-civix-surface-3 border-2 border-civix-border-strong flex items-center justify-center">
              <div className="w-1.5 h-1.5 rounded-full bg-civix-text-secondary" />
            </div>

            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-[10px] font-mono font-semibold text-civix-text-muted flex items-center">
                  <Clock className="w-2.5 h-2.5 mr-1 text-civix-text-muted" />
                  {item.time} IST
                </span>
                <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm border uppercase tracking-widest ${tagStyles[item.tagType]}`}>
                  {item.tag}
                </span>
              </div>
              <p className="text-xs text-civix-text-secondary leading-snug font-sans">
                {item.message}
              </p>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
};
