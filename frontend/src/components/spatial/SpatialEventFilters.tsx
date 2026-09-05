import React from 'react';
import { Filter, RotateCcw } from 'lucide-react';

interface SpatialEventFiltersProps {
  eventTypeFilter: string;
  epistemicFilter: string;
  onSetEventTypeFilter: (type: string) => void;
  onSetEpistemicFilter: (status: string) => void;
  onClearFilters: () => void;
  filteredCount: number;
  totalCount: number;
  availableEventTypes: string[];
}

export const SpatialEventFilters: React.FC<SpatialEventFiltersProps> = ({
  eventTypeFilter,
  epistemicFilter,
  onSetEventTypeFilter,
  onSetEpistemicFilter,
  onClearFilters,
  filteredCount,
  totalCount,
  availableEventTypes
}) => {
  const isFiltered = eventTypeFilter !== 'ALL' || epistemicFilter !== 'ALL';

  return (
    <div className="civix-panel p-3 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center space-x-1.5 text-civix-text-muted font-bold uppercase text-[10px] tracking-wider mr-1">
          <Filter className="w-3.5 h-3.5 text-civix-blue-400" />
          <span>Filters:</span>
        </div>

        {/* Event Type Filter */}
        <select
          value={eventTypeFilter}
          onChange={(e) => onSetEventTypeFilter(e.target.value)}
          className="civix-input py-1 px-2.5 text-xs font-semibold"
        >
          <option value="ALL">All Event Types</option>
          {availableEventTypes.map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>

        {/* Epistemic Status Filter */}
        <select
          value={epistemicFilter}
          onChange={(e) => onSetEpistemicFilter(e.target.value)}
          className="civix-input py-1 px-2.5 text-xs font-semibold"
        >
          <option value="ALL">All Epistemic Statuses</option>
          <option value="CONFIRMED">CONFIRMED</option>
          <option value="PROBABLE">PROBABLE</option>
          <option value="POSSIBLE">POSSIBLE</option>
          <option value="REFUTED">REFUTED</option>
        </select>

        {/* Clear Filters Button */}
        {isFiltered && (
          <button
            onClick={onClearFilters}
            className="civix-btn-secondary py-1 text-[11px]"
          >
            <RotateCcw className="w-3 h-3 text-civix-text-muted" />
            <span>Clear Filters</span>
          </button>
        )}
      </div>

      {/* Dynamic Count Indicator */}
      <div className="font-mono text-xs text-civix-text-muted">
        Showing <span className="font-bold text-civix-text-main">{filteredCount}</span> of <span className="font-bold text-civix-text-main">{totalCount}</span> spatial events
      </div>
    </div>
  );
};
