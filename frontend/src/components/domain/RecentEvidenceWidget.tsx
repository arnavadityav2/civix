import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { evidenceApi } from '../../api/evidence';
import { useCaseSelection } from '../../context/CaseSelectionContext';
import { Panel } from '../ui/Panel';
import { Badge } from '../ui/Badge';
import { ArrowRight, Loader2, FileCheck, FileClock, AlertCircle } from 'lucide-react';

export const RecentEvidenceWidget: React.FC = () => {
  const { selectedCaseId } = useCaseSelection();

  const { data: evidence = [], isLoading, error } = useQuery({
    queryKey: ['evidence', selectedCaseId],
    queryFn: () => (selectedCaseId ? evidenceApi.listEvidence(selectedCaseId) : Promise.resolve([])),
    enabled: !!selectedCaseId,
  });

  return (
    <Panel
      title="RECENT EVIDENCE LOG"
      headerAction={
        <button className="text-xs font-semibold text-blue-700 hover:text-blue-900 flex items-center space-x-1">
          <span>View All Evidence</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      }
      className="h-full"
    >
      {!selectedCaseId ? (
        <div className="py-8 text-center text-xs text-slate-500 font-mono">
          Select a case to view recent evidence.
        </div>
      ) : isLoading ? (
        <div className="py-8 flex items-center justify-center text-slate-400 space-x-2 text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-amber-600" />
          <span>Fetching evidence log...</span>
        </div>
      ) : error ? (
        <div className="py-4 text-center text-xs text-red-600 font-mono">
          Failed to load evidence log for selected case.
        </div>
      ) : evidence.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500 font-mono">
          No evidence artifacts ingested for this case.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-[10px] font-bold text-slate-600 uppercase tracking-wider">
                <th className="py-2 px-3">ID / Artifact</th>
                <th className="py-2 px-3">MIME / Type</th>
                <th className="py-2 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs font-sans">
              {evidence.slice(0, 5).map((item) => (
                <tr key={item.artifact_id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-2.5 px-3">
                    <div className="font-semibold text-slate-900 truncate max-w-[160px]">
                      {item.original_filename || 'Evidence File'}
                    </div>
                    <div className="text-[10px] font-mono text-slate-500">
                      ID: {item.artifact_id.slice(0, 8)}...
                    </div>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-[11px] text-slate-600">
                    {item.mime_type || 'application/octet-stream'}
                  </td>
                  <td className="py-2.5 px-3">
                    {item.processing_status === 'COMPLETED' || item.processing_status === 'STORED' ? (
                      <Badge variant="confirmed" className="flex items-center space-x-1 w-fit">
                        <FileCheck className="w-3 h-3 mr-1" />
                        <span>PROCESSED</span>
                      </Badge>
                    ) : item.processing_status === 'PROCESSING' ? (
                      <Badge variant="warning" className="flex items-center space-x-1 w-fit">
                        <FileClock className="w-3 h-3 mr-1 animate-pulse" />
                        <span>PARSING</span>
                      </Badge>
                    ) : (
                      <Badge variant="critical" className="flex items-center space-x-1 w-fit">
                        <AlertCircle className="w-3 h-3 mr-1" />
                        <span>{item.processing_status}</span>
                      </Badge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
};
