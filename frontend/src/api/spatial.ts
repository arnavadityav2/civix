import { apiClient } from './client';

export type CaseStatus = 'OPEN' | 'UNDER_INVESTIGATION' | 'CLOSED_SOLVED' | 'CLOSED_UNSOLVED' | 'SUSPENDED';
export type CasePriority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type CaseType = 'FRAUD' | 'THEFT' | 'ORGANIZED_CRIME' | 'FINANCIAL_CRIME' | 'CYBER_FRAUD' | 'CRIMINAL' | 'INTELLIGENCE' | 'MULTI_CASE';
export type EpistemicStatus = 'CONFIRMED' | 'PROBABLE' | 'POSSIBLE' | 'REFUTED' | 'INCONCLUSIVE';
export type LocationPredicate = 'LOCATED_AT' | 'SEEN_AT' | 'PRESENT_AT' | 'RESIDED_AT' | 'VISITED' | 'ALIBI_CONFIRMED_AT' | 'REGISTERED_AT' | 'PINGED_TOWER';

export interface SpatialCaseProperties {
  case_id: string;
  case_number: string;
  title: string;
  status: CaseStatus;
  priority: CasePriority;
  case_type: CaseType;
  event_count: number;
  spatial_semantic: 'CASE_FOOTPRINT_CENTROID';
}

export interface SpatialCaseFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number]; // [longitude, latitude]
  };
  properties: SpatialCaseProperties;
}

export interface SpatialCaseCollection {
  type: 'FeatureCollection';
  features: SpatialCaseFeature[];
}

export interface SpatialEventProperties {
  event_location_id: string;
  event_id: string;
  event_type: string;
  event_start: string;
  event_end: string;
  is_open_ended: boolean;
  location_id: string;
  location_name: string;
  location_type: string;
  location_predicate: LocationPredicate;
  epistemic_status: EpistemicStatus;
  case_id: string;
  source_record_id: string | null;
  generation_run_id: string | null;
  generation_origin: string | null;
}

export interface SpatialEventFeature {
  type: 'Feature';
  geometry: {
    type: 'Point' | 'LineString';
    coordinates: [number, number] | [number, number][];
  };
  properties: SpatialEventProperties;
}

export interface SpatialEventCollection {
  type: 'FeatureCollection';
  features: SpatialEventFeature[];
}

export interface SpatialCaseQueryParams {
  bbox?: string;
  status?: string;
  priority?: string;
  case_type?: string;
  limit?: number;
}

export interface SpatialEventQueryParams {
  bbox?: string;
  event_type?: string;
  limit?: number;
}

export const spatialApi = {
  getSpatialCases: async (params?: SpatialCaseQueryParams): Promise<SpatialCaseCollection> => {
    const response = await apiClient.get<SpatialCaseCollection>('/spatial/cases', { params });
    return response.data;
  },

  getSpatialCaseEvents: async (caseId: string, params?: SpatialEventQueryParams): Promise<SpatialEventCollection> => {
    const response = await apiClient.get<SpatialEventCollection>(`/spatial/cases/${caseId}/events`, { params });
    return response.data;
  }
};
