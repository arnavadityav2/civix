import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { leadsApi } from '../../api/leads';
import type { InvestigativeLeadResponse } from '../../types/api';
import { HierarchyBadge } from './HierarchyBadge';
import { X, CheckCircle, XCircle, Clock, Loader2 } from 'lucide-react';

interface LeadReviewModalProps {
  lead: InvestigativeLeadResponse;
  caseId: string;
  onClose: () => void;
}

export const LeadReviewModal: React.FC<LeadReviewModalProps> = ({ lead, caseId, onClose }) => {
  const [selectedStatus, setSelectedStatus] = useState<string>('CONFIRMED');
  const [notes, setNotes] = useState<string>('');
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () =>
      leadsApi.disposeLead(caseId, lead.lead_id, {
        status: selectedStatus,
        disposition_notes: notes,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads', caseId] });
      onClose();
    },
  });

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4">
      <div className="bg-white border border-slate-300 rounded-lg shadow-xl max-w-xl w-full overflow-hidden">
        {/* Header */}
        <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <HierarchyBadge tier="MODEL_SIGNAL" />
            <h3 className="text-sm font-bold tracking-tight">Investigator Lead Review</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="bg-slate-50 p-3.5 border border-slate-200 rounded">
            <h4 className="text-xs font-bold text-slate-900 font-sans mb-1">{lead.lead_text}</h4>
            <div className="flex items-center space-x-3 text-[11px] font-mono text-slate-600">
              <span>Behavioral Model Score: {lead.ai_confidence ? lead.ai_confidence.toFixed(3) : 'N/A'}</span>
              <span>•</span>
              <span>Priority: {lead.priority}</span>
              <span>•</span>
              <span>Status: {lead.status}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
              Select Disposition Action
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setSelectedStatus('CONFIRMED')}
                className={`py-2 px-3 border rounded text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors ${
                  selectedStatus === 'CONFIRMED'
                    ? 'bg-emerald-50 border-emerald-600 text-emerald-900 font-bold'
                    : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <CheckCircle className="w-3.5 h-3.5 text-emerald-700" />
                <span>Confirm Lead</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedStatus('FALSE_POSITIVE')}
                className={`py-2 px-3 border rounded text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors ${
                  selectedStatus === 'FALSE_POSITIVE'
                    ? 'bg-red-50 border-red-600 text-red-900 font-bold'
                    : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <XCircle className="w-3.5 h-3.5 text-red-700" />
                <span>False Positive</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedStatus('CLOSED')}
                className={`py-2 px-3 border rounded text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors ${
                  selectedStatus === 'CLOSED'
                    ? 'bg-slate-200 border-slate-600 text-slate-900 font-bold'
                    : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
                }`}
              >
                <Clock className="w-3.5 h-3.5 text-slate-700" />
                <span>Close Lead</span>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
              Investigator Rationale / Disposition Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record investigative basis for this disposition action..."
              className="w-full text-xs bg-slate-50 border border-slate-300 rounded p-2.5 text-slate-900 focus:outline-none focus:border-slate-800"
            />
          </div>

          {mutation.isError && (
            <div className="p-2.5 bg-red-50 border border-red-200 rounded text-xs text-red-800 font-mono">
              Failed to submit disposition action. State machine violation or permission error.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-50 border-t border-slate-200 px-6 py-3 flex items-center justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-white border border-slate-300 rounded text-xs font-semibold text-slate-700 hover:bg-slate-100"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !notes.trim()}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold flex items-center space-x-1.5 disabled:opacity-50"
          >
            {mutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <span>Save Disposition</span>
          </button>
        </div>
      </div>
    </div>
  );
};
