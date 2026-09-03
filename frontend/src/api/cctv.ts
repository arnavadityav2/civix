import { apiClient } from './client';

export interface Camera {
  camera_id: string;
  source_id: string;
  camera_code: string;
  display_name: string;
  city: string;
  region: string;
  latitude: number;
  longitude: number;
  camera_type: string;
  status: string;
  access_type: string;
  last_health_check?: string;
  created_at: string;
}

export interface Feed {
  feed_id: string;
  camera_id: string;
  feed_type: string;
  feed_url: string;
  embed_url?: string;
  frame_rate: number;
  resolution_w: number;
  resolution_h: number;
  is_active: boolean;
  created_at: string;
}

export interface CameraDetail {
  camera: Camera;
  feeds: Feed[];
}

export interface CVTrack {
  track_id: string;
  first_seen: string;
  last_seen: string;
  crop_storage_uri: string;
  detected_make: string;
}

export interface CCTVPlateDetection {
  plate_detection_id: string;
  job_id: string;
  camera_id: string;
  track_id: string;
  detection_id?: string;
  frame_timestamp: string;
  bounding_box: any;
  plate_crop_storage_uri: string;
  raw_ocr_text: string;
  normalized_plate: string;
  ocr_confidence: number;
  confidence_category: string;
  detector_model: string;
  ocr_engine: string;
  ocr_engine_version: string;
  created_at: string;
}

export interface SearchJobRequest {
  case_id: string;
  target_vehicle_id?: string;
  camera_ids: string[];
  start_time: string;
  end_time: string;
}

export interface SearchJobResponse {
  job_id: string;
  case_id: string;
  requested_by: string;
  target_vehicle_id: string;
  camera_ids: string[];
  start_time: string;
  end_time: string;
  status: string;
  progress_pct: number;
  frames_processed: number;
  error_message?: string;
}

export const cctvApi = {
  async listCameras(): Promise<Camera[]> {
    const response = await apiClient.get<Camera[]>('/cctv/cameras');
    return response.data;
  },

  async getCameraDetail(cameraId: string): Promise<CameraDetail> {
    const response = await apiClient.get<CameraDetail>(`/cctv/cameras/${cameraId}`);
    return response.data;
  },

  async syncRegistry(): Promise<any> {
    const response = await apiClient.post('/cctv/registry/sync');
    return response.data;
  },

  async startSearchJob(request: SearchJobRequest): Promise<SearchJobResponse> {
    const response = await apiClient.post<SearchJobResponse>('/cctv/search', request);
    return response.data;
  },

  async getSearchJob(jobId: string): Promise<SearchJobResponse> {
    const response = await apiClient.get<SearchJobResponse>(`/cctv/search/${jobId}`);
    return response.data;
  },

  async getJobTracks(jobId: string): Promise<CVTrack[]> {
    const response = await apiClient.get<CVTrack[]>(`/cctv/search/${jobId}/tracks`);
    return response.data;
  },

  async getJobPlates(jobId: string): Promise<CCTVPlateDetection[]> {
    const response = await apiClient.get<CCTVPlateDetection[]>(`/cctv/search/${jobId}/plates`);
    return response.data;
  }
};
