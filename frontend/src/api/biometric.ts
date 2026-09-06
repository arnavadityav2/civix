import { apiClient } from './client';

// ============================================================
// BIOMETRIC INTELLIGENCE API CLIENT
// Wraps all /api/v1/biometric/* endpoints
// ============================================================

export interface BiometricSearchResponse {
  status: string; // MATCH_FOUND | AMBIGUOUS_MATCH | NO_CIVIX_MATCH | NO_FACE_DETECTED | MULTIPLE_FACES_DETECTED | BIOMETRIC_QUALITY_INSUFFICIENT | ERROR
  detected_faces: number;
  face_bounding_box?: number[];
  model_version?: string;
  index_source?: string;
  connector_status?: string;
  // Cosine proximity — NOT a probability. Use "COSINE PROXIMITY" label in UI.
  match_score?: number;
  confidence_band?: 'HIGH' | 'MEDIUM' | 'LOW' | 'UNCERTAIN';
  person_id?: string;
  person_name?: string;
  avatar_url?: string | null; // NOTE: avatar_url is not in current DB schema — will be null
  classification?: string;
  primary_role?: string;
  synthetic_identity?: {
    synthetic_id: string;
    name: string;
    age: number;
    occupation: string;
    city: string;
    phone: string;
    address: string;
    status: string;
    label: string;        // Always "DEMO ONLY"
    image_hash_prefix: string;
  };
  error_message?: string;
}

export interface BiometricReference {
  ref_id: string;
  person_id: string;
  image_path: string;
  source_type: string;
  is_derived: boolean;
  quality_note: string;
  capture_timestamp: string;
  camera_location: string;
  provenance: string;
  embedding_key: string;
  embedding_model: string;
  embedding_model_version: string;
  embedding_dim: number;
  detection_confidence: number;
}

export interface BiometricContextResponse {
  person_id: string;
  cases: {
    case_id: string;
    case_number: string;
    title: string;
    status: string;
    role: string;
  }[];
  evidence: any[];
  events: any[];
  leads: any[];
}

export interface BiometricAvailability {
  person_id: string;
  enrolled: boolean;
  reference_count: number;
  index_source: string;
}

export interface CasePersonBiometricStatus {
  entity_id: string;
  role: string;
  display_name: string;
  gender?: string;
  date_of_birth?: string;
  nationality?: string;
  is_deceased?: boolean;
  biometric_enrolled: boolean;
  biometric_reference_count: number;
  biometric_status: 'AVAILABLE' | 'NO_REFERENCE';
}

export interface CaseBiometricManifest {
  case_id: string;
  case_number: string;
  case_title: string;
  case_status: string;
  persons: CasePersonBiometricStatus[];
  enrolled_count: number;
  total_person_count: number;
}

export interface CCTVObservation {
  observation_id: string;
  case_id: string;
  camera_id?: string;
  signal_class?: string;
  timestamp?: string;
  investigator_notes?: string;
  camera_code?: string;
  camera_name?: string;
  city?: string;
  region?: string;
  latitude?: number;
  longitude?: number;
}

export interface CCTVTraceResponse {
  person_id: string;
  observations: CCTVObservation[];
  observation_count: number;
  data_source: string;
  note: 'LIVE_DATA' | 'SYNTHETIC_DEMO';
}

export interface PersonSummary {
  person_id: string;
  display_name: string;
  gender?: string;
  date_of_birth?: string;
  nationality?: string;
  is_deceased?: boolean;
  notes?: string;
  entity_type: string;
  visibility_status: string;
}

// ============================================================
// API METHODS
// ============================================================

export const biometricApi = {
  /**
   * Submit a face image for biometric search against the CIVIX index.
   * Returns cosine proximity scores, NOT probabilities.
   */
  search: async (file: File): Promise<BiometricSearchResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/biometric/search', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  /**
   * Get reference images enrolled for a specific person in the biometric index.
   */
  getReferences: async (personId: string): Promise<{ references: BiometricReference[] }> => {
    const response = await apiClient.get(`/biometric/references/${personId}`);
    return response.data;
  },

  /**
   * Get investigative context (linked cases, evidence, events, leads) for a matched person.
   */
  getContext: async (personId: string): Promise<BiometricContextResponse> => {
    const response = await apiClient.get(`/biometric/context/${personId}`);
    return response.data;
  },

  /**
   * Check if a specific person has biometric enrollment in the CIVIX index.
   * Used to dynamically show [ANALYZE] vs [NO REFERENCE] in the Case → Person workflow.
   */
  checkAvailability: async (personId: string): Promise<BiometricAvailability> => {
    const response = await apiClient.get(`/biometric/availability/${personId}`);
    return response.data;
  },

  /**
   * Get all persons in a case with their biometric enrollment status.
   * This is the primary entry point for the Case → Person → Biometric workflow.
   */
  getCaseBiometricManifest: async (caseId: string): Promise<CaseBiometricManifest> => {
    const response = await apiClient.get(`/cases/${caseId}/biometric-manifest`);
    return response.data;
  },

  /**
   * Get CCTV trace observations for a person (via their case linkages).
   * NOTE: cctv_observation table currently has 0 rows in the demo environment.
   * This returns empty observations gracefully — UI should handle NO_CCTV_OBSERVATIONS state.
   */
  getCctvTrace: async (personId: string): Promise<CCTVTraceResponse> => {
    const response = await apiClient.get(`/biometric/cctv-trace/${personId}`);
    return response.data;
  },

  /**
   * Get basic person details for display in the biometric workstation.
   */
  getPersonSummary: async (personId: string): Promise<PersonSummary> => {
    const response = await apiClient.get(`/biometric/person-summary/${personId}`);
    return response.data;
  },

  /**
   * Build the reference image URL for a given image_path from the references endpoint.
   * Uses the backend's static file serving for biometric reference images.
   */
  buildReferenceImageUrl: (imagePath: string): string => {
    const base = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, '');
    return `${base}/${imagePath}`;
  },
};
