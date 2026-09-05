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
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-civix-surface border border-civix-border rounded-sm shadow-2xl max-w-xl w-full overflow-hidden">
        {/* Header */}
        <div className="civix-panel-header px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <HierarchyBadge tier="MODEL_SIGNAL" />
            <h3 className="civix-panel-title">Investigator Lead Review</h3>
          </div>
          <button onClick={onClose} className="text-civix-text-muted hover:text-civix-text-main p-1 rounded-sm">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="bg-civix-surface-2 p-3.5 border border-civix-border rounded-sm">
            <h4 className="text-xs font-bold text-civix-text-main font-sans mb-1">{lead.lead_text}</h4>
            <div className="flex items-center space-x-3 text-[11px] font-mono text-civix-text-secondary">
              <span>Behavioral Model Score: {lead.ai_confidence ? lead.ai_confidence.toFixed(3) : 'N/A'}</span>
              <span>•</span>
              <span>Priority: {lead.priority}</span>
              <span>•</span>
              <span>Status: {lead.status}</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-civix-text-muted uppercase tracking-wider mb-2">
              Select Disposition Action
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setSelectedStatus('CONFIRMED')}
                className={`py-2 px-3 border rounded-sm text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors ${
                  selectedStatus === 'CONFIRMED'
                    ? 'bg-civix-green-950 border-civix-green-600/50 text-civix-green-400 font-bold'
                    : 'bg-civix-surface-2 border-civix-border text-civix-text-secondary hover:bg-civix-surface'
                }`}
              >
                <CheckCircle className="w-3.5 h-3.5 text-civix-green-400" />
                <span>Confirm Lead</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedStatus('FALSE_POSITIVE')}
                className={`py-2 px-3 border rounded-sm text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors ${
                  selectedStatus === 'FALSE_POSITIVE'
                    ? 'bg-civix-red-950 border-civix-red-600/50 text-civix-red-400 font-bold'
                    : 'bg-civix-surface-2 border-civix-border text-civix-text-secondary hover:bg-civix-surface'
                }`}
              >
                <XCircle className="w-3.5 h-3.5 text-civix-red-400" />
                <span>False Positive</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedStatus('CLOSED')}
                className={`py-2 px-3 border rounded-sm text-xs font-semibold flex items-center justify-center space-x-1.5 transition-colors ${
                  selectedStatus === 'CLOSED'
                    ? 'bg-civix-surface-2 border-civix-border text-civix-text-main font-bold'
                    : 'bg-civix-surface-2 border-civix-border text-civix-text-secondary hover:bg-civix-surface'
                }`}
              >
                <Clock className="w-3.5 h-3.5 text-civix-text-muted" />
                <span>Close Lead</span>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-civix-text-muted uppercase tracking-wider mb-1">
              Investigator Rationale / Disposition Notes
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record investigative basis for this disposition action..."
              className="civix-input w-full p-2.5 text-xs"
            />
          </div>

          {mutation.isError && (
            <div className="p-2.5 bg-civix-red-950/40 border border-civix-red-600/40 rounded-sm text-xs text-civix-red-400 font-mono">
              Failed to submit disposition action. State machine violation or permission error.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-civix-surface-2 border-t border-civix-border px-6 py-3 flex items-center justify-end space-x-3">
          <button
            onClick={onClose}
            className="civix-btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !notes.trim()}
            className="civix-btn-primary"
          >
            {mutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            <span>Save Disposition</span>
          </button>
        </div>
      </div>
    </div>
  );
};
