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
        style: 'bg-emerald-50 text-emerald-800 border-emerald-300',
        icon: CheckCircle
      };
    case 'PROBABLE':
      return {
        label: 'PROBABLE',
        style: 'bg-amber-50 text-amber-800 border-amber-300',
        icon: AlertTriangle
      };
    case 'POSSIBLE':
      return {
        label: 'POSSIBLE',
        style: 'bg-slate-100 text-slate-700 border-slate-300',
        icon: Info
      };
    case 'REFUTED':
      return {
        label: 'REFUTED',
        style: 'bg-red-50 text-red-800 border-red-300 line-through',
        icon: Ban
      };
    case 'INCONCLUSIVE':
    default:
      return {
        label: 'INCONCLUSIVE',
        style: 'bg-gray-100 text-gray-700 border-gray-300',
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
    <div className="bg-white border border-slate-200 rounded p-4 shadow-md flex flex-col justify-between space-y-4 font-sans text-xs">
      <div>
        {/* Drawer Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-2.5 mb-3">
          <div className="flex items-center space-x-1.5">
            <Info className="w-4 h-4 text-[#1a3a6c]" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              EVENT DETAILS
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 p-1 rounded hover:bg-slate-100 transition-colors"
            title="Close Inspector"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Primary Event Header */}
        <div className="mb-3.5">
          <span className="text-[10px] font-mono text-slate-400 font-bold uppercase tracking-wider">
            {props.event_type}
          </span>
          <h2 className="text-sm font-bold text-slate-900 leading-tight mt-0.5">
            {props.location_name}
          </h2>
          <span className="text-[11px] text-slate-500 font-mono">
            Type: {props.location_type}
          </span>
        </div>

        {/* Predicate & Epistemic Badges */}
        <div className="grid grid-cols-2 gap-2 mb-4">
          {/* Predicate Badge */}
          <div className="bg-slate-50 rounded border border-slate-200 p-2 flex flex-col justify-between">
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Predicate
            </span>
            <div className="flex items-center space-x-1.5">
              <PredIcon className="w-3.5 h-3.5 text-[#1a3a6c]" />
              <span className="font-semibold text-slate-800 text-[11px]">
                {predLabel}
              </span>
            </div>
          </div>

          {/* Epistemic Status Badge */}
          <div className="bg-slate-50 rounded border border-slate-200 p-2 flex flex-col justify-between">
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">
              Epistemic Status
            </span>
            <div className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded border text-[10px] font-bold ${epistemic.style}`}>
              <EpistemicIcon className="w-3 h-3" />
              <span>{epistemic.label}</span>
            </div>
          </div>
        </div>

        {/* Temporal Bounds */}
        <div className="bg-slate-50 rounded border border-slate-200 p-3 space-y-2 mb-4">
          <div className="flex items-center justify-between border-b border-slate-200/60 pb-1.5">
            <span className="text-[10px] font-bold text-slate-400 uppercase flex items-center">
              <Clock className="w-3 h-3 mr-1 text-slate-400" />
              Start Time
            </span>
            <span className="font-mono text-[11px] font-semibold text-slate-800">
              {formatTimestamp(props.event_start)}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase">
              End Time
            </span>
            <span className="font-mono text-[11px] font-semibold text-slate-800">
              {props.is_open_ended ? (
                <span className="text-amber-700 bg-amber-50 px-1 rounded font-bold text-[10px] border border-amber-200">
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
          <div className="bg-amber-50/80 border border-amber-200 text-amber-800 p-2.5 rounded text-[11px] mb-4 space-y-1">
            <div className="font-bold flex items-center">
              <ShieldAlert className="w-3.5 h-3.5 mr-1 text-amber-600" />
              Telecommunications Signal Safeguard
            </div>
            <p className="text-[10px] text-amber-700 leading-snug">
              This event represents a cell tower coverage ping signal within sector bounds. It does not establish direct physical person presence.
            </p>
          </div>
        )}

        {/* Evidence & Participants References */}
        <div className="space-y-3">
          {/* Source Evidence References */}
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              SOURCE EVIDENCE REFERENCES
            </span>
            {props.source_record_id ? (
              <div className="bg-slate-50 border border-slate-200 rounded p-2 flex items-center justify-between">
                <div className="flex items-center space-x-1.5">
                  <FileText className="w-3.5 h-3.5 text-blue-700" />
                  <span className="font-mono text-[11px] text-slate-700">
                    {props.source_record_id.slice(0, 12)}...
                  </span>
                </div>
                <span className="text-[9px] font-bold bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded border border-blue-200">
                  SOURCE RECORD
                </span>
              </div>
            ) : (
              <div className="text-[11px] text-slate-400 italic bg-slate-50 border border-slate-200/80 p-2 rounded">
                No linked source record ID provided.
              </div>
            )}
          </div>

          {/* Generator / Provenance Version Metadata */}
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
              GENERATION / PROVENANCE
            </span>
            <div className="bg-slate-50 border border-slate-200 rounded p-2 text-[10px] font-mono space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-400">Generator Version:</span>
                <span className="font-semibold text-slate-800">{props.generation_origin || '1.0.0-phase11d'}</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-slate-200/60">
                <span className="text-slate-400">Generation Run ID:</span>
                <span className="text-slate-600">{props.generation_run_id ? `${props.generation_run_id.slice(0, 8)}...` : 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
