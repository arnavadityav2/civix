import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search as SearchIcon, Filter, Hash, ShieldCheck, ChevronRight, ChevronLeft, Loader2 } from 'lucide-react';
import { EntityAvatar } from './EntityAvatar';
import type { EntityResponse } from '../../types/api';
import { casesApi } from '../../api/cases';

export type RegistryEntity = EntityResponse & {
  entity: EntityResponse['entity'] & {
    role?: string;
    case_count?: number;
  };
};

interface EntityRegistryListProps {
  entities?: RegistryEntity[];
  isLoading?: boolean;
  selectedEntityId?: string;
  caseId?: string;
}

export const EntityRegistryList: React.FC<EntityRegistryListProps> = ({ 
  entities: initialEntities = [], 
  isLoading: initialLoading = false,
  selectedEntityId,
  caseId
}) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('ALL');
  const [page, setPage] = useState<number>(1);
  const pageSize = 50;

  const filterOptions = ['ALL', 'PERSON', 'VEHICLE', 'PHONE_NUMBER', 'ORGANIZATION', 'DEVICE'];

  // Server-side paginated query when caseId is supplied
  const { data: caseEntitiesResp, isLoading: isCaseQueryLoading } = useQuery({
    queryKey: ['case-entities-registry', caseId, filterType, page, pageSize],
    queryFn: () => (caseId ? casesApi.getCaseEntities(caseId, {
      entity_type: filterType === 'ALL' ? undefined : filterType,
      limit: pageSize,
      offset: (page - 1) * pageSize
    }) : Promise.resolve(null)),
    enabled: !!caseId,
    staleTime: 10_000,
  });

  const handleFilterChange = (newType: string) => {
    setFilterType(newType);
    setPage(1);
  };

  // Determine effective entities to display
  const effectiveEntities: RegistryEntity[] = useMemo(() => {
    if (caseId && caseEntitiesResp) {
      return (caseEntitiesResp.items || []).map((e: any) => ({
        entity: {
          entity_id: e.entity_id,
          entity_type: e.entity_type,
          created_at: '',
          visibility_status: 'ACTIVE',
          role: e.role,
        },
        subtype_data: {
          display_name: e.display_name,
          avatar_url: e.avatar_url,
          legal_name: e.display_name,
          model: e.display_name,
          msisdn: e.display_name,
          registration_number: e.display_name,
          raw_identifier: e.display_name
        }
      }));
    }
    return initialEntities;
  }, [caseId, caseEntitiesResp, initialEntities]);

  // Client-side search filtering on current active set
  const getDisplayName = (e: RegistryEntity): string => {
    const type = e.entity.entity_type?.toUpperCase();
    if (!e.subtype_data) return 'Unknown Entity';
    
    switch (type) {
      case 'PERSON': return e.subtype_data.display_name || 'Unknown Person';
      case 'ORGANIZATION': return e.subtype_data.legal_name || 'Organization';
      case 'DEVICE': return e.subtype_data.model || e.subtype_data.imei || 'Device';
      case 'PHONE_NUMBER': return e.subtype_data.msisdn || 'Phone Number';
      case 'VEHICLE': return e.subtype_data.registration_number || 'Vehicle';
      case 'FINANCIAL_ACCOUNT': return e.subtype_data.account_number || e.subtype_data.masked_number || 'Financial Account';
      case 'SOURCE_IDENTITY': return e.subtype_data.raw_identifier || 'Source Identity';
      default: return e.subtype_data.display_name || 'Entity';
    }
  };

  const filteredEntities = useMemo(() => {
    return effectiveEntities.filter(e => {
      if (!caseId && filterType !== 'ALL' && e.entity.entity_type?.toUpperCase() !== filterType) {
        return false;
      }
      
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const typeStr = e.entity.entity_type?.toLowerCase() || '';
        const idStr = e.entity.entity_id.toLowerCase();
        const displayName = getDisplayName(e).toLowerCase();
        return typeStr.includes(term) || idStr.includes(term) || displayName.includes(term);
      }
      return true;
    });
  }, [effectiveEntities, searchTerm, filterType, caseId]);

  // Stats derivation
  const totalCount = caseId && caseEntitiesResp ? caseEntitiesResp.total_count : (initialEntities.length);
  const totalPages = Math.ceil(totalCount / pageSize) || 1;

  const stats = useMemo(() => {
    if (caseId && caseEntitiesResp?.entity_counts) {
      const ec = caseEntitiesResp.entity_counts;
      return {
        total: ec.person_count + ec.vehicle_count + ec.phone_count + (ec.organization_count || 0) + (ec.device_count || 0),
        persons: ec.person_count,
        vehicles: ec.vehicle_count,
        phones: ec.phone_count
      };
    }
    const s = { total: initialEntities.length, persons: 0, vehicles: 0, phones: 0 };
    initialEntities.forEach(e => {
      switch (e.entity.entity_type?.toUpperCase()) {
        case 'PERSON': s.persons++; break;
        case 'VEHICLE': s.vehicles++; break;
        case 'PHONE_NUMBER': s.phones++; break;
      }
    });
    return s;
  }, [caseId, caseEntitiesResp, initialEntities]);

  const isLoading = caseId ? isCaseQueryLoading : initialLoading;

  return (
    <div className="flex flex-col h-full bg-civix-surface border border-civix-border rounded-sm overflow-hidden shadow-sm">
      
      {/* HEADER SECTION */}
      <div className="bg-civix-surface-2 border-b border-civix-border p-4 flex-shrink-0 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-civix-text-main uppercase tracking-widest font-mono">
              ENTITY REGISTRY
            </h3>
            <p className="text-[10px] text-civix-text-muted font-sans mt-0.5">
              People, vehicles, phone records, and devices connected to investigation.
            </p>
          </div>
          <div className="flex gap-3 text-[10px] font-mono text-civix-text-muted">
            <div className="text-right">
              <span className="block font-bold text-civix-text-main">{stats.total.toLocaleString()}</span>
              TOTAL
            </div>
            <div className="text-right">
              <span className="block font-bold text-civix-blue-400">{stats.persons.toLocaleString()}</span>
              PEOPLE
            </div>
            <div className="text-right">
              <span className="block font-bold text-civix-gold">{stats.vehicles.toLocaleString()}</span>
              VEHICLES
            </div>
            <div className="text-right hidden sm:block">
              <span className="block font-bold text-civix-green-400">{stats.phones.toLocaleString()}</span>
              PHONES
            </div>
          </div>
        </div>

        {/* SEARCH AND FILTERS */}
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-civix-text-muted" />
            <input
              type="text"
              placeholder="Search active page entities by name, ID, identifier..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-civix-surface-2 border border-civix-border rounded-sm py-1.5 pl-8 pr-3 text-xs text-civix-text-main focus:outline-none focus:border-civix-blue-500 placeholder-civix-text-muted/50 transition-colors font-mono"
            />
          </div>
          <div className="relative w-full sm:w-44 flex-shrink-0">
            <Filter className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-civix-text-muted" />
            <select
              value={filterType}
              onChange={(e) => handleFilterChange(e.target.value)}
              className="w-full appearance-none bg-civix-surface-2 border border-civix-border rounded-sm py-1.5 pl-8 pr-3 text-xs text-civix-text-main focus:outline-none focus:border-civix-blue-500 transition-colors uppercase font-mono tracking-wider cursor-pointer"
            >
              {filterOptions.map(opt => (
                <option key={opt} value={opt}>{opt.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* LIST SECTION */}
      <div className="flex-1 overflow-y-auto min-h-0 bg-civix-surface">
        {isLoading ? (
          <div className="h-full flex flex-col items-center justify-center space-y-3 py-16">
            <Loader2 className="w-6 h-6 animate-spin text-civix-blue-light" />
            <p className="text-xs font-mono text-civix-text-muted uppercase tracking-widest">Querying Entity Registry...</p>
          </div>
        ) : filteredEntities.length === 0 ? (
          <div className="py-16 px-6 text-center text-civix-text-muted">
            <ShieldCheck className="w-8 h-8 mx-auto mb-2 text-civix-text-secondary opacity-50" />
            <p className="text-xs font-mono uppercase tracking-wider">NO ENTITIES FOUND FOR THIS FILTER</p>
          </div>
        ) : (
          <div className="divide-y divide-civix-border/50">
            {filteredEntities.map((entityObj) => {
              const { entity, subtype_data } = entityObj;
              const isSelected = selectedEntityId === entity.entity_id;
              const type = entity.entity_type?.toUpperCase();
              const displayName = getDisplayName(entityObj);
              const role = entity.role || 'SUBJECT';

              return (
                <div 
                  key={entity.entity_id}
                  className={`group flex items-center p-3 transition-colors ${
                    isSelected 
                      ? 'bg-civix-blue-900/10 border-l-2 border-l-civix-blue-500' 
                      : 'hover:bg-civix-surface-2 border-l-2 border-l-transparent'
                  }`}
                >
                  {/* Entity Image / Avatar */}
                  <div className="flex-shrink-0 mr-3">
                    <EntityAvatar 
                      entityType={type}
                      avatarUrl={subtype_data?.avatar_url}
                      name={displayName}
                      size="lg"
                    />
                  </div>

                  {/* Core Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <h4 className="text-sm font-bold text-civix-text-main truncate font-sans tracking-tight">
                        {displayName}
                      </h4>
                      {type === 'PERSON' && subtype_data?.notes && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-sm border border-civix-gold-600/30 bg-civix-gold-950/40 text-civix-gold-400 uppercase">
                          Alias
                        </span>
                      )}
                    </div>
                    <div className="flex items-center text-[10px] font-mono text-civix-text-muted mt-1 space-x-3">
                      <span className="flex items-center space-x-1">
                        <Hash className="w-3 h-3 text-civix-text-secondary" />
                        <span className="truncate w-28" title={entity.entity_id}>{entity.entity_id.split('-')[0]}</span>
                      </span>
                      <span className="text-civix-border">•</span>
                      <span className="text-civix-blue-300 uppercase">{type.replace(/_/g, ' ')}</span>
                      <span className="text-civix-border">•</span>
                      <span className="text-civix-text-secondary uppercase">{role.replace(/_/g, ' ')}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex-shrink-0 flex flex-col items-end pl-3 space-y-2">
                    <button
                      onClick={() => navigate(`/entities/${entity.entity_id}`)}
                      className={`flex items-center space-x-1 px-3 py-1.5 rounded-sm text-[10px] font-mono font-bold transition-colors ${
                        isSelected 
                          ? 'bg-civix-blue-600 text-white shadow-sm'
                          : 'bg-civix-surface-2 border border-civix-border text-civix-text-secondary hover:text-civix-text-main hover:border-civix-blue-500/50'
                      }`}
                    >
                      <span>VIEW DOSSIER</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* FOOTER PAGINATION */}
      {caseId && totalPages > 1 && (
        <div className="bg-civix-surface-2 border-t border-civix-border p-3 flex items-center justify-between text-xs font-mono text-civix-text-muted">
          <div>
            Showing <strong className="text-white">{(page - 1) * pageSize + 1}</strong> to <strong className="text-white">{Math.min(page * pageSize, totalCount)}</strong> of <strong className="text-white">{totalCount.toLocaleString()}</strong>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1 bg-civix-surface border border-civix-border rounded hover:bg-civix-surface-3 disabled:opacity-40"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-white font-bold">Page {page} of {totalPages}</span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1 bg-civix-surface border border-civix-border rounded hover:bg-civix-surface-3 disabled:opacity-40"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
