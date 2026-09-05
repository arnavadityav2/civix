/**
 * CIVIX 2.0 — CDR & Tower Intelligence API Contract
 * frontend/src/api/telecom.ts
 *
 * Data Contract Truth (from Phase A Audit, 2026-09-05):
 * - CALL events: CALLER/CALLEE MSISDN available ✓
 * - DEVICE_PING events: location linkage for 37/249 events ✓
 * - IMSI: NOT available (all NULL in database)
 * - SIM↔DEVICE links: NOT available (sim_in_device = 0 rows)
 * - SIM↔MSISDN links: NOT available (sim_number_assignment = 0 rows)
 * - SIM swap detection: NOT AVAILABLE
 * - Cross-case telecom: NOT AVAILABLE (0 shared telecom entities)
 * - Neo4j: OFFLINE — PostgreSQL-only
 *
 * All interfaces reflect REAL data availability.
 * No fake fields. No hardcoded fallback values.
 */

import { apiClient } from './client';

// ─── Data Quality Flags ──────────────────────────────────────────────────────

export interface TelecomDataQualityFlags {
  imei_available: boolean;
  imsi_available: boolean;
  sim_available: boolean;
  location_is_cell_sector?: boolean;
  note: string;
}

// ─── Pagination ──────────────────────────────────────────────────────────────

export interface TelecomPagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// ─── Case Telecom Events ─────────────────────────────────────────────────────

export interface TelecomEventItem {
  event_id: string;
  event_type: 'CALL' | 'DEVICE_PING' | 'MESSAGE';
  /** ISO 8601 — lower bound of occurred_at TSTZRANGE */
  start: string | null;
  /** ISO 8601 — upper bound of occurred_at TSTZRANGE */
  end: string | null;
  /** Derived: upper - lower in seconds */
  duration_seconds: number | null;
  description: string | null;

  // CALL-specific (from event_participant role=CALLER/CALLEE)
  caller_msisdn: string | null;
  caller_operator: string | null;
  callee_msisdn: string | null;
  callee_operator: string | null;

  // DEVICE_PING-specific (from event_participant role=SUBJECT)
  subject_msisdn: string | null;

  // NOT AVAILABLE in current dataset (sim_in_device = 0, sim_number_assignment = 0)
  imei: null;
  imsi: null;

  // Location (from event_location → location)
  location_id: string | null;
  location_name: string | null;
  location_type: string | null;
  location_epistemic_status: string | null;
  location_lat: number | null;
  location_lon: number | null;

  // Provenance
  source_reference: string | null;
  source_record_type: string | null;

  _data_quality: TelecomDataQualityFlags;
}

export interface TelecomEventSummary {
  call_count: number;
  ping_count: number;
  message_count: number;
  total_telecom_events: number;
  data_limitations: {
    imei_linkage: string;
    imsi_linkage: string;
    sim_linkage: string;
    note: string;
  };
}

export interface TelecomEventsResponse {
  items: TelecomEventItem[];
  pagination: TelecomPagination;
  summary: TelecomEventSummary;
}

export interface TelecomEventsParams {
  event_type?: 'CALL' | 'DEVICE_PING' | 'MESSAGE';
  msisdn?: string;
  page?: number;
  page_size?: number;
}

// ─── Case Telecom Entities ───────────────────────────────────────────────────

export interface TelecomEntityItem {
  entity_id: string;
  entity_type: 'PHONE_NUMBER' | 'SIM' | 'DEVICE';
  /** Canonical identifier for this entity type */
  identifier: string | null;
  /** MSISDN | IMEI | ICCID */
  identifier_type: 'MSISDN' | 'IMEI' | 'ICCID' | 'ENTITY_ID';
  case_role: string;

  // PHONE_NUMBER fields
  msisdn: string | null;
  phone_operator: string | null;
  country_code: string | null;
  number_type: string | null;

  // DEVICE fields
  imei: string | null;
  device_type: string | null;
  manufacturer: string | null;
  model: string | null;

  // SIM fields
  iccid: string | null;
  /** Always null in current dataset — IMSI was never seeded */
  imsi: null;
  issuing_operator: string | null;

  // Metrics
  linked_event_count: number;
  linked_case_count: number;
  first_seen: string | null;
  last_seen: string | null;
}

export interface TelecomEntitiesResponse {
  items: TelecomEntityItem[];
  pagination: TelecomPagination;
}

export interface TelecomEntitiesParams {
  entity_type?: 'PHONE_NUMBER' | 'DEVICE' | 'SIM';
  page?: number;
  page_size?: number;
}

// ─── Case Telecom Towers ─────────────────────────────────────────────────────

export interface TelecomTower {
  tower_id: string;
  /** Location name — may be "Investigative Location — [Area]" or a real tower name */
  name: string | null;
  location_type: 'CELL_SECTOR_POLYGON';
  centroid_lat: number | null;
  centroid_lon: number | null;
  /** GeoJSON geometry — polygon or point */
  geometry: Record<string, unknown> | null;
  /** NULL in current dataset — no directional sector data seeded */
  azimuth_degrees: number | null;
  /** NULL in current dataset */
  beamwidth_degrees: number | null;
  uncertainty_radius_meters: number | null;
  hit_count: number;
  call_count: number;
  ping_count: number;
  first_observed: string | null;
  last_observed: string | null;
  _note: string;
}

export interface TelecomTowersResponse {
  towers: TelecomTower[];
  count: number;
  case_id: string;
  _data_quality: {
    azimuth_available: boolean;
    beamwidth_available: boolean;
    real_bts_ids_available: boolean;
    note: string;
  };
}

// ─── Tower Dump ──────────────────────────────────────────────────────────────

export interface TowerDumpItem {
  event_id: string;
  event_type: string;
  start: string | null;
  end: string | null;
  duration_seconds: number | null;
  case_id: string | null;
  observed_msisdn: string | null;
  operator: string | null;
  phone_role: 'CALLER' | 'CALLEE' | 'SUBJECT' | null;
  observed_from_event: string;
  /** NOT AVAILABLE */
  imei: null;
  /** NOT AVAILABLE */
  imsi: null;
  /** NOT AVAILABLE */
  sim_id: null;
}

export interface TowerDumpSummary {
  unique_msisdns_in_window: number;
  unique_events: number;
}

export interface TowerDumpResponse {
  tower_id: string;
  tower_name: string | null;
  items: TowerDumpItem[];
  pagination: TelecomPagination;
  summary: TowerDumpSummary;
  _data_quality: {
    imei_available: boolean;
    imsi_available: boolean;
    note: string;
  };
}

export interface TowerDumpParams {
  tower_id: string;
  case_id?: string;
  start_time?: string;
  end_time?: string;
  page?: number;
  page_size?: number;
}

// ─── Co-location ─────────────────────────────────────────────────────────────

export interface CoLocationResult {
  tower_id: string;
  tower_name: string | null;
  msisdn_a: string;
  msisdn_b: string;
  time_a: string | null;
  time_b: string | null;
  gap_seconds: number | null;
  supporting_event_ids: string[];
  /** Always CELL_SECTOR_APPROXIMATION — not GPS co-location */
  confidence: 'CELL_SECTOR_APPROXIMATION';
  note: string;
}

export interface CoLocationResponse {
  msisdn_a: string;
  msisdn_b: string;
  overlap_window_seconds: number;
  /** Total matching pairs across all pages */
  co_locations_found: number;
  results: CoLocationResult[];
  /** Pagination metadata — M-1 remediation */
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
  _data_quality: {
    precision: 'CELL_SECTOR_POLYGON';
    imei_linkage: boolean;
    warning: string;
  };
}

export interface CoLocationParams {
  msisdn_a: string;
  msisdn_b: string;
  case_id?: string;
  tower_id?: string;
  start_time?: string;
  end_time?: string;
  overlap_window_seconds?: number;
  page?: number;
  page_size?: number;
}

// ─── Device/SIM Matrix ───────────────────────────────────────────────────────

export interface DeviceSimMatrixItem {
  entity_id: string;
  imei: string | null;
  device_type: string | null;
  manufacturer: string | null;
  model: string | null;
  case_count: number;
  event_count: number;
  sims_observed: Array<{sim_id: string; iccid: string | null; imsi: string | null}>;
  msisdns_observed: string[];
  sim_count: number;
  msisdn_count: number;
  reuse_classification: 'DATA_NOT_AVAILABLE' | 'OBSERVED_REUSE' | 'POSSIBLE_SIM_SWAP' | 'CONFIRMED_SIM_SWAP';
  first_seen: string | null;
  last_seen: string | null;
}

export interface DeviceSimMatrixDataQuality {
  sim_in_device_rows: 0;
  sim_number_assignment_rows: 0;
  imsi_populated: false;
  sim_swap_detection: 'NOT AVAILABLE';
  reason: string;
  what_is_available: string;
}

export interface DeviceSimMatrixResponse {
  items: DeviceSimMatrixItem[];
  pagination: TelecomPagination;
  _data_quality: DeviceSimMatrixDataQuality;
}

// ─── Global Telecom Summary ───────────────────────────────────────────────────

export interface TelecomSummaryResponse {
  events: {
    total_calls: number;
    total_device_pings: number;
    total_messages: number;
    total_telecom_events: number;
  };
  entities: {
    unique_phone_numbers: number;
    unique_sims: number;
    unique_devices: number;
    unique_imeis: number;
    /** Always 0 — IMSI values are NULL in database */
    unique_imsis: 0;
  };
  towers: {
    cell_sector_polygons: number;
    towers_with_linked_events: number;
    pings_linked_to_cell_sector: number;
    pings_unmapped: number;
  };
  cross_case: {
    shared_phones: number;
    shared_devices: number;
    shared_sims: number;
  };
  data_quality: {
    sim_in_device_rows: 0;
    sim_number_assignment_rows: 0;
    imsi_populated: false;
    sim_swap_detection_available: false;
    cross_case_telecom_available: boolean;
    tower_dump_partial: boolean;
  };
  _note: string;
}

// ─── API Client ───────────────────────────────────────────────────────────────

export const telecomApi = {
  /**
   * GET /api/v1/cases/{case_id}/telecom/events
   * Returns CALL and DEVICE_PING events for a case.
   */
  getCaseTelecomEvents: async (
    caseId: string,
    params: TelecomEventsParams = {}
  ): Promise<TelecomEventsResponse> => {
    const response = await apiClient.get<TelecomEventsResponse>(
      `/cases/${caseId}/telecom/events`,
      { params }
    );
    return response.data;
  },

  /**
   * GET /api/v1/cases/{case_id}/telecom/entities
   * Returns PHONE_NUMBER, SIM, DEVICE entities linked to a case.
   */
  getCaseTelecomEntities: async (
    caseId: string,
    params: TelecomEntitiesParams = {}
  ): Promise<TelecomEntitiesResponse> => {
    const response = await apiClient.get<TelecomEntitiesResponse>(
      `/cases/${caseId}/telecom/entities`,
      { params }
    );
    return response.data;
  },

  /**
   * GET /api/v1/cases/{case_id}/telecom/towers
   * Returns CELL_SECTOR_POLYGON locations linked to a case.
   */
  getCaseTelecomTowers: async (
    caseId: string
  ): Promise<TelecomTowersResponse> => {
    const response = await apiClient.get<TelecomTowersResponse>(
      `/cases/${caseId}/telecom/towers`
    );
    return response.data;
  },

  /**
   * GET /api/v1/telecom/tower-dump
   * Returns all observable phones/events at a cell sector in a time window.
   */
  getTowerDump: async (
    params: TowerDumpParams
  ): Promise<TowerDumpResponse> => {
    const response = await apiClient.get<TowerDumpResponse>(
      `/telecom/tower-dump`,
      { params }
    );
    return response.data;
  },

  /**
   * GET /api/v1/telecom/co-location
   * Detects cell-sector co-location of two MSISDNs.
   * NOTE: Precision is CELL_SECTOR only — not GPS.
   */
  getCoLocation: async (
    params: CoLocationParams
  ): Promise<CoLocationResponse> => {
    const response = await apiClient.get<CoLocationResponse>(
      `/telecom/co-location`,
      { params }
    );
    return response.data;
  },

  /**
   * GET /api/v1/telecom/device-sim-matrix
   * Returns IMEI device records.
   * NOTE: SIM linkage is NOT AVAILABLE — sim_in_device table is empty.
   */
  getDeviceSimMatrix: async (
    params: { case_id?: string; page?: number; page_size?: number; min_reuse?: number } = {}
  ): Promise<DeviceSimMatrixResponse> => {
    const response = await apiClient.get<DeviceSimMatrixResponse>(
      `/telecom/device-sim-matrix`,
      { params }
    );
    return response.data;
  },

  /**
   * GET /api/v1/telecom/summary
   * Returns global CDR & Tower Intelligence summary metrics.
   * ALL values are database-derived — zero hardcoded numbers.
   */
  getTelecomSummary: async (): Promise<TelecomSummaryResponse> => {
    const response = await apiClient.get<TelecomSummaryResponse>(
      `/telecom/summary`
    );
    return response.data;
  },

  // ── BENCHMARK CASE DISCOVERY ─────────────────────────────────────────────
  // These endpoints query ONLY civix_telecom_benchmark.
  // They NEVER query civix.investigative_case.

  /**
   * GET /api/v1/telecom/benchmark/cases
   * Returns all available benchmark (BENCH-*) cases.
   * Isolated from the primary CIVIX case registry.
   */
  getBenchmarkCases: async (): Promise<BenchmarkCasesResponse> => {
    const response = await apiClient.get<BenchmarkCasesResponse>(
      `/telecom/benchmark/cases`
    );
    return response.data;
  },

  /**
   * GET /api/v1/telecom/benchmark/case-phones
   * Returns top phones for a BENCH- case — for co-location pair selection.
   * ONLY queries civix_telecom_benchmark.
   */
  getBenchmarkCasePhones: async (
    caseId: string,
    limit: number = 50
  ): Promise<BenchmarkCasePhonesResponse> => {
    const response = await apiClient.get<BenchmarkCasePhonesResponse>(
      `/telecom/benchmark/case-phones`,
      { params: { case_id: caseId, limit } }
    );
    return response.data;
  },

};

export interface BenchmarkCasePhone {
  id: string;
  msisdn: string;
  operator: string | null;
  circle: string | null;
  event_count: number;
}

export interface BenchmarkCasePhonesResponse {
  case_number: string;
  phones: BenchmarkCasePhone[];
  count: number;
  data_source: 'civix_telecom_benchmark';
  provenance: 'SYNTHETIC_TELECOM_BENCHMARK';
}

// ─── Benchmark Types ──────────────────────────────────────────────────────────

export interface BenchmarkCaseItem {
  id: string;
  case_number: string;
  title: string;
  description: string | null;
  scenario_type: string;
  severity: string;
  start_time: string | null;
  end_time: string | null;
  provenance: 'SYNTHETIC_TELECOM_BENCHMARK';
  generation_run_id: string;
  synthetic_flag: true;
  event_count: number;
}

export interface BenchmarkCasesResponse {
  cases: BenchmarkCaseItem[];
  count: number;
  data_source: 'civix_telecom_benchmark';
  provenance: 'SYNTHETIC_TELECOM_BENCHMARK';
  _note: string;
}

export type { TelecomEventsResponse, TelecomEntitiesResponse, TelecomTowersResponse };
