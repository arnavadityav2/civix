import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search as SearchIcon, Filter, Hash, ShieldCheck, ChevronRight } from 'lucide-react';
import { EntityAvatar } from './EntityAvatar';
import type { EntityResponse } from '../../types/api';

// Extend EntityBase internally if needed to include role/case_count for list views
export type RegistryEntity = EntityResponse & {
  entity: EntityResponse['entity'] & {
    role?: string;
    case_count?: number;
  };
};

interface EntityRegistryListProps {
  entities: RegistryEntity[];
  isLoading: boolean;
  selectedEntityId?: string;
}

export const EntityRegistryList: React.FC<EntityRegistryListProps> = ({ 
  entities, 
  isLoading,
  selectedEntityId
}) => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('ALL');

  const filterOptions = ['ALL', 'PERSON', 'VEHICLE', 'ORGANIZATION', 'DEVICE', 'PHONE_NUMBER', 'FINANCIAL_ACCOUNT'];

  // Helper to extract display name
  const getDisplayName = (e: EntityWithSubtype): string => {
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
      default: return 'Entity';
    }
  };

  const filteredEntities = useMemo(() => {
    return entities.filter(e => {
      // Type Filter
      if (filterType !== 'ALL' && e.entity.entity_type?.toUpperCase() !== filterType) {
        return false;
      }
      
      // Search Filter
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const typeStr = e.entity.entity_type?.toLowerCase() || '';
        const idStr = e.entity.entity_id.toLowerCase();
        const displayName = getDisplayName(e).toLowerCase();
        
        let match = typeStr.includes(term) || idStr.includes(term) || displayName.includes(term);
        
        // Specific checks like Alias for Person
        if (e.entity.entity_type === 'PERSON' && e.subtype_data) {
          const person = e.subtype_data as Record<string, any>;
          if (person.notes && person.notes.toLowerCase().includes(term)) {
            match = true;
          }
        }
        
        if (!match) return false;
      }
      return true;
    });
  }, [entities, searchTerm, filterType]);

  // Aggregate stats
  const stats = useMemo(() => {
    const s = { total: entities.length, persons: 0, vehicles: 0, orgs: 0, devices: 0 };
    entities.forEach(e => {
      switch (e.entity.entity_type) {
        case 'PERSON': s.persons++; break;
        case 'VEHICLE': s.vehicles++; break;
        case 'ORGANIZATION': s.orgs++; break;
        case 'DEVICE': s.devices++; break;
      }
    });
    return s;
  }, [entities]);

  if (isLoading) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-3 bg-civix-surface border border-civix-border rounded-sm py-12">
        <div className="w-8 h-8 border-2 border-civix-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-xs font-mono text-civix-text-muted uppercase tracking-widest">LOADING ENTITY REGISTRY</p>
      </div>
    );
  }

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
              People, vehicles, organizations and devices connected to investigations.
            </p>
          </div>
          <div className="flex gap-3 text-[10px] font-mono text-civix-text-muted">
            <div className="text-right">
              <span className="block font-bold text-civix-text-main">{stats.total}</span>
              TOTAL
            </div>
            <div className="text-right">
              <span className="block font-bold text-civix-blue-400">{stats.persons}</span>
              PEOPLE
            </div>
            <div className="text-right hidden sm:block">
              <span className="block font-bold text-civix-red-400">{stats.vehicles}</span>
              VEHICLES
            </div>
          </div>
        </div>

        {/* SEARCH AND FILTERS */}
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-civix-text-muted" />
            <input
              type="text"
              placeholder="Search entities by name, ID, alias..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-civix-surface-2 border border-civix-border rounded-sm py-1.5 pl-8 pr-3 text-xs text-civix-text-main focus:outline-none focus:border-civix-blue-500 placeholder-civix-text-muted/50 transition-colors"
            />
          </div>
          <div className="relative w-full sm:w-40 flex-shrink-0">
            <Filter className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-civix-text-muted" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full appearance-none bg-civix-surface-2 border border-civix-border rounded-sm py-1.5 pl-8 pr-3 text-xs text-civix-text-main focus:outline-none focus:border-civix-blue-500 transition-colors uppercase font-mono tracking-wider cursor-pointer"
            >
              {filterOptions.map(opt => (
                <option key={opt} value={opt}>{opt.replace('_', ' ')}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* LIST SECTION */}
      <div className="flex-1 overflow-y-auto min-h-0 bg-civix-surface">
        {filteredEntities.length === 0 ? (
          <div className="py-12 px-6 text-center text-civix-text-muted">
            <ShieldCheck className="w-8 h-8 mx-auto mb-2 text-civix-text-secondary opacity-50" />
            <p className="text-xs font-mono uppercase tracking-wider">NO ENTITIES MATCH SEARCH</p>
          </div>
        ) : (
          <div className="divide-y divide-civix-border/50">
            {filteredEntities.map((entityObj) => {
              const { entity, subtype_data } = entityObj;
              const isSelected = selectedEntityId === entity.entity_id;
              const type = entity.entity_type?.toUpperCase();
              const displayName = getDisplayName(entityObj);
              
              // Role/Case Count (derived from context if possible, otherwise generic)
              // Since this list could be case-scoped or global, we show what we have safely
              const role = entity.role || 'SUBJECT';
              const caseCount = entity.case_count; // only exists if returned by specific API

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
                      avatarUrl={(subtype_data as PersonSubtype)?.avatar_url}
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
                      {type === 'PERSON' && (subtype_data as PersonSubtype)?.notes && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-sm border border-civix-gold-600/30 bg-civix-gold-950/40 text-civix-gold-400 uppercase">
                          Alias
                        </span>
                      )}
                    </div>
                    <div className="flex items-center text-[10px] font-mono text-civix-text-muted mt-1 space-x-3">
                      <span className="flex items-center space-x-1">
                        <Hash className="w-3 h-3 text-civix-text-secondary" />
                        <span className="truncate w-24" title={entity.entity_id}>{entity.entity_id.split('-')[0]}</span>
                      </span>
                      <span className="text-civix-border">•</span>
                      <span className="text-civix-blue-300 uppercase">{type.replace('_', ' ')}</span>
                      <span className="text-civix-border">•</span>
                      <span className="text-civix-text-secondary uppercase">{role}</span>
                    </div>
                  </div>

                  {/* Signals / Actions */}
                  <div className="flex-shrink-0 flex flex-col items-end pl-3 space-y-2">
                    {caseCount !== undefined && caseCount > 1 && (
                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-sm bg-civix-red-950/40 border border-civix-red-600/40 text-civix-red-400">
                        {caseCount} CASES • NETWORK HUB
                      </span>
                    )}
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
    </div>
  );
};
