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
        <button className="text-[11px] font-semibold text-civix-blue-light hover:text-civix-text-primary flex items-center space-x-1 transition-colors font-mono">
          <span>View All Evidence</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      }
      className="h-full"
    >
      {!selectedCaseId ? (
        <div className="py-8 text-center text-xs text-civix-text-muted font-mono">
          Select a case to view recent evidence.
        </div>
      ) : isLoading ? (
        <div className="py-8 flex items-center justify-center text-civix-text-muted space-x-2 text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-civix-blue-light" />
          <span>Fetching evidence log...</span>
        </div>
      ) : error ? (
        <div className="py-4 text-center text-xs text-civix-red font-mono">
          Failed to load evidence log for selected case.
        </div>
      ) : evidence.length === 0 ? (
        <div className="py-8 text-center text-xs text-civix-text-muted font-mono">
          No evidence artifacts ingested for this case.
        </div>
      ) : (
        <div className="overflow-x-auto -mx-4 -mb-4">
          <table className="civix-table">
            <thead className="civix-table-header">
              <tr>
                <th className="py-2 px-3">ARTIFACT</th>
                <th className="py-2 px-3">TYPE</th>
                <th className="py-2 px-3">STATUS</th>
              </tr>
            </thead>
            <tbody className="civix-table-body">
              {evidence.slice(0, 5).map((item) => (
                <tr key={item.artifact_id} className="hover:bg-civix-surface-3 cursor-pointer transition-colors">
                  <td className="py-2 px-3">
                    <div className="font-semibold text-civix-text-primary text-xs truncate max-w-[160px]">
                      {item.original_filename || 'Evidence File'}
                    </div>
                    <div className="text-[10px] font-mono text-civix-text-mono mt-0.5">
                      ID: {item.artifact_id.slice(0, 8)}...
                    </div>
                  </td>
                  <td className="py-2 px-3 font-mono text-[10px] text-civix-text-muted">
                    {item.mime_type || 'application/octet-stream'}
                  </td>
                  <td className="py-2 px-3">
                    {item.processing_status === 'COMPLETED' || item.processing_status === 'STORED' || item.processing_status === 'GENERATED' ? (
                      <Badge variant="confirmed" className="flex items-center space-x-1 w-fit">
                        <FileCheck className="w-2.5 h-2.5 mr-1" />
                        <span>PROCESSED</span>
                      </Badge>
                    ) : item.processing_status === 'PROCESSING' ? (
                      <Badge variant="warning" className="flex items-center space-x-1 w-fit">
                        <FileClock className="w-2.5 h-2.5 mr-1 animate-pulse" />
                        <span>PARSING</span>
                      </Badge>
                    ) : (
                      <Badge variant="critical" className="flex items-center space-x-1 w-fit">
                        <AlertCircle className="w-2.5 h-2.5 mr-1" />
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
