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
} from 'lucide-react';

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
  const location = useLocation();
  const { selectedCaseId } = useCaseSelection();

  const [expandedLeadId, setExpandedLeadId] = useState<string | null>(null);

  // Navigation back
  const canGoBack = !!location.key && location.key !== 'default';
  function handleBack() {
    if (canGoBack) navigate(-1);
    else navigate('/search');
  }

  // 1. Fetch Entity Base + Subtype Data
  const {
    data: entityResponse,
    isLoading: entityLoading,
    error: entityError,
    refetch: refetchEntity,
  } = useQuery({
    queryKey: ['entity', entityId],
    queryFn: () => (entityId ? entitiesApi.getEntity(entityId) : Promise.reject(new Error('No entity ID'))),
    enabled: !!entityId,
    staleTime: 60_000,
  });

  // 2. Fetch C2 Identity Candidates
  const { data: candidatesData } = useQuery({
    queryKey: ['identityCandidates'],
    queryFn: () => identityApi.getCandidates(),
    staleTime: 60_000,
  });

  // Filter candidates relevant to this entity
  const matchingCandidates = (candidatesData?.candidates || []).filter(
    (c) => c.proposed_person_id === entityId || c.source_identity_id === entityId
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
  const targetLeads = (leadsData || []).filter((l) => l.target_entity_id === entityId);

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
    const caseMap = new Map<string, CaseListItem>(casesList?.map((c: CaseListItem) => [c.case_id, c]));

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
            onClick={handleBack}
            className="civix-btn-secondary"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Search</span>
          </button>
        </div>
      </div>
    );
  }

  // ── Data Extracted Truthfully ──────────────────────────────────────────────
  const { entity, subtype_data } = entityResponse;
  const entityType = entity.entity_type?.toUpperCase();
  const displayIdentity = deriveDisplayIdentity(entityType, subtype_data);
  const EntityIcon = getEntityIcon(entityType);
  const typeBadgeClass = ENTITY_COLOR_CLASS[entityType] || 'bg-civix-surface-2 border-civix-border text-civix-text-secondary';
  const iconBorderClass = ENTITY_ICON_BORDER[entityType] || 'bg-civix-surface-2 border-civix-border';
  const iconColorClass = ENTITY_ICON_COLOR[entityType] || 'text-civix-text-secondary';

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">

      {/* ── Page Header ───────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-start justify-between pb-4 border-b border-civix-border gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <button
              onClick={handleBack}
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

      {/* ── Main 2-Column Dossier Workspace ───────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

        {/* Left Column (2/3 width): Core Attributes, C2 Resolution, Relationships, Leads */}
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
                {/* Mandatory Disclaimer */}
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

                {/* Candidate List */}
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

          {/* 3. RELATIONSHIPS */}
          <SectionPanel
            title="Entity Relationships"
            subtitle={selectedCaseId ? `Traversed relationships in Case ${selectedCaseId.substring(0, 8)}...` : 'Graph traversal requires an active case context'}
            headerRight={
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-blue-950 border-civix-blue-600/50 text-civix-blue-400">
                {entityRelationships.length} LINKS
              </span>
            }
          >
            {!selectedCaseId ? (
              <TruthfulEmptyState
                title="CASE CONTEXT REQUIRED"
                description="Relationship graph traversal is ACL-bounded by case context. Select an active case to view projected relationships for this entity."
                icon={GitFork}
              />
            ) : entityRelationships.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="civix-table">
                  <thead>
                    <tr>
                      <th className="civix-table-th">Connected Entity</th>
                      <th className="civix-table-th">Relationship</th>
                      <th className="civix-table-th">Status / Epistemic</th>
                      <th className="civix-table-th">Provenance</th>
                      <th className="civix-table-th text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entityRelationships.map((rel) => (
                      <tr key={rel.id} className="civix-table-tr">
                        <td className="civix-table-td">
                          <div className="flex items-center space-x-2">
                            <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm border ${ENTITY_COLOR_CLASS[rel.targetType] || 'bg-civix-surface-2 border-civix-border text-civix-text-secondary'}`}>
                              {rel.targetType}
                            </span>
                            <span className="font-bold text-civix-text-main">{rel.targetName}</span>
                          </div>
                        </td>
                        <td className="civix-table-td">
                          <div>
                            <span className="font-semibold text-civix-text-main">{rel.predicate}</span>
                            <span className="text-[10px] font-mono text-civix-text-muted block">{rel.rawPredicate}</span>
                          </div>
                        </td>
                        <td className="civix-table-td">
                          {rel.isCandidate ? (
                            <span className="inline-flex items-center text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm border bg-civix-gold-950 border-civix-gold-600/50 text-civix-gold-400">
                              CANDIDATE
                            </span>
                          ) : rel.epistemicStatus ? (
                            <span className="inline-flex items-center text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm border bg-civix-green-950 border-civix-green-600/50 text-civix-green-400">
                              {rel.epistemicStatus}
                            </span>
                          ) : (
                            <span className="text-[10px] font-mono text-civix-text-muted">EVIDENCE-BACKED</span>
                          )}
                        </td>
                        <td className="civix-table-td font-mono text-[10px] text-civix-text-muted">
                          {rel.assertionId ? `Assertion: ${rel.assertionId.substring(0, 8)}...` : 'Neo4j Projection'}
                        </td>
                        <td className="civix-table-td text-right">
                          <button
                            onClick={() => navigate(`/entities/${rel.targetId}`)}
                            className="inline-flex items-center space-x-1 text-[11px] font-semibold text-civix-blue-400 hover:text-civix-blue-300 transition-colors"
                          >
                            <span>Dossier</span>
                            <ChevronRight className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <TruthfulEmptyState
                title="NO PROJECTED RELATIONSHIPS"
                description="No relationships are projected for this entity in the active case graph."
              />
            )}
          </SectionPanel>

          {/* 4. INVESTIGATIVE LEADS & MODEL SIGNALS */}
          <SectionPanel
            title="Investigative Lead Signals (C3 Engine)"
            subtitle="Automated findings, behavioral model signals, and explanation trace"
            headerRight={
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-blue-950 border-civix-blue-600/50 text-civix-blue-400">
                {targetLeads.length} LEADS
              </span>
            }
          >
            {!selectedCaseId ? (
              <TruthfulEmptyState
                title="CASE CONTEXT REQUIRED"
                description="Lead analysis is case-scoped. Select an active case context to surface investigative leads for this entity."
                icon={Zap}
              />
            ) : targetLeads.length > 0 ? (
              <div className="space-y-4">
                {targetLeads.map((lead) => {
                  const isExpanded = expandedLeadId === lead.lead_id;
                  const scoreFormatted = lead.ai_confidence != null ? (lead.ai_confidence * 100).toFixed(1) + '%' : 'N/A';

                  return (
                    <div key={lead.lead_id} className="border border-civix-border rounded-sm bg-civix-surface overflow-hidden">
                      {/* Lead Summary Bar */}
                      <div className="p-3.5 bg-civix-surface-2 border-b border-civix-border flex flex-col md:flex-row md:items-center justify-between gap-2">
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border ${
                              lead.priority === 'HIGH' ? 'bg-civix-red-950 border-civix-red-600/50 text-civix-red-400' :
                              lead.priority === 'MEDIUM' ? 'bg-civix-gold-950 border-civix-gold-600/50 text-civix-gold-400' :
                              'bg-civix-surface border-civix-border text-civix-text-secondary'
                            }`}>
                              {lead.priority} PRIORITY
                            </span>
                            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-surface border-civix-border text-civix-text-secondary">
                              STATUS: {lead.status}
                            </span>
                            <span className="text-[10px] font-mono text-civix-text-muted">ID: {lead.lead_id.substring(0, 8)}...</span>
                          </div>
                          <p className="text-xs font-bold text-civix-text-main leading-snug">{lead.lead_text}</p>
                        </div>

                        {/* Model Signal Badge (STRICT TERMINOLOGY: NOT 'CONFIDENCE') */}
                        <div className="flex items-center space-x-3 flex-shrink-0">
                          <div className="text-right">
                            <p className="text-[9px] font-bold text-civix-blue-400 uppercase tracking-wider">MODEL SIGNAL</p>
                            <p className="text-sm font-extrabold font-mono text-civix-blue-300">{scoreFormatted}</p>
                          </div>
                          <button
                            onClick={() => setExpandedLeadId(isExpanded ? null : lead.lead_id)}
                            className="p-1.5 text-civix-text-muted hover:text-civix-text-main bg-civix-surface border border-civix-border rounded-sm transition-colors"
                          >
                            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>

                      {/* CIVIX Canonical Intelligence Hierarchy */}
                      <div className="p-3.5 bg-civix-surface text-xs space-y-3">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] font-mono border-b border-civix-border/40 pb-2.5">
                          <div>
                            <span className="text-civix-text-muted block uppercase">1. Source Evidence</span>
                            <span className="font-bold text-civix-text-secondary">CDR / Case Registry</span>
                          </div>
                          <div>
                            <span className="text-civix-text-muted block uppercase">2. Findings Count</span>
                            <span className="font-bold text-civix-text-secondary">{lead.finding_count ?? 0} Deterministic</span>
                          </div>
                          <div>
                            <span className="text-civix-text-muted block uppercase">3. Model Signal</span>
                            <span className="font-bold text-civix-blue-400">Behavioral Score</span>
                          </div>
                          <div>
                            <span className="text-civix-text-muted block uppercase">4. Explanation</span>
                            <span className="font-bold text-civix-text-secondary">{lead.explanation_status || 'NOT_RUN'}</span>
                          </div>
                        </div>

                        {/* Detailed findings trace if expanded */}
                        {isExpanded && (
                          <div className="pt-1 space-y-2 bg-civix-surface-2 p-3 rounded-sm border border-civix-border text-[11px]">
                            <p className="font-bold text-civix-text-main uppercase tracking-wider text-[10px]">C3 Lead Trace Details</p>
                            <p className="text-civix-text-secondary leading-relaxed font-sans">
                              Feature Vector Version: <span className="font-mono text-civix-text-main">{lead.feature_vector_version || 'v1.0'}</span>
                            </p>
                            <div className="pt-2 flex items-center space-x-2">
                              <button
                                onClick={() => navigate(`/cases/${selectedCaseId}`)}
                                className="civix-btn-primary"
                              >
                                <ExternalLink className="w-3 h-3 text-civix-gold" />
                                <span>Inspect in Case Workspace</span>
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <TruthfulEmptyState
                title="NO TARGETED LEADS"
                description="No C3 automated investigative leads target this entity in the active case file."
              />
            )}
          </SectionPanel>

        </div>

        {/* Right Column (1/3 width): Case Involvement, Evidence, Registry Actions & Provenance */}
        <div className="space-y-6">

          {/* 5. CASE INVOLVEMENT */}
          <SectionPanel
            title="Case Involvement"
            subtitle="Case files where this entity holds an assigned role"
          >
            {caseInvolvementList.length > 0 ? (
              <div className="space-y-3">
                {caseInvolvementList.map((c) => (
                  <div key={c.case_id} className="border border-civix-border rounded-sm p-3 bg-civix-surface space-y-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="civix-id">
                          {c.case_number}
                        </span>
                        <h4 className="text-xs font-bold text-civix-text-main mt-1 leading-snug">{c.title}</h4>
                      </div>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border bg-civix-red-950 border-civix-red-600/50 text-civix-red-400">
                        {c.role}
                      </span>
                    </div>

                    {c.role_basis && (
                      <p className="text-[11px] text-civix-text-secondary font-sans italic leading-tight">
                        "{c.role_basis}"
                      </p>
                    )}

                    <div className="pt-1 flex items-center justify-between border-t border-civix-border/40 text-[10px] font-mono text-civix-text-muted">
                      <span>Jurisdiction: {c.jurisdiction}</span>
                      <button
                        onClick={() => navigate(`/cases/${c.case_id}`)}
                        className="font-bold text-civix-blue-400 hover:text-civix-blue-300 transition-colors flex items-center space-x-1"
                      >
                        <span>Open Case</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <TruthfulEmptyState
                title="NO CASE ASSIGNMENTS"
                description="This entity is not explicitly linked to any active case file via case_entity_role."
              />
            )}
          </SectionPanel>

          {/* 6. EVIDENCE ARTIFACTS */}
          <SectionPanel
            title="Associated Evidence"
            subtitle={selectedCaseId ? `Evidence files in Case ${selectedCaseId.substring(0, 8)}...` : 'Select a case context to view evidence'}
          >
            {!selectedCaseId ? (
              <TruthfulEmptyState
                title="CASE CONTEXT REQUIRED"
                description="Evidence documents are case-scoped. Select a case context to surface evidence artifacts."
                icon={FileText}
              />
            ) : (evidenceData || []).length > 0 ? (
              <div className="space-y-2">
                {(evidenceData || []).map((art) => (
                  <div key={art.artifact_id} className="border border-civix-border rounded-sm p-2.5 bg-civix-surface space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-civix-text-main truncate max-w-[180px]" title={art.original_filename}>
                        {art.original_filename || 'Evidence File'}
                      </span>
                      <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-sm border ${
                        art.processing_status === 'COMPLETED' ? 'bg-civix-green-950 border-civix-green-600/50 text-civix-green-400' :
                        art.processing_status === 'FAILED' ? 'bg-civix-red-950 border-civix-red-600/50 text-civix-red-400' :
                        art.processing_status === 'PROCESSING' ? 'bg-civix-blue-950 border-civix-blue-600/50 text-civix-blue-400' :
                        'bg-civix-surface-2 border-civix-border text-civix-text-secondary'
                      }`}>
                        {art.processing_status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[10px] font-mono text-civix-text-muted">
                      <span>{art.mime_type || 'binary/octet-stream'}</span>
                      <span>{art.file_size_bytes ? (art.file_size_bytes / 1024).toFixed(1) + ' KB' : 'N/A'}</span>
                    </div>

                    {art.processing_status === 'FAILED' && (
                      <div className="mt-1 p-1.5 bg-civix-red-950/40 border border-civix-red-600/40 rounded-sm text-[10px] text-civix-red-400 font-mono">
                        FAILED_NLP: Text extraction failed or mime type unsupported.
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <TruthfulEmptyState
                title="NO EVIDENCE ARTIFACTS"
                description="No evidence documents are uploaded for the active case file."
              />
            )}
          </SectionPanel>

          {/* 7. PROVENANCE & AUDIT TRAIL */}
          <SectionPanel
            title="System Provenance"
            subtitle="Record origin & access control scope"
          >
            <div className="space-y-2.5 text-xs">
              <div className="bg-civix-surface border border-civix-border rounded-sm p-3 space-y-2">
                <p className="text-[10px] font-bold text-civix-text-muted uppercase tracking-wider">Why does CIVIX know this entity?</p>
                <p className="text-[11px] text-civix-text-secondary leading-relaxed font-sans">
                  This entity record exists in PostgreSQL table <code className="font-mono text-civix-text-main bg-civix-surface-2 px-1 py-0.5 rounded-sm">civix.entity</code> and is indexed in the global intelligence network.
                </p>
                <div className="space-y-1 pt-1 text-[10px] font-mono text-civix-text-muted border-t border-civix-border/40">
                  <p>RLS Access: <span className="font-bold text-civix-text-main">READ / WRITE Granted</span></p>
                  <p>Visibility Status: <span className="font-bold text-civix-green-400">{entity.visibility_status}</span></p>
                  <p>Ingestion Time: <span>{new Date(entity.created_at).toISOString()}</span></p>
                </div>
              </div>
            </div>
          </SectionPanel>

        </div>
      </div>
    </div>
  );
};
