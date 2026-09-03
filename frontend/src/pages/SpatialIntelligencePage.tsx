import React, { useState, useEffect, useMemo } from 'react';
import { spatialApi } from '../api/spatial';
import type { 
  SpatialCaseFeature, 
  SpatialCaseCollection, 
  SpatialEventFeature, 
  SpatialEventCollection 
} from '../api/spatial';
import { NCRInvestigationMap } from '../components/spatial/NCRInvestigationMap';
import { CaseSummaryPanel } from '../components/spatial/CaseSummaryPanel';
import { SpatialLayerControl } from '../components/spatial/SpatialLayerControl';
import { MapControlsPanel } from '../components/spatial/MapControlsPanel';
import { CaseEventMap } from '../components/spatial/CaseEventMap';
import { EventInspectorDrawer } from '../components/spatial/EventInspectorDrawer';
import { EventTimelineScrubber } from '../components/spatial/EventTimelineScrubber';
import { SpatialEventFilters } from '../components/spatial/SpatialEventFilters';
import { 
  Filter, 
  Calendar, 
  RefreshCw, 
  Copy, 
  ArrowRight, 
  ArrowLeft,
  Check, 
  AlertTriangle,
  Scale,
  Shield,
  Briefcase,
  AlertCircle,
  MapPin,
  Layers
} from 'lucide-react';

export const SpatialIntelligencePage: React.FC = () => {
  // Mode & Cases State
  const [viewMode, setViewMode] = useState<'GLOBAL_MAP' | 'CASE_EVENT_MAP'>('GLOBAL_MAP');
  const [cases, setCases] = useState<SpatialCaseFeature[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Case Event Map State
  const [activeCaseEvents, setActiveCaseEvents] = useState<SpatialEventFeature[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [isEventsLoading, setIsEventsLoading] = useState<boolean>(false);
  const [eventsError, setEventsError] = useState<string | null>(null);

  // Case Event Filters
  const [eventTypeFilter, setEventTypeFilter] = useState<string>('ALL');
  const [epistemicFilter, setEpistemicFilter] = useState<string>('ALL');

  // Global Filters
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');

  // Layer Controls
  const [layers, setLayers] = useState({
    footprints: true,
    eventLocations: false,
    routes: false,
    heatmap: false
  });

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data: SpatialCaseCollection = await spatialApi.getSpatialCases({ limit: 100 });
      setCases(data.features || []);
      if (data.features?.length > 0 && !selectedCaseId) {
        setSelectedCaseId(data.features[0].properties.case_id);
      }
    } catch (err: any) {
      console.error('Failed to fetch spatial cases:', err);
      setError(err.response?.data?.detail || 'Failed to load spatial cases from backend.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCaseEvents = async (caseId: string) => {
    setIsEventsLoading(true);
    setEventsError(null);
    setActiveCaseEvents([]);
    setSelectedEventId(null);
    setEventTypeFilter('ALL');
    setEpistemicFilter('ALL');

    try {
      const data: SpatialEventCollection = await spatialApi.getSpatialCaseEvents(caseId);
      const eventsList = data.features || [];
      setActiveCaseEvents(eventsList);
      if (eventsList.length > 0) {
        setSelectedEventId(eventsList[0].properties.event_location_id);
      }
    } catch (err: any) {
      console.error('Failed to fetch case events:', err);
      setEventsError(
        err.response?.status === 404
          ? 'No spatial events are currently available for this case or access is denied.'
          : err.response?.data?.detail || 'Failed to load spatial events for selected case.'
      );
    } finally {
      setIsEventsLoading(false);
    }
  };

  const filteredCases = useMemo(() => {
    return cases.filter(c => {
      if (statusFilter !== 'ALL' && c.properties.status !== statusFilter) return false;
      if (priorityFilter !== 'ALL' && c.properties.priority !== priorityFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const title = (c.properties.title || '').toLowerCase();
        const num = (c.properties.case_number || '').toLowerCase();
        const id = (c.properties.case_id || '').toLowerCase();
        if (!title.includes(q) && !num.includes(q) && !id.includes(q)) return false;
      }
      return true;
    });
  }, [cases, statusFilter, priorityFilter, searchQuery]);

  const filteredCaseEvents = useMemo(() => {
    return activeCaseEvents.filter(e => {
      if (eventTypeFilter !== 'ALL' && e.properties.event_type !== eventTypeFilter) return false;
      if (epistemicFilter !== 'ALL' && e.properties.epistemic_status !== epistemicFilter) return false;
      return true;
    });
  }, [activeCaseEvents, eventTypeFilter, epistemicFilter]);

  const availableEventTypes = useMemo(() => {
    const types = new Set<string>();
    activeCaseEvents.forEach(e => {
      if (e.properties.event_type) types.add(e.properties.event_type);
    });
    return Array.from(types);
  }, [activeCaseEvents]);

  const selectedCase = useMemo(() => {
    return cases.find(c => c.properties.case_id === selectedCaseId) || null;
  }, [cases, selectedCaseId]);

  const selectedEvent = useMemo(() => {
    return filteredCaseEvents.find(e => e.properties.event_location_id === selectedEventId) || null;
  }, [filteredCaseEvents, selectedEventId]);

  const handleCopyCaseId = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(id);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleOpenEventMap = (caseId: string) => {
    setSelectedCaseId(caseId);
    setViewMode('CASE_EVENT_MAP');
    fetchCaseEvents(caseId);
  };

  const handleBackToGlobalMap = () => {
    setViewMode('GLOBAL_MAP');
  };

  const handleToggleLayer = (key: 'footprints' | 'eventLocations' | 'routes' | 'heatmap') => {
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleResetLayers = () => {
    setLayers({ footprints: true, eventLocations: false, routes: false, heatmap: false });
  };

  const handleFitViewport = () => {
    setSelectedCaseId(null);
  };

  const handleClearCaseFilters = () => {
    setEventTypeFilter('ALL');
    setEpistemicFilter('ALL');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans p-4 sm:p-6 space-y-5">
      {/* Top Header Controls Bar */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white border border-slate-200 rounded p-4 shadow-2xs">
        <div>
          {viewMode === 'CASE_EVENT_MAP' ? (
            <div className="space-y-1">
              <button
                onClick={handleBackToGlobalMap}
                className="inline-flex items-center space-x-1.5 text-xs font-bold text-[#1a3a6c] hover:text-[#132c54] bg-blue-50 hover:bg-blue-100 border border-blue-200 px-2.5 py-1 rounded transition-colors mb-1 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back to Global Map</span>
              </button>
              <h1 className="text-xl font-bold text-[#1a3a6c] tracking-tight uppercase flex items-center space-x-2">
                <span>CASE EVENT MAP: {selectedCase?.properties.title || 'Investigative Case'}</span>
              </h1>
              <p className="text-slate-500 text-xs">
                Spatial event chronology and evidence
              </p>
            </div>
          ) : (
            <div>
              <h1 className="text-xl font-bold text-[#1a3a6c] tracking-tight uppercase">
                SPATIAL INTELLIGENCE
              </h1>
              <p className="text-slate-500 text-xs mt-0.5">
                Delhi NCR Operational Map & Case Intelligence Overview
              </p>
            </div>
          )}
        </div>

        {/* Header Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {viewMode === 'CASE_EVENT_MAP' && (
            <div className="flex items-center space-x-2">
              <span className="text-[10px] uppercase font-bold text-slate-400">Select Case:</span>
              <select
                value={selectedCaseId || ''}
                onChange={(e) => handleOpenEventMap(e.target.value)}
                className="bg-white border border-slate-300 text-slate-800 text-xs font-semibold rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#1a3a6c] shadow-2xs cursor-pointer max-w-xs truncate"
              >
                {cases.map((c) => (
                  <option key={c.properties.case_id} value={c.properties.case_id}>
                    {c.properties.case_number} - {c.properties.title}
                  </option>
                ))}
              </select>
            </div>
          )}
          {viewMode === 'GLOBAL_MAP' && (
            <>
              {/* Search Box */}
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search FIR, title, case ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-white border border-slate-300 text-slate-800 text-xs font-semibold rounded pl-7 pr-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#1a3a6c] shadow-2xs w-48 focus:w-60 transition-all"
                />
                <Filter className="w-3.5 h-3.5 text-slate-400 absolute left-2 top-2" />
              </div>
              {/* Case Scope Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-white border border-slate-300 text-slate-800 text-xs font-semibold rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#1a3a6c] shadow-2xs cursor-pointer"
              >
                <option value="ALL">All Cases</option>
              </select>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-white border border-slate-300 text-slate-800 text-xs font-semibold rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#1a3a6c] shadow-2xs cursor-pointer"
              >
                <option value="ALL">All Status</option>
                <option value="OPEN">Open</option>
                <option value="UNDER_INVESTIGATION">Under Investigation</option>
                <option value="CLOSED_SOLVED">Closed Solved</option>
              </select>

              {/* Priority Filter */}
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="bg-white border border-slate-300 text-slate-800 text-xs font-semibold rounded px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#1a3a6c] shadow-2xs cursor-pointer"
              >
                <option value="ALL">All Priorities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>

              <button className="flex items-center space-x-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-xs font-semibold px-3 py-1.5 rounded shadow-2xs transition-colors cursor-pointer">
                <Filter className="w-3.5 h-3.5 text-slate-500" />
                <span>Filters</span>
              </button>
            </>
          )}

          <button 
            onClick={fetchCases}
            disabled={isLoading}
            className="flex items-center space-x-1.5 bg-[#1a3a6c] hover:bg-[#132c54] text-white text-xs font-semibold px-3 py-1.5 rounded shadow-2xs transition-colors cursor-pointer"
          >
            <Calendar className="w-3.5 h-3.5 text-amber-400" />
            <span>View Timeline</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span>{error}</span>
          </div>
          <button 
            onClick={fetchCases}
            className="bg-red-100 hover:bg-red-200 text-red-800 px-2 py-1 rounded font-semibold text-[11px]"
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Workspace Split Screen Grid */}
      {viewMode === 'GLOBAL_MAP' ? (
        /* MODE A: GLOBAL SPATIAL INTELLIGENCE VIEW */
        <>
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-stretch">
            {/* Left Column (8 cols): NCR Interactive Map */}
            <div className="xl:col-span-8 bg-white border border-slate-200 rounded p-3 shadow-2xs flex flex-col h-[560px]">
              <div className="flex-1 w-full h-full min-h-0">
                {isLoading ? (
                  <div className="w-full h-full bg-slate-100 rounded border border-slate-200 flex flex-col items-center justify-center text-slate-400 text-xs animate-pulse">
                    <RefreshCw className="w-6 h-6 animate-spin text-slate-400 mb-2" />
                    <span>Loading Delhi NCR Spatial Case Footprints...</span>
                  </div>
                ) : (
                  <NCRInvestigationMap
                    cases={filteredCases}
                    selectedCaseId={selectedCaseId}
                    onSelectCase={setSelectedCaseId}
                  />
                )}
              </div>
            </div>

            {/* Right Column (4 cols): Inspector & Controls */}
            <div className="xl:col-span-4 flex flex-col space-y-3.5">
              {/* Case Summary Card */}
              <CaseSummaryPanel
                selectedCase={selectedCase}
                onOpenEventMap={handleOpenEventMap}
              />

              {/* Spatial Layers Card */}
              <SpatialLayerControl
                layers={layers}
                onToggleLayer={handleToggleLayer}
                hasSelectedCase={!!selectedCase}
              />

              {/* Map Controls Card */}
              <MapControlsPanel
                onFitViewport={handleFitViewport}
                onResetLayers={handleResetLayers}
                onExportView={() => alert('Map View Export triggered.')}
              />
            </div>
          </div>

          {/* Bottom Section: Active Cases Table */}
          <div className="bg-white border border-slate-200 rounded shadow-2xs p-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
              <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                ACTIVE CASES IN VIEWPORT ({filteredCases.length})
              </h2>
              <span className="text-[11px] font-mono text-slate-400">Showing top case footprints</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                    <th className="py-2.5 px-3">CASE ID</th>
                    <th className="py-2.5 px-3">TITLE / SUBJECT</th>
                    <th className="py-2.5 px-3">STATUS</th>
                    <th className="py-2.5 px-3">PRIORITY</th>
                    <th className="py-2.5 px-3">CASE TYPE</th>
                    <th className="py-2.5 px-3">LAST ACTIVITY</th>
                    <th className="py-2.5 px-3 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700 font-sans">
                  {filteredCases.map((feat) => {
                    const { case_id, title, status, priority, case_type } = feat.properties;
                    const isSelected = case_id === selectedCaseId;

                    return (
                      <tr
                        key={case_id}
                        onClick={() => setSelectedCaseId(case_id)}
                        className={`hover:bg-blue-50/60 transition-colors cursor-pointer ${
                          isSelected ? 'bg-blue-50/80 font-medium' : ''
                        }`}
                      >
                        <td className="py-2.5 px-3 font-mono text-[11px]">
                          <div className="flex items-center space-x-1.5 text-slate-500">
                            <span>{case_id.slice(0, 8)}...</span>
                            <button
                              onClick={(e) => handleCopyCaseId(case_id, e)}
                              className="text-slate-400 hover:text-slate-700 transition-colors"
                              title="Copy Case ID"
                            >
                              {copiedId === case_id ? (
                                <Check className="w-3 h-3 text-emerald-600" />
                              ) : (
                                <Copy className="w-3 h-3" />
                              )}
                            </button>
                          </div>
                        </td>

                        <td className="py-2.5 px-3 font-semibold text-slate-900">
                          {title}
                        </td>

                        <td className="py-2.5 px-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-50 text-blue-800 border border-blue-200">
                            {status}
                          </span>
                        </td>

                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            priority === 'CRITICAL' ? 'bg-red-50 text-red-700 border border-red-200' :
                            priority === 'HIGH' ? 'bg-orange-50 text-orange-700 border border-orange-200' :
                            'bg-amber-50 text-amber-700 border border-amber-200'
                          }`}>
                            {priority}
                          </span>
                        </td>

                        <td className="py-2.5 px-3 text-slate-600">
                          <div className="flex items-center space-x-1">
                            {case_type.includes('FINANCIAL') || case_type.includes('FRAUD') ? <Scale className="w-3 h-3 text-slate-400" /> :
                             case_type === 'CRIMINAL' || case_type === 'ORGANIZED_CRIME' ? <Shield className="w-3 h-3 text-slate-400" /> :
                             case_type === 'INTELLIGENCE' ? <AlertCircle className="w-3 h-3 text-slate-400" /> :
                             <Briefcase className="w-3 h-3 text-slate-400" />}
                            <span>{case_type}</span>
                          </div>
                        </td>

                        <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">
                          Recent
                        </td>

                        <td className="py-2.5 px-3 text-right">
                          <ArrowRight className="w-4 h-4 text-slate-400 inline-block" />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="mt-3 pt-3 border-t border-slate-100 text-center">
              <button 
                onClick={() => alert('Viewing all 250 cases.')}
                className="text-xs font-bold text-[#1a3a6c] hover:underline inline-flex items-center space-x-1"
              >
                <span>View All Cases (250)</span>
                <ArrowRight className="w-3.5 h-3.5 text-amber-500" />
              </button>
            </div>
          </div>
        </>
      ) : (
        /* MODE B: DEDICATED CASE EVENT MAP VIEW WITH TIMELINE SCRUBBER */
        <div className="space-y-4">
          {/* Filter Bar */}
          <SpatialEventFilters
            eventTypeFilter={eventTypeFilter}
            epistemicFilter={epistemicFilter}
            onSetEventTypeFilter={setEventTypeFilter}
            onSetEpistemicFilter={setEpistemicFilter}
            onClearFilters={handleClearCaseFilters}
            filteredCount={filteredCaseEvents.length}
            totalCount={activeCaseEvents.length}
            availableEventTypes={availableEventTypes}
          />

          {/* Split Workspace: Map + Inspector */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-stretch">
            {/* Left Column (8 cols): Case Event Map */}
            <div className="xl:col-span-8 bg-white border border-slate-200 rounded p-3 shadow-2xs flex flex-col h-[520px]">
              <div className="flex-1 w-full h-full min-h-0">
                {isEventsLoading ? (
                  <div className="w-full h-full bg-slate-100 rounded border border-slate-200 flex flex-col items-center justify-center text-slate-400 text-xs animate-pulse">
                    <RefreshCw className="w-6 h-6 animate-spin text-slate-400 mb-2" />
                    <span>Loading Case Spatial Events...</span>
                  </div>
                ) : eventsError ? (
                  <div className="w-full h-full bg-slate-50 rounded border border-slate-200 flex flex-col items-center justify-center p-6 text-center text-slate-500 text-xs">
                    <AlertTriangle className="w-8 h-8 text-amber-600 mb-2" />
                    <h3 className="font-bold text-slate-800 text-sm">NO SPATIAL EVENTS</h3>
                    <p className="max-w-xs mt-1 text-slate-500">{eventsError}</p>
                  </div>
                ) : filteredCaseEvents.length === 0 ? (
                  <div className="w-full h-full bg-slate-50 rounded border border-slate-200 flex flex-col items-center justify-center p-6 text-center text-slate-500 text-xs">
                    <MapPin className="w-8 h-8 text-slate-300 mb-2" />
                    <h3 className="font-bold text-slate-800 text-sm">NO MATCHING SPATIAL EVENTS</h3>
                    <p className="max-w-xs mt-1 text-slate-500">
                      Try adjusting or clearing the active event filters.
                    </p>
                    <button
                      onClick={handleClearCaseFilters}
                      className="mt-3 bg-[#1a3a6c] text-white px-3 py-1.5 rounded text-xs font-semibold"
                    >
                      Clear Filters
                    </button>
                  </div>
                ) : (
                  <CaseEventMap
                    events={filteredCaseEvents}
                    selectedEventId={selectedEventId}
                    onSelectEvent={(evt) => setSelectedEventId(evt.properties.event_location_id)}
                  />
                )}
              </div>
            </div>

            {/* Right Column (4 cols): Event Inspector Drawer */}
            <div className="xl:col-span-4 flex flex-col space-y-3.5">
              {selectedEvent ? (
                <EventInspectorDrawer
                  event={selectedEvent}
                  onClose={() => setSelectedEventId(null)}
                />
              ) : (
                <div className="bg-white border border-slate-200 rounded p-6 shadow-sm flex flex-col items-center justify-center text-center h-[280px]">
                  <Layers className="w-8 h-8 text-slate-300 mb-2" />
                  <h3 className="text-sm font-bold text-slate-800">Select an Event</h3>
                  <p className="text-xs text-slate-500 max-w-xs mt-1">
                    Click an event marker on the map or a node on the timeline scrubber to inspect details, predicates, timestamps, and evidence.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Bottom Section: Chronological Event Timeline Scrubber */}
          <EventTimelineScrubber
            events={filteredCaseEvents}
            selectedEventId={selectedEventId}
            onSelectEvent={(id) => setSelectedEventId(id)}
          />
        </div>
      )}
    </div>
  );
};
