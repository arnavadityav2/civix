import React from 'react';
import { 
  GitFork, 
  AlertTriangle, 
  ShieldCheck, 
  Sparkles,
  Link2,
  FileText
} from 'lucide-react';

export interface ConnectionInspectorProps {
  relationship: {
    id: string;
    sourceName: string;
    targetName: string;
    predicate: string;
    isModelGenerated: boolean;
    modelScore?: number;
    explanation?: string;
    status: string;
    provenance?: string;
  };
  onClose: () => void;
}

export const EntityConnectionInspector: React.FC<ConnectionInspectorProps> = ({ 
  relationship, 
  onClose 
}) => {
  if (!relationship) return null;

  return (
    <div className="w-80 bg-civix-surface border-l border-civix-border flex flex-col h-full shadow-2xl flex-shrink-0">
      <div className="p-4 border-b border-civix-border flex items-center justify-between bg-civix-surface-2">
        <div className="flex items-center space-x-2">
          {relationship.isModelGenerated ? (
            <Sparkles className="w-4 h-4 text-civix-gold" />
          ) : (
            <Link2 className="w-4 h-4 text-civix-blue-400" />
          )}
          <h3 className="text-sm font-bold text-white uppercase tracking-widest font-mono">
            {relationship.isModelGenerated ? 'MODEL-GENERATED LEAD' : 'RELATIONSHIP'}
          </h3>
        </div>
        <button 
          onClick={onClose}
          className="text-civix-text-muted hover:text-white transition-colors"
        >
          &times;
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        
        {/* ENTITIES */}
        <div className="space-y-2">
          <div className="bg-civix-surface-2 border border-civix-border p-2 rounded-sm">
            <span className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider block mb-1">SOURCE</span>
            <span className="text-xs font-bold text-civix-text-main">{relationship.sourceName}</span>
          </div>
          <div className="flex justify-center text-civix-text-muted">
            <GitFork className="w-4 h-4 rotate-90" />
          </div>
          <div className="bg-civix-surface-2 border border-civix-border p-2 rounded-sm">
            <span className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider block mb-1">TARGET</span>
            <span className="text-xs font-bold text-civix-text-main">{relationship.targetName}</span>
          </div>
        </div>

        {/* METADATA */}
        <div className="space-y-3">
          <div>
            <span className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider block mb-0.5">Relationship Type</span>
            <span className="text-xs font-mono text-civix-blue-300 uppercase">{relationship.predicate.replace(/_/g, ' ')}</span>
          </div>

          <div>
            <span className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider block mb-0.5">Status</span>
            {relationship.isModelGenerated ? (
              <span className="inline-flex items-center space-x-1.5 text-[10px] font-bold px-2 py-0.5 rounded-sm bg-civix-gold-950/40 border border-civix-gold-600/40 text-civix-gold-400 uppercase">
                <AlertTriangle className="w-3 h-3" />
                <span>UNRESOLVED</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1.5 text-[10px] font-bold px-2 py-0.5 rounded-sm bg-civix-green-950/40 border border-civix-green-600/40 text-civix-green-400 uppercase">
                <ShieldCheck className="w-3 h-3" />
                <span>{relationship.status || 'AUTHORITATIVE GRAPH RECORD'}</span>
              </span>
            )}
          </div>

          {relationship.isModelGenerated && relationship.modelScore !== undefined && (
            <div>
              <span className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider block mb-0.5">Model Score</span>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold text-civix-gold font-mono">{relationship.modelScore}%</span>
                <div className="flex-1 h-1.5 bg-civix-surface-2 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-civix-gold" 
                    style={{ width: `${relationship.modelScore}%` }}
                  />
                </div>
              </div>
            </div>
          )}

          {relationship.explanation && (
            <div>
              <span className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider block mb-1">
                {relationship.isModelGenerated ? 'Why Surfaced' : 'Provenance'}
              </span>
              <p className="text-xs text-civix-text-secondary leading-relaxed bg-civix-surface-3 p-2 rounded-sm border border-civix-border-subtle">
                {relationship.explanation}
              </p>
            </div>
          )}
        </div>

        {/* DISCLAIMER FOR ML */}
        {relationship.isModelGenerated && (
          <div className="mt-4 p-3 border border-civix-gold-600/40 bg-civix-gold-950/40 rounded-sm">
            <div className="flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-civix-gold-500 flex-shrink-0 mt-0.5" />
              <p className="text-[10px] text-civix-gold-400 font-bold uppercase tracking-wider leading-relaxed">
                MODEL OUTPUT IS NOT CONFIRMATION. REQUIRES INVESTIGATOR VALIDATION.
              </p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
