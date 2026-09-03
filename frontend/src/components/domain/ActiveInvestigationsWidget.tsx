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
      title={`ACTIVE INVESTIGATIONS (${activeCount} ACTIVE)`}
      headerAction={
        <button className="text-xs font-semibold text-blue-700 hover:text-blue-900 flex items-center space-x-1">
          <span>View All Cases</span>
          <ArrowRight className="w-3 h-3" />
        </button>
      }
      className="h-full"
    >
      {isLoading ? (
        <div className="py-8 flex items-center justify-center text-slate-400 space-x-2 text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-amber-600" />
          <span>Fetching active cases...</span>
        </div>
      ) : error ? (
        <div className="py-4 text-center text-xs text-red-600 font-mono">
          Failed to load cases from backend.
        </div>
      ) : cases.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500 font-mono">
          No active cases found.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-[10px] font-bold text-slate-600 uppercase tracking-wider">
                <th className="py-2 px-3">Case ID</th>
                <th className="py-2 px-3">Title / Subject</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3">Priority</th>
                <th className="py-2 px-3">Jurisdiction</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs font-sans">
              {cases.map((c) => {
                const isSelected = selectedCaseId === c.case_id;
                return (
                  <tr
                    key={c.case_id}
                    onClick={() => setSelectedCaseId(c.case_id)}
                    className={`cursor-pointer transition-colors ${
                      isSelected ? 'bg-blue-50/70 border-l-3 border-blue-700' : 'hover:bg-slate-50'
                    }`}
                  >
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-900">
                      <div className="flex items-center space-x-1.5">
                        <span>{c.case_number || c.case_id.slice(0, 8)}</span>
                        <button
                          onClick={(e) => copyToClipboard(c.case_number || c.case_id, e)}
                          className="text-slate-400 hover:text-slate-700 p-0.5 rounded"
                          title="Copy Case ID"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                      </div>
                    </td>
                    <td className="py-2.5 px-3">
                      <div className="font-semibold text-slate-900">{c.title}</div>
                      <div className="text-[11px] text-slate-500 font-mono">{c.case_type}</div>
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge variant={c.status === 'OPEN' || c.status === 'ACTIVE' ? 'active' : 'closed'}>
                        {c.status}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge
                        variant={
                          c.priority === 'HIGH' ? 'critical' : c.priority === 'MEDIUM' ? 'warning' : 'default'
                        }
                      >
                        {c.priority}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-slate-600 text-[11px]">
                      {c.jurisdiction}
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
