import React, { useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { entitiesApi } from '../api/entities';
import { identityApi } from '../api/identity';
import { casesApi } from '../api/cases';
import { graphApi } from '../api/graph';
import { leadsApi } from '../api/leads';
import { evidenceApi } from '../api/evidence';
import { useCaseSelection } from '../context/CaseSelectionContext';
import type { GraphNode, CaseListItem } from '../types/api';
import {
  ArrowLeft,
  Loader2,
  AlertTriangle,
  User,
  Building2,
  Smartphone,
  Phone,
  Car,
  CreditCard,
  Fingerprint,
  ShieldCheck,
  Calendar,
  Globe,
  Hash,
  Clock,
  Eye,
  Briefcase,
  ChevronRight,
  ChevronDown,
  Info,
  GitFork,
  FileText,
  RefreshCw,
  Zap,
  ExternalLink,
  ShieldAlert,
  Network,
  Sparkles
} from 'lucide-react';
import { EntityRegistryList, type RegistryEntity } from '../components/domain/EntityRegistryList';
import { EntityConnectionsView } from '../components/domain/EntityConnectionsView';

// ── Entity type display config ───────────────────────────────────────────────

const ENTITY_ICONS: Record<string, React.ElementType> = {
  PERSON: User,
  ORGANIZATION: Building2,
  DEVICE: Smartphone,
  PHONE_NUMBER: Phone,
  VEHICLE: Car,
  FINANCIAL_ACCOUNT: CreditCard,
  SOURCE_IDENTITY: Fingerprint,
};

const ENTITY_COLOR_CLASS: Record<string, string> = {
  PERSON: 'bg-civix-blue-900/40 border-civix-blue-600/50 text-civix-blue-400',
  ORGANIZATION: 'bg-civix-gold-900/40 border-civix-gold-600/50 text-civix-gold-400',
  DEVICE: 'bg-civix-blue-950/60 border-civix-blue-500/40 text-civix-blue-300',
  PHONE_NUMBER: 'bg-civix-green-900/40 border-civix-green-600/50 text-civix-green-400',
  VEHICLE: 'bg-civix-red-900/40 border-civix-red-600/50 text-civix-red-400',
  FINANCIAL_ACCOUNT: 'bg-civix-gold-900/40 border-civix-gold-600/50 text-civix-gold-400',
  SOURCE_IDENTITY: 'bg-civix-surface-2 border-civix-border text-civix-text-secondary',
};

const ENTITY_ICON_BORDER: Record<string, string> = {
  PERSON: 'bg-civix-blue-950 border-civix-blue-600/50',
  ORGANIZATION: 'bg-civix-gold-950 border-civix-gold-600/50',
  DEVICE: 'bg-civix-surface-2 border-civix-blue-500/40',
  PHONE_NUMBER: 'bg-civix-green-950 border-civix-green-600/50',
  VEHICLE: 'bg-civix-red-950 border-civix-red-600/50',
  FINANCIAL_ACCOUNT: 'bg-civix-gold-950 border-civix-gold-600/50',
  SOURCE_IDENTITY: 'bg-civix-surface-2 border-civix-border',
};

const ENTITY_ICON_COLOR: Record<string, string> = {
  PERSON: 'text-civix-blue-400',
  ORGANIZATION: 'text-civix-gold-400',
  DEVICE: 'text-civix-blue-300',
  PHONE_NUMBER: 'text-civix-green-400',
  VEHICLE: 'text-civix-red-400',
  FINANCIAL_ACCOUNT: 'text-civix-gold-400',
  SOURCE_IDENTITY: 'text-civix-text-secondary',
};

function getEntityIcon(type: string): React.ElementType {
  return ENTITY_ICONS[type?.toUpperCase()] ?? Fingerprint;
}

/** Strip synthetic suffix (e.g. `RJ14-CB-2847_b058a8f4` -> `RJ14-CB-2847`) */
function cleanSyntheticSuffix(value: string): string {
  if (!value) return value;
  return value.replace(/_[0-9a-f]{8}$/i, '');
}

/** Format predicate string for human display. REGISTERED_TO -> Registered To */
function formatPredicate(predicate: string): string {
  return predicate
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

// ── Attribute Row ────────────────────────────────────────────────────────────

interface AttributeRowProps {
  label: string;
  value: React.ReactNode;
  icon?: React.ElementType;
  mono?: boolean;
}

const AttributeRow: React.FC<AttributeRowProps> = ({ label, value, icon: Icon, mono = false }) => (
  <div className="flex items-start py-2 border-b border-civix-border/40 last:border-b-0">
    <div className="w-40 flex-shrink-0 flex items-center space-x-2 pr-3">
      {Icon && <Icon className="w-3.5 h-3.5 text-civix-text-muted flex-shrink-0" />}
      <span className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider">{label}</span>
    </div>
    <div className={`flex-1 text-xs ${mono ? 'font-mono text-civix-text-main' : 'text-civix-text-main font-medium'}`}>
      {value}
    </div>
  </div>
);

// ── Section Panel ────────────────────────────────────────────────────────────

interface SectionPanelProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  headerRight?: React.ReactNode;
}

const SectionPanel: React.FC<SectionPanelProps> = ({ title, subtitle, children, headerRight }) => (
  <div className="civix-panel rounded-sm overflow-hidden">
    <div className="civix-panel-header flex items-center justify-between">
      <div>
        <h3 className="civix-panel-title">{title}</h3>
        {subtitle && <p className="civix-panel-subtitle mt-0.5">{subtitle}</p>}
      </div>
      {headerRight}
    </div>
    <div className="p-4">{children}</div>
  </div>
);

// ── Truthful Empty State Component ───────────────────────────────────────────

interface TruthfulEmptyStateProps {
  title: string;
  description: string;
  icon?: React.ElementType;
}

const TruthfulEmptyState: React.FC<TruthfulEmptyStateProps> = ({
  title,
  description,
  icon: Icon = Info
}) => (
  <div className="py-6 px-4 bg-civix-surface border border-civix-border rounded-sm text-center space-y-1.5">
    <Icon className="w-5 h-5 text-civix-text-muted mx-auto" />
    <p className="text-xs font-bold text-civix-text-secondary uppercase tracking-wider">{title}</p>
    <p className="text-[11px] text-civix-text-muted max-w-md mx-auto leading-relaxed">{description}</p>
  </div>
);

// ── Subtype Renderers ─────────────────────────────────────────────────────────

function renderPersonAttributes(data: Record<string, any>) {
  const hasAnyData = data && Object.keys(data).some(k => data[k] != null && data[k] !== '' && data[k] !== false);
  if (!hasAnyData) {
    return <TruthfulEmptyState title="NO SUBTYPE DATA AVAILABLE" description="No additional Person attributes are populated in the database for this record." />;
  }

  return (
    <div>
      {data.display_name != null && (
        <AttributeRow label="Full Name" value={data.display_name} icon={User} />
      )}
      {data.date_of_birth != null && (
        <AttributeRow label="Date of Birth" value={String(data.date_of_birth)} icon={Calendar} mono />
      )}
      {data.gender != null && (
        <AttributeRow label="Gender" value={String(data.gender)} />
      )}
      {data.nationality != null && (
        <AttributeRow label="Nationality" value={String(data.nationality)} icon={Globe} />
      )}
      {data.is_deceased != null && (
        <AttributeRow
          label="Deceased"
          value={
            <span className={data.is_deceased ? 'text-civix-red-400 font-semibold' : 'text-civix-text-main'}>
              {data.is_deceased ? 'YES' : 'NO'}
            </span>
          }
        />
      )}
      {data.deceased_at != null && (
        <AttributeRow label="Deceased Date" value={String(data.deceased_at)} icon={Calendar} mono />
      )}
      {data.notes != null && data.notes !== '' && (
        <AttributeRow label="Notes" value={<span className="italic text-civix-text-secondary">{String(data.notes)}</span>} />
      )}
    </div>
  );
}

function renderDeviceAttributes(data: Record<string, any>) {
  const hasAnyData = data && Object.keys(data).some(k => data[k] != null && data[k] !== '');
  if (!hasAnyData) {
    return <TruthfulEmptyState title="NO DEVICE DATA AVAILABLE" description="No additional Device attributes are populated in the database for this record." />;
  }

  return (
    <div>
      {data.device_type != null && (
        <AttributeRow label="Device Type" value={String(data.device_type)} icon={Smartphone} mono />
      )}
      {data.manufacturer != null && (
        <AttributeRow label="Manufacturer" value={String(data.manufacturer)} />
      )}
      {data.model != null && (
        <AttributeRow label="Model" value={String(data.model)} />
      )}
      {data.imei != null && (
        <AttributeRow label="IMEI" value={String(data.imei)} icon={Hash} mono />
      )}
      {data.mac_address != null && (
        <AttributeRow label="MAC Address" value={String(data.mac_address)} icon={Hash} mono />
      )}
    </div>
  );
}

function renderOrganizationAttributes(data: Record<string, any>) {
  const hasAnyData = data && Object.keys(data).some(k => data[k] != null && data[k] !== '');
  if (!hasAnyData) {
    return <TruthfulEmptyState title="NO ORGANIZATION DATA AVAILABLE" description="No additional Organization attributes are populated in the database for this record." />;
  }

  return (
    <div>
      {data.legal_name != null && (
        <AttributeRow label="Legal Name" value={String(data.legal_name)} icon={Building2} />
      )}
      {data.org_type != null && (
        <AttributeRow label="Organization Type" value={String(data.org_type)} mono />
      )}
      {data.registration_number != null && (
        <AttributeRow label="Registration No." value={cleanSyntheticSuffix(String(data.registration_number))} icon={Hash} mono />
      )}
      {data.incorporation_date != null && (
        <AttributeRow label="Incorporation Date" value={String(data.incorporation_date)} icon={Calendar} mono />
      )}
      {data.jurisdiction != null && (
        <AttributeRow label="Jurisdiction" value={String(data.jurisdiction)} icon={Globe} mono />
      )}
    </div>
  );
}

function renderPhoneNumberAttributes(data: Record<string, any>) {
  const hasAnyData = data && Object.keys(data).some(k => data[k] != null && data[k] !== '');
  if (!hasAnyData) {
    return <TruthfulEmptyState title="NO PHONE DATA AVAILABLE" description="No additional Phone Number attributes are populated in the database for this record." />;
  }

  return (
    <div>
      {data.msisdn != null && (
        <AttributeRow label="MSISDN" value={String(data.msisdn)} icon={Phone} mono />
      )}
      {data.country_code != null && (
        <AttributeRow label="Country Code" value={String(data.country_code)} icon={Globe} mono />
      )}
      {data.operator != null && (
        <AttributeRow label="Operator" value={String(data.operator)} />
      )}
      {data.number_type != null && (
        <AttributeRow label="Number Type" value={String(data.number_type)} mono />
      )}
    </div>
  );
}

function renderSourceIdentityAttributes(data: Record<string, any>) {
  const hasAnyData = data && Object.keys(data).some(k => data[k] != null && data[k] !== '');
  if (!hasAnyData) {
    return <TruthfulEmptyState title="NO SOURCE IDENTITY DATA AVAILABLE" description="No additional Source Identity attributes are populated in the database for this record." />;
  }

  return (
    <div>
      {data.raw_identifier != null && (
        <AttributeRow label="Raw Identifier" value={cleanSyntheticSuffix(String(data.raw_identifier))} icon={Fingerprint} mono />
      )}
      {data.identifier_type != null && (
        <AttributeRow label="Identifier Type" value={String(data.identifier_type)} mono />
      )}
      {data.observed_at != null && (
        <AttributeRow label="Observed At" value={new Date(data.observed_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })} icon={Clock} mono />
      )}
    </div>
  );
}

function renderSubtypeSection(entityType: string, subtypeData: Record<string, any>) {
  const type = entityType?.toUpperCase();

  // Backend ADR-033: VEHICLE and FINANCIAL_ACCOUNT have no Pydantic model / subtype table
  if (type === 'VEHICLE') {
    const regNum = subtypeData?.registration_number ?? null;
    const vType = subtypeData?.vehicle_type ?? null;
    return (
      <div className="space-y-3">
        {regNum && <AttributeRow label="Registration No." value={cleanSyntheticSuffix(String(regNum))} icon={Hash} mono />}
        {vType && <AttributeRow label="Vehicle Type" value={String(vType)} mono />}
        <div className="py-3 px-3.5 bg-civix-gold-950/40 border border-civix-gold-600/40 rounded-sm text-xs space-y-1">
          <div className="flex items-center space-x-1.5 text-civix-gold-400 font-bold text-[10px] uppercase tracking-wider">
            <Info className="w-3.5 h-3.5 text-civix-gold-500" />
            <span>ADR-033 Schema Constraint</span>
          </div>
          <p className="text-[11px] leading-relaxed text-civix-text-secondary font-sans">
            Extended vehicle registry attributes (make, model, color, engine number, chassis) are not defined in the current API schema.
          </p>
        </div>
      </div>
    );
  }

  if (type === 'FINANCIAL_ACCOUNT') {
    const accNum = subtypeData?.account_number || subtypeData?.masked_number || null;
    return (
      <div className="space-y-3">
        {accNum && <AttributeRow label="Account Number" value={String(accNum)} icon={CreditCard} mono />}
        <div className="py-3 px-3.5 bg-civix-gold-950/40 border border-civix-gold-600/40 rounded-sm text-xs space-y-1">
          <div className="flex items-center space-x-1.5 text-civix-gold-400 font-bold text-[10px] uppercase tracking-wider">
            <Info className="w-3.5 h-3.5 text-civix-gold-500" />
            <span>ADR-033 Schema Constraint</span>
          </div>
          <p className="text-[11px] leading-relaxed text-civix-text-secondary font-sans">
            Financial account subtype details (bank name, IFSC code, account balance, owner mapping) are excluded from the core entity API contract. Balances and transactions are not fabricated.
          </p>
        </div>
      </div>
    );
  }

  const isEmpty = !subtypeData || Object.keys(subtypeData).length === 0;
  if (isEmpty) {
    return <TruthfulEmptyState title={`NO ${type} DATA`} description={`No subtype attributes returned for this ${type.toLowerCase()} entity.`} />;
  }

  switch (type) {
    case 'PERSON': return renderPersonAttributes(subtypeData);
    case 'DEVICE': return renderDeviceAttributes(subtypeData);
    case 'ORGANIZATION': return renderOrganizationAttributes(subtypeData);
    case 'PHONE_NUMBER': return renderPhoneNumberAttributes(subtypeData);
    case 'SOURCE_IDENTITY': return renderSourceIdentityAttributes(subtypeData);
    default: return <TruthfulEmptyState title="UNSUPPORTED SUBTYPE" description={`No renderer defined for entity type ${type}.`} />;
  }
}

// ── Derive display identity from entity response ─────────────────────────────

function deriveDisplayIdentity(entityType: string, subtypeData: Record<string, any>): string {
  const type = entityType?.toUpperCase();
  if (!subtypeData || Object.keys(subtypeData).length === 0) return 'Entity Record';
  switch (type) {
    case 'PERSON': return subtypeData.display_name || 'Person Entity';
    case 'ORGANIZATION': return subtypeData.legal_name || 'Organization Entity';
    case 'DEVICE': return subtypeData.model || subtypeData.imei || subtypeData.mac_address || `${subtypeData.device_type || 'Device'}`;
    case 'PHONE_NUMBER': return subtypeData.msisdn ? `Phone: ${subtypeData.msisdn}` : 'Phone Number';
    case 'SOURCE_IDENTITY': return cleanSyntheticSuffix(subtypeData.raw_identifier || 'Source Identity');
    case 'VEHICLE': return cleanSyntheticSuffix(subtypeData.registration_number || 'Vehicle Entity');
    case 'FINANCIAL_ACCOUNT': return subtypeData.account_number || subtypeData.masked_number || 'Financial Account';
    default: return 'Entity Record';
  }
}

// ── Main EntityDossierPage Component ──────────────────────────────────────────

export const EntityDossierPage: React.FC = () => {
  const { entityId } = useParams<{ entityId: string }>();
  const navigate = useNavigate();
  // const location = useLocation();
  const { selectedCaseId } = useCaseSelection();
  const [viewConnectionsMode, setViewConnectionsMode] = useState(false);

  // 1. Identity Base + Subtype API
  const { data: entityResponse, isLoading: entityLoading, error: entityError, refetch: refetchEntity } = useQuery({
    queryKey: ['entity', entityId],
    queryFn: () => entitiesApi.getEntity(entityId!)
  });

  // 2. Fetch Case Entities (for the left column)
  const { data: caseEntitiesData, isLoading: caseEntitiesLoading } = useQuery({
    queryKey: ['caseEntities', selectedCaseId],
    queryFn: () => (selectedCaseId ? casesApi.getCaseEntities(selectedCaseId) : Promise.resolve([])),
    enabled: !!selectedCaseId
  });

  const mappedCaseEntities: RegistryEntity[] = React.useMemo(() => {
    const rawData = caseEntitiesData as any;
    const arrayData = Array.isArray(rawData) ? rawData : (rawData?.items || rawData?.entities || []);
    return arrayData.map((e: any) => ({
      entity: {
        entity_id: e.entity_id,
        entity_type: e.entity_type,
        created_at: '',
        visibility_status: 'ACTIVE',
        role: e.role,
        case_count: 1
      },
      subtype_data: {
        display_name: e.display_name,
        avatar_url: e.avatar_url,
        legal_name: e.display_name,
        model: e.display_name,
        msisdn: e.display_name,
        registration_number: e.display_name,
        raw_identifier: e.display_name,
        notes: e.role_basis
      }
    }));
  }, [caseEntitiesData]);

  // 3. Identity Resolution (Candidates) API
  const { data: candidatesData } = useQuery({
    queryKey: ['identityCandidates'],
    queryFn: () => identityApi.getCandidates(),
    staleTime: 60_000,
  });

  const matchingCandidates = (Array.isArray(candidatesData) ? candidatesData : (candidatesData?.candidates || [])).filter(
    (c: any) => c.proposed_person_id === entityId || c.source_identity_id === entityId
  );

  // 3. Fetch Case List (to map case names for case involvement)
  const { data: casesList } = useQuery({
    queryKey: ['cases'],
    queryFn: () => casesApi.listCases(),
    staleTime: 60_000,
  });

  // 4. Fetch Graph Data for Active Case Context (to derive relationships & case involvement)
  const { data: graphData } = useQuery({
    queryKey: ['caseGraph_dossier', selectedCaseId],
    queryFn: () => (selectedCaseId ? graphApi.getCaseGraph(selectedCaseId, 2, 200, 500) : Promise.resolve(null)),
    enabled: !!selectedCaseId,
    staleTime: 30_000,
  });

  // 5. Fetch Leads for Active Case Context
  const { data: leadsData } = useQuery({
    queryKey: ['caseLeads_dossier', selectedCaseId],
    queryFn: () => (selectedCaseId ? leadsApi.getCaseLeads(selectedCaseId) : Promise.resolve([])),
    enabled: !!selectedCaseId,
    staleTime: 30_000,
  });

  // Filter leads targeting this entity
  const leadsArray = Array.isArray(leadsData) ? leadsData : ((leadsData as any)?.items || (leadsData as any)?.leads || []);
  const targetLeads = leadsArray.filter((l: any) => l.target_entity_id === entityId);

  // 6. Fetch Evidence for Active Case Context
  const { data: evidenceData } = useQuery({
    queryKey: ['caseEvidence_dossier', selectedCaseId],
    queryFn: () => (selectedCaseId ? evidenceApi.listEvidence(selectedCaseId) : Promise.resolve([])),
    enabled: !!selectedCaseId,
    staleTime: 30_000,
  });

  // Derive Case Involvement from graph nodes & case list
  const caseInvolvementList = React.useMemo(() => {
    if (!graphData || !entityId) return [];
    const entityNodes = graphData.nodes.filter(
      (n) => n.id === entityId || n.properties.entity_id === entityId
    );
    const casesArray = Array.isArray(casesList) ? casesList : ((casesList as any)?.items || (casesList as any)?.cases || []);
    const caseMap = new Map<string, CaseListItem>(casesArray.map((c: any) => [c.case_id, c]));

    const result: Array<{
      case_id: string;
      case_number: string;
      title: string;
      role: string;
      role_basis?: string;
      status: string;
      jurisdiction: string;
    }> = [];

    // Find HAS_ROLE edges from Case -> Entity
    const roleRels = graphData.relationships.filter(
      (r) => r.type === 'HAS_ROLE' && r.end_node === entityId
    );

    for (const rel of roleRels) {
      const caseNode = graphData.nodes.find((n) => n.id === rel.start_node);
      const caseMeta = caseNode ? caseMap.get(caseNode.id) : null;
      const cId = caseNode?.id || selectedCaseId || '';
      const cNum = (caseNode?.properties?.case_number as string | undefined) || caseMeta?.case_number || 'CASE';
      const cTitle = (caseNode?.properties?.title as string | undefined) || caseMeta?.title || 'Investigative Case';
      const cStatus = (caseNode?.properties?.status as string | undefined) || caseMeta?.status || 'OPEN';
      const cJur = (caseNode?.properties?.jurisdiction as string | undefined) || caseMeta?.jurisdiction || 'DELHI NCR';
      const role = rel.properties?.role || 'SUSPECT';
      const roleBasis = rel.properties?.role_basis || undefined;

      result.push({
        case_id: cId,
        case_number: cNum,
        title: cTitle,
        role: String(role),
        role_basis: roleBasis ? String(roleBasis) : undefined,
        status: cStatus,
        jurisdiction: cJur,
      });
    }

    // Fallback: if selectedCaseId exists and entity is in graph, but HAS_ROLE wasn't captured directly
    if (result.length === 0 && entityNodes.length > 0 && selectedCaseId) {
      const cMeta = caseMap.get(selectedCaseId);
      if (cMeta) {
        result.push({
          case_id: cMeta.case_id,
          case_number: cMeta.case_number,
          title: cMeta.title,
          role: String(entityNodes[0].properties.role || 'SUBJECT_ENTITY'),
          role_basis: entityNodes[0].properties.role_basis ? String(entityNodes[0].properties.role_basis) : undefined,
          status: cMeta.status,
          jurisdiction: cMeta.jurisdiction,
        });
      }
    }

    return result;
  }, [graphData, entityId, casesList, selectedCaseId]);

  // Derive Graph Relationships connected to this entity
  const entityRelationships = React.useMemo(() => {
    if (!graphData || !entityId) return [];
    const nodeMap = new Map<string, GraphNode>(graphData.nodes.map((n) => [n.id, n]));
    const rels: Array<{
      id: string;
      targetId: string;
      targetName: string;
      targetType: string;
      predicate: string;
      rawPredicate: string;
      epistemicStatus?: string;
      assertionId?: string;
      isCandidate?: boolean;
    }> = [];

    // 1. Direct relationships connected to this entity
    for (const r of graphData.relationships) {
      if (r.start_node === entityId || r.end_node === entityId) {
        const otherId = r.start_node === entityId ? r.end_node : r.start_node;
        const otherNode = nodeMap.get(otherId);
        if (!otherNode) continue;
        const targetType = otherNode.labels[0] || 'Entity';
        if (['Case', 'Assertion', 'Event'].includes(targetType)) continue;

        const targetName =
          otherNode.properties.display_name ||
          otherNode.properties.legal_name ||
          otherNode.properties.registration_number ||
          otherNode.properties.msisdn ||
          otherNode.id;

        rels.push({
          id: r.id,
          targetId: otherId,
          targetName: cleanSyntheticSuffix(String(targetName)),
          targetType,
          predicate: formatPredicate(r.type),
          rawPredicate: r.type,
          epistemicStatus: r.properties?.role || undefined,
          isCandidate: r.type === 'CANDIDATE_FOR',
        });
      }
    }

    // 2. Assertion-based relationships where subject/object matches entityId
    const assertionNodes = graphData.nodes.filter((n) => n.labels.includes('Assertion'));
    for (const a of assertionNodes) {
      const p = a.properties;
      const sub = p.subject_entity_id;
      const obj = p.object_entity_id;
      const pred = p.predicate;
      if (!pred || (sub !== entityId && obj !== entityId)) continue;

      const otherId = sub === entityId ? obj : sub;
      const otherNode = nodeMap.get(otherId);
      const targetName = otherNode
        ? otherNode.properties.display_name || otherNode.properties.registration_number || otherId
        : otherId.slice(0, 12) + '...';
      const targetType = otherNode ? otherNode.labels[0] : 'Entity';

      // Avoid duplicates
      if (!rels.some((r) => r.targetId === otherId && r.rawPredicate === pred)) {
        rels.push({
          id: a.id,
          targetId: otherId,
          targetName: cleanSyntheticSuffix(String(targetName)),
          targetType,
          predicate: formatPredicate(String(pred)),
          rawPredicate: String(pred),
          epistemicStatus: p.epistemic_status ? String(p.epistemic_status) : undefined,
          assertionId: a.id,
        });
      }
    }

    return rels;
  }, [graphData, entityId]);

  // ── Loading state ──────────────────────────────────────────────────────────
  if (entityLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-3 text-civix-text-muted">
        <Loader2 className="w-8 h-8 animate-spin text-civix-gold" />
        <div className="text-center">
          <p className="text-sm font-bold text-civix-text-main uppercase tracking-wider">Loading Entity Dossier</p>
          <p className="text-xs text-civix-text-muted font-mono mt-0.5">
            Querying PostgreSQL entity registry · RLS clearance check
          </p>
        </div>
      </div>
    );
  }

  // ── Error state ────────────────────────────────────────────────────────────
  if (entityError || !entityResponse) {
    return (
      <div className="py-16 text-center space-y-4 max-w-lg mx-auto">
        <AlertTriangle className="w-12 h-12 text-civix-red mx-auto" />
        <div>
          <h2 className="text-base font-bold text-civix-text-main uppercase tracking-wider">Entity File Unavailable</h2>
          <p className="text-xs text-civix-text-muted mt-1 leading-relaxed">
            Entity ID <span className="font-mono font-bold text-civix-text-secondary">{entityId}</span> could not be retrieved from the intelligence workspace.
            It may not exist, may be inactive, or you may lack case access permissions.
          </p>
        </div>
        <div className="flex items-center justify-center space-x-3 pt-2">
          <button
            onClick={() => refetchEntity()}
            className="civix-btn-primary"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Query</span>
          </button>
          <button
            onClick={() => setViewConnectionsMode(false)}
            className="civix-btn-secondary"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Search</span>
          </button>
        </div>
      </div>
    );
  }

  // Pre-process connections for the graph
  const connectionsForGraph = React.useMemo(() => {
    const rels = graphData?.relationships;
    const relsArray = Array.isArray(rels) ? rels : [];
    return relsArray.map((r: any) => {
      const isOutgoing = r.source === entityId;
      const neighborId = isOutgoing ? r.target : r.source;
      const nodes = graphData?.nodes;
      const nodesArray = Array.isArray(nodes) ? nodes : [];
      const neighborNode = nodesArray.find((n: any) => n.id === neighborId);
      return {
        id: r.id,
        targetId: neighborId,
        targetName: (neighborNode as any)?.label || neighborId,
        targetType: (neighborNode as any)?.type || "Unknown",
        predicate: formatPredicate(r.predicate),
        rawPredicate: r.predicate,
        epistemicStatus: r.epistemic_status,
        isCandidate: r.is_candidate
      };
    });
  }, [graphData, entityId]);

  // ── Data Extracted Truthfully ──────────────────────────────────────────────
  const { entity, subtype_data } = entityResponse || { entity: null, subtype_data: null };
  const entityType = entity?.entity_type?.toUpperCase() || 'UNKNOWN';
  const displayIdentity = deriveDisplayIdentity(entityType, subtype_data);
  const EntityIcon = getEntityIcon(entityType);
  const typeBadgeClass = ENTITY_COLOR_CLASS[entityType] || "bg-civix-surface-2 border-civix-border text-civix-text-secondary";
  const iconBorderClass = ENTITY_ICON_BORDER[entityType] || "bg-civix-surface-2 border-civix-border";
  const iconColorClass = ENTITY_ICON_COLOR[entityType] || "text-civix-text-secondary";

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">

      {/* ── Page Header ───────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-start justify-between pb-4 border-b border-civix-border gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <button
              onClick={() => setViewConnectionsMode(false)}
              className="flex items-center space-x-1.5 text-xs font-semibold text-civix-text-muted hover:text-civix-text-main transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back</span>
            </button>
            <span className="text-civix-border">/</span>
            <span className="text-xs text-civix-text-muted">Intelligence Workspace</span>
            <span className="text-civix-border">/</span>
            <span className="text-xs text-civix-text-main font-bold">Entity Dossier</span>
          </div>

          <div className="flex items-center space-x-3">
            <div className={`w-11 h-11 rounded-sm border flex items-center justify-center flex-shrink-0 shadow-sm ${iconBorderClass}`}>
              <EntityIcon className={`w-6 h-6 ${iconColorClass}`} />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h1 className="text-2xl font-extrabold text-civix-text-main tracking-tight">{displayIdentity}</h1>
                <span className={`text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-sm border uppercase tracking-wider ${typeBadgeClass}`}>
                  {entityType.replace('_', ' ')}
                </span>
              </div>
              <p className="text-[11px] text-civix-text-muted font-mono mt-0.5">
                Internal Reference: <span className="font-bold text-civix-text-secondary">{entity.entity_id}</span>
              </p>
            </div>
          </div>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2 flex-wrap flex-shrink-0">
          <button
            onClick={() => refetchEntity()}
            className="civix-btn-secondary"
            title="Refresh Dossier"
          >
            <RefreshCw className="w-3.5 h-3.5 text-civix-text-muted" />
            <span>Refresh</span>
          </button>

          {selectedCaseId ? (
            <button
              onClick={() => navigate(`/cases/${selectedCaseId}/graph`)}
              className="civix-btn-primary"
            >
              <GitFork className="w-3.5 h-3.5 text-civix-gold" />
              <span>Open Case Graph</span>
            </button>
          ) : (
            <button
              onClick={() => navigate('/cases')}
              className="civix-btn-secondary"
            >
              <Briefcase className="w-3.5 h-3.5 text-civix-text-muted" />
              <span>Select Case Context</span>
            </button>
          )}
        </div>
      </div>

      {/* ── Main 3-Column Dossier Workspace ───────────────────────────────────── */}
      <div className="flex flex-col xl:flex-row gap-6 h-[800px]">

        {/* Left Column (1/4 width): Entity Registry List */}
        <div className="w-full xl:w-1/4 h-full hidden xl:block overflow-hidden flex-shrink-0">
          <EntityRegistryList 
            entities={mappedCaseEntities} 
            isLoading={caseEntitiesLoading} 
            selectedEntityId={entityId} 
          />
        </div>

        {/* Center & Right Column Container */}
        <div className="w-full xl:w-3/4 h-full relative border border-civix-border rounded-sm bg-civix-surface">
          {viewConnectionsMode ? (
            <EntityConnectionsView 
              entityId={entity.entity_id}
              entityName={displayIdentity}
              entityType={entityType}
              relationships={connectionsForGraph}
              onBack={() => setViewConnectionsMode(false)}
            />
          ) : (
            <div className="w-full h-full overflow-y-auto p-6 custom-scrollbar">
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

                {/* Main Dossier Panels (2/3) */}
                <div className="xl:col-span-2 space-y-6">

                  {/* 1. ENTITY IDENTITY / CORE FACTS */}
                  <SectionPanel
                    title="Entity Base Record"
                    subtitle="Canonical attributes from PostgreSQL civix.entity"
                    headerRight={
                      <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border ${typeBadgeClass}`}>
                        {entityType.replace('_', ' ')}
                      </span>
                    }
                  >
                    <div className="space-y-1">
                      <AttributeRow label="Entity ID" value={entity.entity_id} icon={Hash} mono />
                      <AttributeRow label="Entity Type" value={entityType.replace('_', ' ')} icon={ShieldCheck} />
                      <AttributeRow
                        label="Registered At"
                        value={new Date(entity.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' })}
                        icon={Clock}
                        mono
                      />
                      <AttributeRow
                        label="Visibility Status"
                        value={
                          <span className="inline-flex items-center space-x-1 font-mono font-bold text-civix-green-400">
                            <Eye className="w-3 h-3 text-civix-green-400" />
                            <span>{entity.visibility_status}</span>
                          </span>
                        }
                      />
                    </div>
                  </SectionPanel>

                  {/* Subtype Attributes */}
                  <SectionPanel
                    title="Subtype Attributes"
                    subtitle={`Structured fields from civix.${entityType.toLowerCase()} — backend-provided only`}
                  >
                    {renderSubtypeSection(entityType, subtype_data)}
                  </SectionPanel>

                  {/* 2. C2 IDENTITY RESOLUTION */}
                  <SectionPanel
                    title="C2 Identity Resolution"
                    subtitle="Deterministic identity candidate links & proposed resolution signals"
                    headerRight={
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-gold-950/40 border-civix-gold-600/40 text-civix-gold-400">
                        {matchingCandidates.length} CANDIDATES
                      </span>
                    }
                  >
                    {matchingCandidates.length > 0 ? (
                      <div className="space-y-4">
                        <div className="bg-civix-gold-950/40 border border-civix-gold-600/40 rounded-sm p-3 space-y-1">
                          <div className="flex items-center space-x-1.5 text-civix-gold-400 font-bold text-xs">
                            <ShieldAlert className="w-4 h-4 text-civix-gold-500 flex-shrink-0" />
                            <span>INSTITUTIONAL RESOLUTION DISCLAIMER</span>
                          </div>
                          <p className="text-[11px] text-civix-text-secondary leading-relaxed font-medium">
                            Identity candidate relationships are proposed deterministic matches. They are <strong>NOT CONFIRMED RESOLUTIONS</strong>.
                            CIVIX strictly enforces that candidate links do not auto-merge entities into a single identity profile without manual supervisor review.
                          </p>
                        </div>

                        <div className="space-y-3">
                          {matchingCandidates.map((cand) => (
                            <div key={cand.candidate_id} className="border border-civix-border rounded-sm bg-civix-surface p-3 space-y-2">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-gold-950/60 border-civix-gold-600/50 text-civix-gold-400">
                                    POSSIBLE / CANDIDATE
                                  </span>
                                  <span className="text-xs font-mono font-bold text-civix-text-main">{cand.matching_rule_id}</span>
                                </div>
                                <span className="text-[10px] font-mono text-civix-text-muted">
                                  {new Date(cand.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'short', timeStyle: 'short' })}
                                </span>
                              </div>

                              <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                                <div>
                                  <p className="text-[9px] font-bold text-civix-text-muted uppercase">Candidate ID</p>
                                  <p className="text-[10px] text-civix-text-secondary truncate">{cand.candidate_id}</p>
                                </div>
                                <div>
                                  <p className="text-[9px] font-bold text-civix-text-muted uppercase">Source Identity ID</p>
                                  <p className="text-[10px] text-civix-text-secondary truncate">{cand.source_identity_id}</p>
                                </div>
                              </div>

                              <div>
                                <p className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider mb-1">Deterministic Matching Signals</p>
                                <div className="flex flex-wrap gap-1">
                                  {cand.deterministic_signals.map((sig) => (
                                    <span key={sig} className="text-[9px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-surface-2 border-civix-border text-civix-text-secondary">
                                      {sig}
                                    </span>
                                  ))}
                                </div>
                              </div>

                              {cand.supporting_evidence_ids && cand.supporting_evidence_ids.length > 0 && (
                                <div className="pt-1">
                                  <p className="text-[9px] font-bold text-civix-text-muted uppercase tracking-wider mb-1">Supporting Evidence IDs</p>
                                  <div className="flex flex-wrap gap-1">
                                    {cand.supporting_evidence_ids.map((eid) => (
                                      <span key={eid} className="text-[9px] font-mono px-1.5 py-0.5 rounded-sm bg-civix-surface-2 text-civix-text-muted">
                                        {eid.substring(0, 8)}...
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <TruthfulEmptyState
                        title="NO IDENTITY CANDIDATES"
                        description="No C2 identity candidate matching records exist for this entity in the identity candidate repository."
                      />
                    )}
                  </SectionPanel>
                </div>

                {/* Right Column (1/3 width): Intelligence & Leads */}
                <div className="space-y-6">

                  {/* NETWORK / CONNECTIONS BUTTON PANEL */}
                  <div className="civix-panel rounded-sm overflow-hidden p-6 bg-gradient-to-b from-civix-surface-2 to-civix-surface border-civix-blue-900/40">
                    <h3 className="text-sm font-bold text-white uppercase tracking-widest font-mono flex items-center mb-2">
                      <Network className="w-4 h-4 mr-2 text-civix-blue-400" />
                      ENTITY GRAPH
                    </h3>
                    <p className="text-[11px] text-civix-text-muted mb-4 leading-relaxed">
                      Visualize 1-hop connections, authoritative links, and ML-generated identity leads directly connected to this entity.
                    </p>
                    <button 
                      onClick={() => setViewConnectionsMode(true)}
                      className="w-full civix-btn-primary py-2.5 flex justify-center bg-civix-blue-600 hover:bg-civix-blue-500 border-civix-blue-400 text-white shadow-lg"
                    >
                      <GitFork className="w-4 h-4 mr-2" />
                      <span>OPEN CONNECTIONS VIEW</span>
                    </button>
                    <div className="mt-3 text-center">
                      <span className="text-[10px] font-mono text-civix-text-secondary uppercase">
                        {graphData?.nodes?.length || 0} Nodes • {graphData?.relationships?.length || 0} Relationships
                      </span>
                    </div>
                  </div>

                  {/* 3. CASE INVOLVEMENT */}
                  <SectionPanel
                    title="Case Involvement"
                    subtitle="Officially linked investigatory records via entity roles"
                    headerRight={
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-surface-2 border-civix-border text-civix-text-secondary">
                        {casesList?.length || 0} CASES
                      </span>
                    }
                  >
                    {casesList && casesList.length > 0 ? (
                      <div className="divide-y divide-civix-border">
                        {casesList.map((c) => (
                          <div key={(c as any).case_id} className="py-3 first:pt-0 last:pb-0">
                            <div className="flex justify-between items-start mb-1">
                              <span className="text-xs font-mono font-bold text-civix-blue-400 tracking-wider">
                                {(c as any).case_number}
                              </span>
                              <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm border uppercase ${
                                (c as any).status.includes('CLOSED') ? 'bg-civix-surface-3 border-civix-border text-civix-text-muted'
                                : 'bg-civix-green-950/40 border-civix-green-600/40 text-civix-green-400'
                              }`}>
                                {(c as any).status.replace('_', ' ')}
                              </span>
                            </div>
                            <h4 className="text-xs font-sans text-civix-text-main font-semibold mb-2">{(c as any).title}</h4>
                            <div className="flex items-center justify-between mt-2">
                              <span className="text-[10px] font-mono px-2 py-0.5 bg-civix-gold/20 text-civix-gold border border-civix-gold/40 rounded-xs uppercase">
                                {(c as any).role || 'SUBJECT'}
                              </span>
                              <button
                                onClick={() => navigate(`/cases/${(c as any).case_id}`)}
                                className="flex items-center space-x-1 text-[10px] font-mono text-civix-text-secondary hover:text-white transition-colors"
                              >
                                <span>VIEW CASE</span>
                                <ExternalLink className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <TruthfulEmptyState
                        title="NO CASE LINKS"
                        description="This entity is not actively linked to any cases in the registry."
                        icon={Briefcase}
                      />
                    )}
                  </SectionPanel>

                  {/* 4. EVIDENCE INVOLVEMENT */}
                  <SectionPanel
                    title="Evidence Records"
                    subtitle="Physical, digital, and trace evidence linked directly to this entity"
                    headerRight={
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-surface-2 border-civix-border text-civix-text-secondary">
                        {evidenceData?.length || 0} ITEMS
                      </span>
                    }
                  >
                    {evidenceData && evidenceData.length > 0 ? (
                      <div className="grid grid-cols-1 gap-3">
                        {evidenceData.map((ev) => (
                          <div key={(ev as any).evidence_id} className="border border-civix-border rounded-sm bg-civix-surface p-3 flex items-start space-x-3">
                            <div className="w-8 h-8 rounded-sm bg-civix-surface-3 flex items-center justify-center flex-shrink-0 border border-civix-border">
                              <FileText className="w-4 h-4 text-civix-text-muted" />
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="text-xs font-semibold text-civix-text-main truncate">{(ev as any).title || (ev as any).original_filename || 'Evidence Record'}</p>
                              <div className="flex items-center space-x-2 mt-1">
                                <span className="text-[9px] font-mono text-civix-text-secondary uppercase">{(ev as any).evidence_type}</span>
                                <span className="text-civix-border">•</span>
                                <span className="text-[9px] font-mono text-civix-text-muted truncate">{(ev as any).evidence_id.substring(0, 8)}...</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <TruthfulEmptyState
                        title="NO EVIDENCE"
                        description="No evidence artifacts are currently linked to this entity."
                        icon={FileText}
                      />
                    )}
                  </SectionPanel>

                  {/* AI INVESTIGATIVE LEADS */}
                  <SectionPanel
                    title="Intelligence Leads"
                    subtitle="ML-surfaced associative signals"
                    headerRight={
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-gold-950/40 border-civix-gold-600/40 text-civix-gold-400">
                        {targetLeads.length} LEADS
                      </span>
                    }
                  >
                    {targetLeads.length > 0 ? (
                      <div className="space-y-4">
                        <div className="bg-civix-gold-950/40 border border-civix-gold-600/40 rounded-sm p-3">
                          <div className="flex items-start space-x-2 text-civix-gold-400 font-bold text-[10px] uppercase tracking-wider mb-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-civix-gold flex-shrink-0 mt-0.5" />
                            <span>MODEL OUTPUT — NOT CONFIRMATION</span>
                          </div>
                          <p className="text-[11px] text-civix-text-secondary leading-relaxed font-medium">
                            The following leads are generated by the Behavioral Link Prediction Engine.
                            They require investigator validation and ground truth evidence gathering.
                          </p>
                        </div>
                        <div className="space-y-3">
                          {targetLeads.map(lead => (
                            <div key={lead.lead_id} className="border-l-2 border-civix-gold/60 pl-3 py-1 space-y-1.5 bg-civix-surface-2/50 p-2 rounded-r-sm">
                              <div className="flex justify-between items-center">
                                <span className="text-[10px] font-mono font-bold text-civix-text-secondary uppercase">LEAD {lead.lead_id.substring(0, 8)}</span>
                                <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm ${lead.priority === 'HIGH' || lead.priority === 'CRITICAL' ? 'bg-civix-red-950/40 border border-civix-red-600/40 text-civix-red-400' : 'bg-civix-surface-3 border border-civix-border text-civix-text-secondary'}`}>
                                  {lead.priority || 'MEDIUM'}
                                </span>
                              </div>
                              <p className="text-xs text-civix-text-main font-sans leading-relaxed">{lead.lead_text}</p>
                              {lead.ai_confidence && (
                                <div className="flex items-center space-x-2 pt-1">
                                  <span className="text-[9px] font-mono text-civix-text-muted uppercase">Confidence</span>
                                  <div className="w-16 h-1 bg-civix-surface-3 rounded-full overflow-hidden">
                                    <div className="h-full bg-civix-gold" style={{ width: `${lead.ai_confidence * 100}%` }} />
                                  </div>
                                  <span className="text-[9px] font-mono text-civix-gold font-bold">{(lead.ai_confidence * 100).toFixed(0)}%</span>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <TruthfulEmptyState
                        title="NO ML LEADS"
                        description="The behavioral engine has not surfaced any investigative leads specific to this entity."
                        icon={Zap}
                      />
                    )}
                  </SectionPanel>

                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
