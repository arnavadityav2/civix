import React, { useMemo, useRef, useEffect } from 'react';
import type { SpatialEventFeature, EpistemicStatus, LocationPredicate } from '../../api/spatial';
import { Clock } from 'lucide-react';

interface EventTimelineScrubberProps {
  events: SpatialEventFeature[];
  selectedEventId: string | null;
  onSelectEvent: (eventId: string) => void;
}

const getPredicateLabel = (pred: LocationPredicate): string => {
  switch (pred) {
    case 'PINGED_TOWER': return 'Cell Tower Ping';
    case 'SEEN_AT': return 'Seen At';
    case 'PRESENT_AT': return 'Present At';
    case 'RESIDED_AT': return 'Resided At';
    case 'VISITED': return 'Visited';
    case 'ALIBI_CONFIRMED_AT': return 'Alibi Confirmed At';
    case 'REGISTERED_AT': return 'Registered At';
    case 'LOCATED_AT':
    default: return 'Located At';
  }
};

const getEpistemicStyle = (status: EpistemicStatus) => {
  switch (status) {
    case 'CONFIRMED':
      return { bg: 'bg-civix-green-950 text-civix-green-400 border-civix-green-600/50', dot: 'bg-civix-green-400 ring-civix-green-900' };
    case 'PROBABLE':
      return { bg: 'bg-civix-gold-950 text-civix-gold-400 border-civix-gold-600/50', dot: 'bg-civix-gold-400 ring-civix-gold-900' };
    case 'POSSIBLE':
      return { bg: 'bg-civix-surface-2 text-civix-text-secondary border-civix-border', dot: 'bg-civix-text-muted ring-civix-surface-2' };
    case 'REFUTED':
      return { bg: 'bg-civix-red-950 text-civix-red-400 border-civix-red-600/50 line-through', dot: 'bg-civix-red-400 ring-civix-red-900' };
    case 'INCONCLUSIVE':
    default:
      return { bg: 'bg-civix-surface-2 text-civix-text-muted border-civix-border', dot: 'bg-civix-text-muted ring-civix-surface-2' };
  }
};

export const EventTimelineScrubber: React.FC<EventTimelineScrubberProps> = ({
  events,
  selectedEventId,
  onSelectEvent
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const selectedNodeRef = useRef<HTMLDivElement>(null);

  // Chronological sorting by event_start ascending
  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => {
      const timeA = new Date(a.properties.event_start).getTime() || 0;
      const timeB = new Date(b.properties.event_start).getTime() || 0;
      if (timeA !== timeB) return timeA - timeB;
      return a.properties.event_location_id.localeCompare(b.properties.event_location_id);
    });
  }, [events]);

  // Auto-scroll timeline to selected event
  useEffect(() => {
    if (selectedNodeRef.current && containerRef.current) {
      selectedNodeRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'center'
      });
    }
  }, [selectedEventId]);

  if (sortedEvents.length === 0) {
    return (
      <div className="civix-panel p-4 text-center text-xs text-civix-text-muted">
        No chronological spatial events available for timeline display.
      </div>
    );
  }

  const formatTimeOnly = (isoStr: string) => {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) + ' UTC';
    } catch {
      return isoStr;
    }
  };

  const formatDateShort = (isoStr: string) => {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' });
    } catch {
      return '';
    }
  };

  return (
    <div className="civix-panel p-3.5 space-y-3 font-sans">
      <div className="flex items-center justify-between border-b border-civix-border pb-2">
        <div className="flex items-center space-x-1.5">
          <Clock className="w-3.5 h-3.5 text-civix-blue-400" />
          <h3 className="civix-panel-title">
            CHRONOLOGICAL EVENT TIMELINE SCRUBBER ({sortedEvents.length})
          </h3>
        </div>
        <span className="text-[10px] text-civix-text-muted font-mono">
          Select an event node to focus map & inspector
        </span>
      </div>

      {/* Horizontal Scrubber Container */}
      <div
        ref={containerRef}
        className="overflow-x-auto pb-2 pt-1 flex items-start space-x-4"
      >
        {sortedEvents.map((evt) => {
          const props = evt.properties;
          const isSelected = props.event_location_id === selectedEventId;
          const epistemic = getEpistemicStyle(props.epistemic_status);
          const predLabel = getPredicateLabel(props.location_predicate);

          return (
            <div
              key={props.event_location_id}
              ref={isSelected ? selectedNodeRef : null}
              onClick={() => onSelectEvent(props.event_location_id)}
              className={`flex-shrink-0 w-56 p-2.5 rounded-sm border transition-all cursor-pointer relative ${
                isSelected
                  ? 'bg-civix-blue-950/80 border-civix-blue-500 shadow-md ring-1 ring-civix-blue-500/30'
                  : 'bg-civix-surface hover:bg-civix-surface-2 border-civix-border'
              }`}
            >
              {/* Timeline Connector Bar */}
              <div className="flex items-center space-x-2 mb-1.5">
                <span className={`w-2.5 h-2.5 rounded-full ${epistemic.dot} ring-2 flex-shrink-0`} />
                <span className="font-mono text-[10px] font-bold text-civix-text-secondary">
                  {formatTimeOnly(props.event_start)}
                </span>
                <span className="text-[9px] text-civix-text-muted font-mono">
                  {formatDateShort(props.event_start)}
                </span>
              </div>

              {/* Event Title & Type */}
              <div className="mb-1.5">
                <span className="text-[9px] font-mono font-bold uppercase text-civix-text-muted block leading-tight">
                  {props.event_type}
                </span>
                <h4 className="text-xs font-bold text-civix-text-main leading-tight truncate" title={props.location_name}>
                  {props.location_name}
                </h4>
              </div>

              {/* Predicate & Epistemic Badges */}
              <div className="flex flex-wrap items-center gap-1 text-[9px]">
                <span className="bg-civix-surface-2 text-civix-text-secondary px-1.5 py-0.5 rounded-sm border border-civix-border font-semibold truncate max-w-[120px]">
                  {predLabel}
                </span>
                <span className={`px-1.5 py-0.5 rounded-sm border font-bold uppercase ${epistemic.bg}`}>
                  {props.epistemic_status}
                </span>
              </div>

              {/* Open ended indicator */}
              {props.is_open_ended && (
                <span className="mt-1 inline-block text-[8px] font-bold uppercase bg-civix-gold-950 text-civix-gold-400 px-1 rounded-sm border border-civix-gold-600/40">
                  Open Ended
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
