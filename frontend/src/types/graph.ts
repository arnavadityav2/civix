import type { GraphNode, GraphRelationship } from './api';

export type WorkspaceMode = 'EXPLORE' | 'SEE_THREAD' | 'FIND_PATH' | 'FOCUS' | 'CONNECT_ENTITY';

export type EpistemicStatus = 
  | 'VERIFIED'
  | 'SYSTEM_DERIVED'
  | 'PROPOSED'
  | 'ACCEPTED_BY_SUPERVISOR'
  | 'REJECTED';

export const ALLOWED_INVESTIGATOR_PREDICATES = [
  "CALLED",
  "MESSAGED",
  "CO_LOCATED",
  "REGISTERED_TO",
  "OWNED_BY",
  "DRIVER_OF",
  "OWNS",
  "MEMBER_OF",
  "EMPLOYED_BY",
  "ASSOCIATED_WITH",
  "KNOWN_ASSOCIATE_OF",
  "OBSERVED_AT",
  "LINKED_TO",
  "TRANSFERRED_TO",
  "RECEIVED_FROM",
  "PARTICIPATED_IN",
  "RELATED_TO",
  "ALIAS_OF",
  "LIVES_AT",
  "WORKS_AT",
  "OPERATES",
  "CONTROLS",
  "FINANCES",
  "DIRECTED_BY",
  "HAS_SIM",
  "USES_DEVICE",
  "SAME_VEHICLE_AS",
  "TRANSACTED_WITH",
  "PRESENT_AT",
] as const;

export type InvestigatorPredicate = typeof ALLOWED_INVESTIGATOR_PREDICATES[number];

export interface ProposedAssertionPayload {
  subject_entity_id: string;
  predicate: string;
  object_entity_id: string;
  investigator_justification: string;
  evidence_instance_ids?: string[];
}

export interface AssertionProposalResponse {
  assertion_id: string;
  case_id: string;
  subject_entity_id: string;
  predicate: string;
  object_entity_id: string;
  assertion_origin: string;
  proposal_status: string;
  epistemic_status: string;
  investigator_justification: string;
  asserted_by?: string;
  created_at: string;
  message: string;
}

export interface ReviewAssertionPayload {
  decision: 'ACCEPT' | 'REJECT';
  review_notes?: string;
}

export interface ReviewAssertionResponse {
  assertion_id: string;
  previous_status: string;
  new_status: string;
  reviewed_by: string;
  reviewed_at: string;
  message: string;
}

export interface ProposedAssertionListItem {
  assertion_id: string;
  subject_entity_id: string;
  predicate: string;
  object_entity_id: string;
  investigator_justification: string;
  asserted_by?: string;
  created_at: string;
  proposal_status: string;
}

export interface InvestigationTrailItem {
  id: string;
  label: string;
  type: string;
  timestamp: string;
}

export interface GraphFilterState {
  searchQuery: string;
  selectedEntityTypes: Set<string>;
  selectedRelTypes: Set<string>;
  showHidden: boolean;
}

export type UniverseScopeMode = 'CASE_ANCHORED' | 'FULL_CONNECTED_UNIVERSE';

export interface MacroClusterSummary {
  caseClusterCount: number;
  bridgeHubCount: number;
  totalEntities: number;
  totalRelationships: number;
}

