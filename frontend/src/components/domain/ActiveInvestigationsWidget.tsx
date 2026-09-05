import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { casesApi } from '../../api/cases';
import { useCaseSelection } from '../../context/CaseSelectionContext';
import { Panel } from '../ui/Panel';
import { Badge } from '../ui/Badge';
import { Copy, ArrowRight, Loader2 } from 'lucide-react';

export const ActiveInvestigationsWidget: React.FC = () => {
  const { selectedCaseId, setSelectedCaseId } = useCaseSelection();

  const { data: cases = [], isLoading, error } = useQuery({
    queryKey: ['cases'],
    queryFn: casesApi.listCases,
  });

  // Auto-select first case if none selected
  React.useEffect(() => {
    if (cases.length > 0 && !selectedCaseId) {
      setSelectedCaseId(cases[0].case_id);
    }
  }, [cases, selectedCaseId, setSelectedCaseId]);

  const activeCount = cases.filter(c => c.status === 'OPEN' || c.status === 'ACTIVE').length;

  const copyToClipboard = (text: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
  };

  return (
    <Panel
      title={`ACTIVE INVESTIGATIONS`}
      subtitle={`${activeCount} active · ${cases.length} total`}
      headerAction={
        <button className="text-[11px] font-semibold text-civix-blue-light hover:text-civix-text-primary flex items-center space-x-1 transition-colors font-mono">
          <span>View All Cases</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      }
      className="h-full"
    >
      {isLoading ? (
        <div className="py-8 flex items-center justify-center text-civix-text-muted space-x-2 text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-civix-blue-light" />
          <span>Fetching active cases...</span>
        </div>
      ) : error ? (
        <div className="py-4 text-center text-xs text-civix-red font-mono">
          Failed to load cases from backend.
        </div>
      ) : cases.length === 0 ? (
        <div className="py-8 text-center text-xs text-civix-text-muted font-mono">
          No active cases found.
        </div>
      ) : (
        <div className="overflow-x-auto -mx-4 -mb-4">
          <table className="civix-table">
            <thead className="civix-table-header">
              <tr>
                <th className="py-2 px-3">CASE ID</th>
                <th className="py-2 px-3">TITLE / SUBJECT</th>
                <th className="py-2 px-3">STATUS</th>
                <th className="py-2 px-3">PRIORITY</th>
                <th className="py-2 px-3">JURISDICTION</th>
                <th className="py-2 px-3">LAST ACTIVITY</th>
              </tr>
            </thead>
            <tbody className="civix-table-body">
              {cases.map((c) => {
                const isSelected = selectedCaseId === c.case_id;
                return (
                  <tr
                    key={c.case_id}
                    onClick={() => setSelectedCaseId(c.case_id)}
                    className={`cursor-pointer ${isSelected ? 'civix-row-selected' : ''}`}
                  >
                    <td className="py-2 px-3">
                      <div className="flex items-center space-x-1.5">
                        <span className="font-mono text-[11px] text-civix-text-mono">
                          {c.case_number || c.case_id.slice(0, 8)}
                        </span>
                        <button
                          onClick={(e) => copyToClipboard(c.case_number || c.case_id, e)}
                          className="text-civix-text-muted hover:text-civix-text-secondary p-0.5 rounded transition-colors"
                          title="Copy Case ID"
                        >
                          <Copy className="w-2.5 h-2.5" />
                        </button>
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <div className="font-semibold text-civix-text-primary text-xs">{c.title}</div>
                      <div className="text-[10px] text-civix-text-muted font-mono mt-0.5">{c.case_type}</div>
                    </td>
                    <td className="py-2 px-3">
                      <Badge variant={c.status === 'OPEN' || c.status === 'ACTIVE' ? 'active' : 'closed'}>
                        {c.status}
                      </Badge>
                    </td>
                    <td className="py-2 px-3">
                      <Badge
                        variant={
                          c.priority === 'HIGH' ? 'critical' : c.priority === 'MEDIUM' ? 'warning' : 'default'
                        }
                      >
                        {c.priority}
                      </Badge>
                    </td>
                    <td className="py-2 px-3 font-mono text-[10px] text-civix-text-muted">
                      {c.jurisdiction}
                    </td>
                    <td className="py-2 px-3 font-mono text-[10px] text-civix-text-muted">
                      —
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
};
