import React from 'react';
import type { SpatialEventFeature, LocationPredicate } from '../../api/spatial';
import { 
  X, 
  MapPin, 
  Clock, 
  FileText, 
  ShieldAlert, 
  Info,
  Radio,
  Eye,
  Building,
  CheckCircle,
  AlertTriangle,
  HelpCircle,
  Ban
} from 'lucide-react';

interface EventInspectorDrawerProps {
  event: SpatialEventFeature | null;
  onClose: () => void;
}

const getPredicateLabel = (pred: LocationPredicate): { label: string; icon: React.FC<{ className?: string }> } => {
  switch (pred) {
    case 'PINGED_TOWER':
      return { label: 'Cell Tower Ping', icon: Radio };
    case 'SEEN_AT':
      return { label: 'Seen At', icon: Eye };
    case 'PRESENT_AT':
      return { label: 'Present At', icon: MapPin };
    case 'RESIDED_AT':
      return { label: 'Resided At', icon: Building };
    case 'VISITED':
      return { label: 'Visited', icon: MapPin };
    case 'ALIBI_CONFIRMED_AT':
      return { label: 'Alibi Confirmed At', icon: CheckCircle };
    case 'REGISTERED_AT':
      return { label: 'Registered At', icon: FileText };
    case 'LOCATED_AT':
    default:
      return { label: 'Located At', icon: MapPin };
  }
};

const getEpistemicBadge = (status: string) => {
  switch (status) {
    case 'CONFIRMED':
      return {
        label: 'CONFIRMED',
        style: 'bg-civix-green-950 text-civix-green-400 border-civix-green-600/50',
        icon: CheckCircle
      };
    case 'PROBABLE':
      return {
        label: 'PROBABLE',
        style: 'bg-civix-gold-950 text-civix-gold-400 border-civix-gold-600/50',
        icon: AlertTriangle
      };
    case 'POSSIBLE':
      return {
        label: 'POSSIBLE',
        style: 'bg-civix-surface-2 text-civix-text-secondary border-civix-border',
        icon: Info
      };
    case 'REFUTED':
      return {
        label: 'REFUTED',
        style: 'bg-civix-red-950 text-civix-red-400 border-civix-red-600/50 line-through',
        icon: Ban
      };
    case 'INCONCLUSIVE':
    default:
      return {
        label: 'INCONCLUSIVE',
        style: 'bg-civix-surface-2 text-civix-text-muted border-civix-border',
        icon: HelpCircle
      };
  }
};

export const EventInspectorDrawer: React.FC<EventInspectorDrawerProps> = ({
  event,
  onClose
}) => {
  if (!event) return null;

  const props = event.properties;
  const { label: predLabel, icon: PredIcon } = getPredicateLabel(props.location_predicate);
  const epistemic = getEpistemicBadge(props.epistemic_status);
  const EpistemicIcon = epistemic.icon;

  const formatTimestamp = (tsStr: string) => {
    if (!tsStr) return 'N/A';
    try {
      const d = new Date(tsStr);
      return d.toLocaleString('en-US', {
        dateStyle: 'medium',
        timeStyle: 'medium',
        timeZone: 'UTC'
      }) + ' UTC';
    } catch {
      return tsStr;
    }
  };

  return (
    <div className="civix-panel p-4 flex flex-col justify-between space-y-4 font-sans text-xs">
      <div>
        {/* Drawer Header */}
        <div className="flex items-center justify-between border-b border-civix-border pb-2.5 mb-3">
          <div className="flex items-center space-x-1.5">
            <Info className="w-4 h-4 text-civix-blue-400" />
            <h3 className="civix-panel-title">
              EVENT DETAILS
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-civix-text-muted hover:text-civix-text-main p-1 rounded-sm hover:bg-civix-surface-2 transition-colors"
            title="Close Inspector"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Primary Event Header */}
        <div className="mb-3.5">
          <span className="text-[10px] font-mono text-civix-text-muted font-bold uppercase tracking-wider">
            {props.event_type}
          </span>
          <h2 className="text-sm font-bold text-civix-text-main leading-tight mt-0.5">
            {props.location_name}
          </h2>
          <span className="text-[11px] text-civix-text-muted font-mono">
            Type: {props.location_type}
          </span>
        </div>

        {/* Predicate & Epistemic Badges */}
        <div className="grid grid-cols-2 gap-2 mb-4">
          {/* Predicate Badge */}
          <div className="bg-civix-surface rounded-sm border border-civix-border p-2 flex flex-col justify-between">
            <span className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider mb-1">
              Predicate
            </span>
            <div className="flex items-center space-x-1.5">
              <PredIcon className="w-3.5 h-3.5 text-civix-blue-400" />
              <span className="font-semibold text-civix-text-main text-[11px]">
                {predLabel}
              </span>
            </div>
          </div>

          {/* Epistemic Status Badge */}
          <div className="bg-civix-surface rounded-sm border border-civix-border p-2 flex flex-col justify-between">
            <span className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider mb-1">
              Epistemic Status
            </span>
            <div className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded-sm border text-[10px] font-bold ${epistemic.style}`}>
              <EpistemicIcon className="w-3 h-3" />
              <span>{epistemic.label}</span>
            </div>
          </div>
        </div>

        {/* Temporal Bounds */}
        <div className="bg-civix-surface rounded-sm border border-civix-border p-3 space-y-2 mb-4">
          <div className="flex items-center justify-between border-b border-civix-border/40 pb-1.5">
            <span className="text-[10px] font-bold text-civix-text-muted uppercase flex items-center">
              <Clock className="w-3 h-3 mr-1 text-civix-text-muted" />
              Start Time
            </span>
            <span className="font-mono text-[11px] font-semibold text-civix-text-main">
              {formatTimestamp(props.event_start)}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-civix-text-muted uppercase">
              End Time
            </span>
            <span className="font-mono text-[11px] font-semibold text-civix-text-main">
              {props.is_open_ended ? (
                <span className="text-civix-gold-400 bg-civix-gold-950 px-1 rounded-sm font-bold text-[10px] border border-civix-gold-600/40">
                  OPEN ENDED
                </span>
              ) : (
                formatTimestamp(props.event_end)
              )}
            </span>
          </div>
        </div>

        {/* Telecommunication Signal Semantic Safeguard Warning for PINGED_TOWER */}
        {props.location_predicate === 'PINGED_TOWER' && (
          <div className="bg-civix-gold-950/60 border border-civix-gold-600/40 text-civix-gold-400 p-2.5 rounded-sm text-[11px] mb-4 space-y-1">
            <div className="font-bold flex items-center">
              <ShieldAlert className="w-3.5 h-3.5 mr-1 text-civix-gold-500" />
              Telecommunications Signal Safeguard
            </div>
            <p className="text-[10px] text-civix-text-secondary leading-snug">
              This event represents a cell tower coverage ping signal within sector bounds. It does not establish direct physical person presence.
            </p>
          </div>
        )}

        {/* Evidence & Participants References */}
        <div className="space-y-3">
          {/* Source Evidence References */}
          <div>
            <span className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider block mb-1">
              SOURCE EVIDENCE REFERENCES
            </span>
            {props.source_record_id ? (
              <div className="bg-civix-surface border border-civix-border rounded-sm p-2 flex items-center justify-between">
                <div className="flex items-center space-x-1.5">
                  <FileText className="w-3.5 h-3.5 text-civix-blue-400" />
                  <span className="font-mono text-[11px] text-civix-text-secondary">
                    {props.source_record_id.slice(0, 12)}...
                  </span>
                </div>
                <span className="text-[9px] font-bold bg-civix-blue-950 text-civix-blue-400 px-1.5 py-0.5 rounded-sm border border-civix-blue-600/40">
                  SOURCE RECORD
                </span>
              </div>
            ) : (
              <div className="text-[11px] text-civix-text-muted italic bg-civix-surface border border-civix-border p-2 rounded-sm">
                No linked source record ID provided.
              </div>
            )}
          </div>

          {/* Generator / Provenance Version Metadata */}
          <div>
            <span className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider block mb-1">
              GENERATION / PROVENANCE
            </span>
            <div className="bg-civix-surface border border-civix-border rounded-sm p-2 text-[10px] font-mono space-y-1">
              <div className="flex justify-between">
                <span className="text-civix-text-muted">Generator Version:</span>
                <span className="font-semibold text-civix-text-main">{props.generation_origin || '1.0.0-phase11d'}</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-civix-border/40">
                <span className="text-civix-text-muted">Generation Run ID:</span>
                <span className="text-civix-text-secondary">{props.generation_run_id ? `${props.generation_run_id.slice(0, 8)}...` : 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
