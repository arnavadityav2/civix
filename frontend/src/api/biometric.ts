import { apiClient } from './client';

export interface BiometricSearchResponse {
  status: string;
  detected_faces: number;
  face_bounding_box?: number[];
  model_version?: string;
  index_source?: string;
  connector_status?: string;
  match_score?: number;
  confidence_band?: string;
  person_id?: string;
  person_name?: string;
  avatar_url?: string;
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
    label: string;
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
  cases: any[];
  evidence: any[];
  events: any[];
  leads: any[];
}

export const biometricApi = {
  search: async (file: File): Promise<BiometricSearchResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/biometric/search', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getReferences: async (personId: string): Promise<{ references: BiometricReference[] }> => {
    const response = await apiClient.get(`/biometric/references/${personId}`);
    return response.data;
  },
  
  getContext: async (personId: string): Promise<BiometricContextResponse> => {
    const response = await apiClient.get(`/biometric/context/${personId}`);
    return response.data;
  }
};
