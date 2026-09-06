/**
 * CIVIX 2.0 — Canonical TypeScript API Contracts
 * Strictly mirrors backend FastAPI Pydantic models in civix_api/models/
 */

export interface AuthenticatedUser {
  user_id: string;
  username: string;
  display_name: string;
  role: string;
  clearance_level: number;
  external_auth_id?: string;
}

export interface CaseListItem {
  case_id: string;
  case_number: string;
  title: string;
  case_type: string;
  status: string;
  priority: string;
  jurisdiction: string;
  investigating_unit?: string | null;
  opened_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  fir_number?: string | null;
  police_station?: string | null;
  district?: string | null;
  sections_invoked?: string[] | null;
}

export interface CaseRegistryItem {
  case_id: string;
  case_number: string;
  title: string;
  description?: string | null;
  case_type: string;
  status: string;
  priority: string;
  jurisdiction: string;
  police_station: string;
  provenance: 'GOLDEN' | 'SYNTHETIC' | string;
  source_type: string;
  entity_count: number;
  evidence_count: number;
  event_count: number;
  lead_count: number;
  last_activity_at: string;
  created_at: string;
  updated_at: string;
}

export interface CaseRegistryPagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface CaseRegistrySummary {
  total_cases: number;
  active_cases: number;
  critical_cases: number;
  golden_cases: number;
  synthetic_cases: number;
  updated_today: number;
}

export interface CaseRegistryResponse {
  items: CaseRegistryItem[];
  pagination: CaseRegistryPagination;
  summary: CaseRegistrySummary;
}

export interface CaseRegistryParams {
  page?: number;
  page_size?: number;
  search?: string;
  case_type?: string;
  status?: string;
  priority?: string;
  jurisdiction?: string;
  provenance?: string;
  sort_by?: string;
  sort_order?: string;
}

export interface CaseCreateRequest {
  case_number: string;
  title: string;
  case_type: string;
  jurisdiction: string;
  priority?: string;
  investigating_unit?: string;
}

export interface CaseEntityRoleRequest {
  entity_id: string;
  role: string;
  role_basis?: string;
}

export interface CaseEntityRoleResponse {
  role_id: string;
  case_id: string;
  entity_id: string;
  role: string;
  role_basis?: string;
  assigned_by?: string;
  valid_from?: string;
  valid_to?: string;
}

export interface CaseEntityRoleListItem {
  role_id: string;
  entity_id: string;
  role: string;
  role_basis?: string;
  entity_type: string;
  display_name: string;
  gender?: string | null;
  date_of_birth?: string | null;
  nationality?: string | null;
  avatar_url?: string | null;
}

export interface EntityBase {
  entity_id: string;
  entity_type: 'PERSON' | 'DEVICE' | 'ORGANIZATION' | 'PHONE_NUMBER' | 'SOURCE_IDENTITY' | string;
  created_at: string;
  visibility_status: string;
}

export interface EntityResponse {
  entity: EntityBase;
  subtype_data: Record<string, any>;
}

export interface SearchResultItem {
  entity_id: string;
  entity_type: string;
  display_label: string;
  matched_field: string;
}

export interface SearchResponse {
  results: SearchResultItem[];
  limit: number;
  offset: number;
}

export interface GraphNode {
  id: string;
  labels: string[];
  properties: Record<string, any>;
}

export interface GraphRelationship {
  id: string;
  type: string;
  start_node: string;
  end_node: string;
  properties: Record<string, any>;
}

export interface GraphMetadata {
  requested_depth: number;
  max_depth: number;
  node_limit: number;
  relationship_limit: number;
  nodes_returned: number;
  relationships_returned: number;
  truncated: boolean;
}

export interface GraphResponse {
  nodes: GraphNode[];
  relationships: GraphRelationship[];
  metadata?: GraphMetadata;
}

export interface EvidenceUploadResponse {
  artifact_id: string;
  instance_id: string;
  original_filename: string;
  mime_type: string;
  sha256_hash: string;
  file_size_bytes: number;
  processing_status: 'STORED' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | string;
  is_duplicate: boolean;
  message: string;
}

export interface EvidenceStatusResponse {
  artifact_id: string;
  instance_id: string;
  original_filename?: string;
  mime_type?: string;
  file_size_bytes?: number;
  processing_status: string;
  processed_at?: string;
  processing_error?: string;
  media_metadata?: Record<string, any>;
  case_id: string;
  acquired_by?: string;
  acquisition_method?: string;
  created_at: string;
  sha256_hash?: string;
  storage_uri?: string;
}

export interface EvidenceListItem {
  artifact_id: string;
  instance_id: string;
  original_filename?: string;
  mime_type?: string;
  file_size_bytes?: number;
  processing_status: string;
  created_at: string;
  evidence_type?: string | null;
  evidence_title?: string | null;
  sha256_hash?: string;
  storage_uri?: string;
}

export interface InvestigativeLeadResponse {
  lead_id: string;
  case_id: string;
  target_entity_id: string;
  hypothesis_id?: string;
  generated_by_run_id?: string;
  generated_by_person?: string;
  ai_confidence?: number;
  lead_text: string;
  priority: string;
  status: 'OPEN' | 'IN_PROGRESS' | 'CONFIRMED' | 'FALSE_POSITIVE' | 'CLOSED' | 'DEFERRED' | string;
  explanation_status?: string;
  feature_vector_version?: string;
  finding_count?: number;
  findings?: Array<{
    finding_id: string;
    finding_text: string;
    predicate?: string;
  }>;
}


export interface GenerateLeadsResponse {
  case_id: string;
  model_version: string;
  feature_vector_version: string;
  limitations: string[];
  leads: InvestigativeLeadResponse[];
  message?: string;
}

export interface FindingResponse {
  finding_id: string;
  finding_type: string;
  subject_entity_id: string;
  object_entity_id?: string;
  relationship_strength: string;
  key_facts: string[];
  path_description?: string;
  hop_count: number;
  matching_rule_id?: string;
  suppressed: boolean;
  suppression_reason?: string;
}

export interface LeadExplanationResponse {
  lead_id: string;
  explanation_status: string;
  explanation?: Record<string, any> | null;
  ml_score?: number | null;
  feature_vector_version?: string;
  lead_text: string;
  note: string;
}

export interface LeadProvenanceResponse {
  lead_id: string;
  subject_name: string;
  provenance_chain: {
    '1_lead': { lead_id: string; explanation_status: string };
    '2_ml_score': {
      score?: number | null;
      model_name?: string;
      model_version?: string;
      feature_vector_version?: string;
      run_at?: string | null;
    };
    '3_deterministic_findings': Array<{
      finding_id: string;
      finding_type: string;
      path_description?: string;
      hop_count: number;
      matching_rule_id?: string;
      suppressed: boolean;
      key_facts: string[];
      evidence_ids: string[];
    }>;
  };
  provenance_note: string;
}

export interface LeadDispositionRequest {
  status: 'OPEN' | 'IN_PROGRESS' | 'CONFIRMED' | 'FALSE_POSITIVE' | 'CLOSED' | 'DEFERRED' | string;
  disposition_notes: string;
}

export interface IdentityCandidate {
  candidate_id: string;
  source_identity_id: string;
  proposed_person_id: string;
  matching_rule_id: string;
  deterministic_signals: string[];
  supporting_evidence_ids: string[];
  created_at: string;
}

export interface IdentityCandidatesResponse {
  candidates: IdentityCandidate[];
}

