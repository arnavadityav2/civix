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
    <div className="bg-white border border-slate-200 rounded p-3 shadow-2xs flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs font-sans">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center space-x-1.5 text-slate-500 font-bold uppercase text-[10px] tracking-wider mr-1">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span>Filters:</span>
        </div>

        {/* Event Type Filter */}
        <select
          value={eventTypeFilter}
          onChange={(e) => onSetEventTypeFilter(e.target.value)}
          className="bg-white border border-slate-300 text-slate-800 text-xs font-semibold rounded px-2.5 py-1 focus:outline-none focus:ring-1 focus:ring-[#1a3a6c] shadow-2xs cursor-pointer"
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
          className="bg-white border border-slate-300 text-slate-800 text-xs font-semibold rounded px-2.5 py-1 focus:outline-none focus:ring-1 focus:ring-[#1a3a6c] shadow-2xs cursor-pointer"
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
            className="inline-flex items-center space-x-1 text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-2 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3 h-3 text-slate-500" />
            <span>Clear Filters</span>
          </button>
        )}
      </div>

      {/* Dynamic Count Indicator */}
      <div className="font-mono text-xs text-slate-600">
        Showing <span className="font-bold text-slate-900">{filteredCount}</span> of <span className="font-bold text-slate-900">{totalCount}</span> spatial events
      </div>
    </div>
  );
};
