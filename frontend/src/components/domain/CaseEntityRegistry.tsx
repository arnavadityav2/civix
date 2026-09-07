import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  Car,
  Phone,
  Building2,
  Smartphone,
  Shield,
  Search,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import { casesApi } from '../../api/cases';
import { EntityAvatar } from './EntityAvatar';
import type { CaseEntityRoleListItem, EntityCounts } from '../../types/api';

// ─────────────────────────────────────────────────────────────────────────────
// Sub-tab definition
// ─────────────────────────────────────────────────────────────────────────────
type EntitySubTab = 'ALL' | 'PERSON' | 'VEHICLE' | 'PHONE_NUMBER' | 'ORGANIZATION' | 'DEVICE';

interface SubTabConfig {
  id: EntitySubTab;
  label: string;
  shortLabel: string;
  icon: React.ElementType;
  countKey: keyof EntityCounts | null;
  accentColor: string;
  badgeClass: string;
}

const SUB_TABS: SubTabConfig[] = [
  {
    id: 'ALL',
    label: 'All Entities',
    shortLabel: 'All',
    icon: Shield,
    countKey: null,
    accentColor: 'text-slate-300',
    badgeClass: 'bg-slate-800 text-slate-300 border-slate-700',
  },
  {
    id: 'PERSON',
    label: 'People',
    shortLabel: 'People',
    icon: Users,
    countKey: 'person_count',
    accentColor: 'text-cyan-400',
    badgeClass: 'bg-cyan-950/60 text-cyan-300 border-cyan-800/50',
  },
  {
    id: 'VEHICLE',
    label: 'Vehicles',
    shortLabel: 'Vehicles',
    icon: Car,
    countKey: 'vehicle_count',
    accentColor: 'text-emerald-400',
    badgeClass: 'bg-emerald-950/60 text-emerald-300 border-emerald-800/50',
  },
  {
    id: 'PHONE_NUMBER',
    label: 'Phone Numbers',
    shortLabel: 'Phones',
    icon: Phone,
    countKey: 'phone_count',
    accentColor: 'text-purple-400',
    badgeClass: 'bg-purple-950/60 text-purple-300 border-purple-800/50',
  },
  {
    id: 'ORGANIZATION',
    label: 'Organizations',
    shortLabel: 'Orgs',
    icon: Building2,
    countKey: 'organization_count',
    accentColor: 'text-amber-400',
    badgeClass: 'bg-amber-950/60 text-amber-300 border-amber-800/50',
  },
  {
    id: 'DEVICE',
    label: 'Devices',
    shortLabel: 'Devices',
    icon: Smartphone,
    countKey: 'device_count',
    accentColor: 'text-blue-400',
    badgeClass: 'bg-blue-950/60 text-blue-300 border-blue-800/50',
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// Role badge styling
// ─────────────────────────────────────────────────────────────────────────────
const OFFICER_ROLES = ['OFFICER_IN_CHARGE', 'INVESTIGATING_OFFICER', 'SUPERVISING_OFFICER'];

const getRoleBadgeClass = (role: string): string => {
  if (OFFICER_ROLES.includes(role))
    return 'bg-blue-950/70 text-cyan-300 border-blue-800/50';
  switch (role) {
    case 'SUSPECT':
    case 'ACCUSED':
      return 'bg-red-950/70 text-red-300 border-red-800/50';
    case 'VICTIM':
      return 'bg-orange-950/70 text-orange-300 border-orange-800/50';
    case 'WITNESS':
      return 'bg-yellow-950/70 text-yellow-300 border-yellow-800/50';
    case 'COMPLAINANT':
      return 'bg-slate-800/70 text-slate-300 border-slate-700/50';
    default:
      return 'bg-slate-800/70 text-slate-400 border-slate-700/50';
  }
};

// ─────────────────────────────────────────────────────────────────────────────
// Person card (grid display for PERSON entities)
// ─────────────────────────────────────────────────────────────────────────────
interface PersonCardProps {
  entity: CaseEntityRoleListItem;
  onClick: () => void;
}

const PersonCard: React.FC<PersonCardProps> = ({ entity, onClick }) => {
  const isOfficer = OFFICER_ROLES.includes(entity.role);

  return (
    <div
      onClick={onClick}
      className="bg-[#070A0F] border border-[#1E293B] hover:border-cyan-500/40 rounded overflow-hidden cursor-pointer transition-all group flex flex-col"
    >
      {/* Mugshot area */}
      <div className="relative h-32 bg-[#0F172A] flex items-center justify-center border-b border-[#1E293B] overflow-hidden">
        <EntityAvatar
          entityType="PERSON"
          avatarUrl={entity.avatar_url}
          name={entity.display_name}
          size="2xl"
          className="group-hover:scale-105 transition-transform duration-300"
        />
        {/* Officer flag */}
        {isOfficer && (
          <div className="absolute top-1.5 right-1.5 bg-blue-950/90 text-cyan-300 border border-blue-800/60 text-[8px] font-mono font-bold px-1.5 py-0.5 rounded">
            POLICE
          </div>
        )}
        {/* Entity ID chip bottom-left */}
        <div className="absolute bottom-1 left-1 bg-[#050810]/80 text-[8px] font-mono text-slate-500 px-1 py-0.5 rounded">
          {entity.entity_id.split('-')[0]}
        </div>
      </div>

      {/* Info area */}
      <div className="p-2.5 flex flex-col gap-1 flex-1">
        <h3
          className="text-xs font-bold text-white font-sans truncate leading-tight"
          title={entity.display_name}
        >
          {entity.display_name}
        </h3>
        <span
          className={`text-[9px] font-mono font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded border w-fit ${getRoleBadgeClass(entity.role)}`}
        >
          {entity.role.replace(/_/g, ' ')}
        </span>
        {entity.gender && (
          <span className="text-[9px] font-mono text-slate-500 uppercase">
            {entity.gender}
          </span>
        )}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────────────
// Table row (compact list display for PHONE_NUMBER, VEHICLE, ORG, DEVICE)
// ─────────────────────────────────────────────────────────────────────────────
interface EntityRowProps {
  entity: CaseEntityRoleListItem;
  onClick: () => void;
}

const EntityRow: React.FC<EntityRowProps> = ({ entity, onClick }) => (
  <div
    className="flex items-center px-4 py-2.5 border-b border-[#1E293B]/60 hover:bg-[#0A0F1A] transition-colors group cursor-pointer"
    onClick={onClick}
  >
    {/* Avatar icon */}
    <div className="flex-shrink-0 mr-3">
      <EntityAvatar
        entityType={entity.entity_type}
        avatarUrl={entity.avatar_url}
        name={entity.display_name}
        size="sm"
      />
    </div>

    {/* Main content */}
    <div className="flex-1 min-w-0 flex items-center gap-3">
      <span className="text-xs font-mono text-white truncate flex-1" title={entity.display_name}>
        {entity.display_name}
      </span>
      <span className="text-[9px] font-mono text-slate-500 hidden sm:block truncate w-20" title={entity.entity_id}>
        {entity.entity_id.split('-')[0]}
      </span>
      <span
        className={`text-[9px] font-mono font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded border flex-shrink-0 ${getRoleBadgeClass(entity.role)}`}
      >
        {entity.role.replace(/_/g, ' ')}
      </span>
    </div>

    {/* Action */}
    <button
      onClick={(e) => { e.stopPropagation(); onClick(); }}
      className="ml-3 flex-shrink-0 opacity-0 group-hover:opacity-100 flex items-center gap-1 text-[9px] font-mono text-cyan-400 hover:text-cyan-300 transition-all"
    >
      <span>Dossier</span>
      <ChevronRight className="w-3 h-3" />
    </button>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Pagination controls
// ─────────────────────────────────────────────────────────────────────────────
interface PaginationProps {
  page: number;
  totalPages: number;
  totalCount: number;
  pageSize: number;
  onPrev: () => void;
  onNext: () => void;
}

const Pagination: React.FC<PaginationProps> = ({
  page, totalPages, totalCount, pageSize, onPrev, onNext,
}) => (
  <div className="flex items-center justify-between px-4 py-2.5 border-t border-[#1E293B] bg-[#080B12] text-xs font-mono text-slate-400 flex-shrink-0">
    <span>
      Showing{' '}
      <span className="text-white font-bold">{(page - 1) * pageSize + 1}</span>–
      <span className="text-white font-bold">{Math.min(page * pageSize, totalCount)}</span>
      {' '}of{' '}
      <span className="text-white font-bold">{totalCount.toLocaleString()}</span>
    </span>
    <div className="flex items-center gap-1.5">
      <button
        onClick={onPrev}
        disabled={page === 1}
        className="p-1 rounded border border-[#1E293B] bg-[#0C1220] hover:bg-[#111827] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronLeft className="w-3.5 h-3.5" />
      </button>
      <span className="text-white font-bold px-1.5">
        {page} / {totalPages}
      </span>
      <button
        onClick={onNext}
        disabled={page === totalPages}
        className="p-1 rounded border border-[#1E293B] bg-[#0C1220] hover:bg-[#111827] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
      >
        <ChevronRight className="w-3.5 h-3.5" />
      </button>
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────────────────────────
// Main CaseEntityRegistry component
// ─────────────────────────────────────────────────────────────────────────────
interface CaseEntityRegistryProps {
  caseId: string;
}

const PAGE_SIZE = 50;

export const CaseEntityRegistry: React.FC<CaseEntityRegistryProps> = ({ caseId }) => {
  const navigate = useNavigate();
  const [activeSubTab, setActiveSubTab] = useState<EntitySubTab>('ALL');
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');

  // API query — server-side filtered + paginated
  const { data, isLoading, isError } = useQuery({
    queryKey: ['case-entity-registry', caseId, activeSubTab, page, PAGE_SIZE],
    queryFn: () =>
      casesApi.getCaseEntities(caseId, {
        entity_type: activeSubTab === 'ALL' ? undefined : activeSubTab,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      }),
    enabled: !!caseId,
    staleTime: 15_000,
  });

  const items: CaseEntityRoleListItem[] = data?.items || [];
  const totalCount: number = data?.total_count || 0;
  const entityCounts: EntityCounts | undefined = data?.entity_counts;

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  // Client-side search filter on current page results only
  const filteredItems = useMemo(() => {
    if (!searchTerm.trim()) return items;
    const term = searchTerm.toLowerCase();
    return items.filter(
      (e) =>
        e.display_name.toLowerCase().includes(term) ||
        e.entity_id.toLowerCase().includes(term) ||
        e.role.toLowerCase().includes(term) ||
        e.entity_type.toLowerCase().includes(term)
    );
  }, [items, searchTerm]);

  // Total count for the "ALL" tab badge
  const allCount = entityCounts
    ? (entityCounts.person_count || 0) +
      (entityCounts.vehicle_count || 0) +
      (entityCounts.phone_count || 0) +
      (entityCounts.organization_count || 0) +
      (entityCounts.device_count || 0)
    : totalCount;

  const getTabCount = (tab: SubTabConfig): number | undefined => {
    if (!entityCounts) return undefined;
    if (tab.id === 'ALL') return allCount;
    if (!tab.countKey) return undefined;
    return entityCounts[tab.countKey] as number | undefined;
  };

  const handleSubTabChange = (tabId: EntitySubTab) => {
    setActiveSubTab(tabId);
    setPage(1);
    setSearchTerm('');
  };

  const handleEntityClick = (entity: CaseEntityRoleListItem) => {
    navigate(`/entities/${entity.entity_id}`);
  };

  return (
    <div className="flex flex-col bg-[#07090E] border border-[#1E293B] rounded-sm shadow-xl overflow-hidden">
      {/* ── HEADER ── */}
      <div className="bg-[#0A0E17] border-b border-[#1E293B] px-5 py-3 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-widest font-mono">
              Entity Registry
            </h3>
            <p className="text-[10px] text-slate-500 font-mono mt-0.5">
              People, vehicles, phone records and devices connected to this investigation
            </p>
          </div>
          {entityCounts && (
            <div className="hidden sm:flex items-center gap-4 text-[10px] font-mono">
              <div className="text-right">
                <span className="block text-sm font-bold text-white">{allCount.toLocaleString()}</span>
                <span className="text-slate-500 uppercase">Total</span>
              </div>
              <div className="text-right">
                <span className="block text-sm font-bold text-cyan-400">{entityCounts.person_count}</span>
                <span className="text-slate-500 uppercase">People</span>
              </div>
              <div className="text-right">
                <span className="block text-sm font-bold text-emerald-400">{entityCounts.vehicle_count}</span>
                <span className="text-slate-500 uppercase">Vehicles</span>
              </div>
              <div className="text-right">
                <span className="block text-sm font-bold text-purple-400">{entityCounts.phone_count.toLocaleString()}</span>
                <span className="text-slate-500 uppercase">Phones</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── SUB-TAB NAVIGATION ── */}
      <div className="bg-[#080B12] border-b border-[#1E293B] flex items-center gap-0.5 px-2 pt-2 overflow-x-auto flex-shrink-0">
        {SUB_TABS.map((tab) => {
          const Icon = tab.icon;
          const count = getTabCount(tab);
          const isActive = activeSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleSubTabChange(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 text-[10px] font-mono font-semibold uppercase tracking-wider rounded-t border-b-2 whitespace-nowrap transition-all ${
                isActive
                  ? 'border-cyan-400 text-cyan-300 bg-cyan-950/30'
                  : 'border-transparent text-slate-500 hover:text-slate-300 hover:bg-[#0C1220]'
              }`}
            >
              <Icon className={`w-3 h-3 ${isActive ? 'text-cyan-400' : 'text-slate-600'}`} />
              <span>{tab.shortLabel}</span>
              {count !== undefined && count > 0 && (
                <span
                  className={`text-[9px] px-1.5 py-0.5 rounded font-bold border ${
                    isActive ? tab.badgeClass : 'bg-[#0A0E17] text-slate-500 border-slate-700'
                  }`}
                >
                  {count.toLocaleString()}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ── SEARCH BAR ── */}
      <div className="px-4 py-2.5 border-b border-[#1E293B] bg-[#080B12] flex-shrink-0">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-600" />
          <input
            type="text"
            placeholder={`Search ${activeSubTab === 'ALL' ? 'entities' : activeSubTab.toLowerCase().replace('_', ' ')}...`}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-[#0A0E17] border border-[#1E293B] rounded py-1.5 pl-8 pr-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/40 placeholder-slate-600 font-mono transition-colors"
          />
        </div>
        {searchTerm && (
          <p className="text-[9px] font-mono text-slate-500 mt-1">
            Filtering current page results. Use pagination to search across all records.
          </p>
        )}
      </div>

      {/* ── CONTENT BODY ── */}
      <div className="flex-1 overflow-y-auto min-h-[300px]">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin text-cyan-500" />
            <span className="text-[10px] font-mono uppercase tracking-widest">Querying Entity Registry...</span>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-slate-500">
            <AlertTriangle className="w-8 h-8 text-red-500" />
            <span className="text-xs font-mono uppercase">Entity registry query failed</span>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-2 text-slate-500">
            <Shield className="w-8 h-8 text-slate-700" />
            <p className="text-xs font-mono uppercase tracking-wider">
              {searchTerm ? 'No matching entities on this page' : `No ${activeSubTab === 'ALL' ? 'entities' : activeSubTab.toLowerCase().replace('_', ' ')} linked`}
            </p>
          </div>
        ) : activeSubTab === 'PERSON' ? (
          /* ── PERSON GRID VIEW ── */
          <div className="p-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3">
              {filteredItems.map((entity) => (
                <PersonCard
                  key={entity.entity_id}
                  entity={entity}
                  onClick={() => handleEntityClick(entity)}
                />
              ))}
            </div>
          </div>
        ) : (
          /* ── TABLE VIEW for ALL other entity types ── */
          <div>
            {/* Column headers */}
            <div className="flex items-center px-4 py-2 border-b border-[#1E293B] bg-[#080B12] text-[9px] font-mono text-slate-500 uppercase tracking-wider">
              <div className="w-6 mr-3 flex-shrink-0" />
              <div className="flex-1">Identifier</div>
              <div className="hidden sm:block w-24 mr-3">ID Fragment</div>
              <div className="w-28 mr-3">Role</div>
              <div className="w-20 text-right">Action</div>
            </div>
            {filteredItems.map((entity) => (
              <EntityRow
                key={entity.entity_id}
                entity={entity}
                onClick={() => handleEntityClick(entity)}
              />
            ))}
          </div>
        )}
      </div>

      {/* ── PAGINATION FOOTER ── */}
      {totalPages > 1 && (
        <Pagination
          page={page}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={PAGE_SIZE}
          onPrev={() => setPage((p) => Math.max(1, p - 1))}
          onNext={() => setPage((p) => Math.min(totalPages, p + 1))}
        />
      )}
    </div>
  );
};
