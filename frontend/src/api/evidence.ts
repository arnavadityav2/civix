import { apiClient } from './client';
import type { EvidenceUploadResponse, EvidenceStatusResponse, EvidenceListItem } from '../types/api';

export const evidenceApi = {
  async uploadEvidence(
    caseId: string,
    file: File,
    acquisitionMethod = 'FIELD_COLLECTION',
    acquisitionContext = ''
  ): Promise<EvidenceUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('acquisition_method', acquisitionMethod);
    formData.append('acquisition_context', acquisitionContext);

    const response = await apiClient.post<EvidenceUploadResponse>(
      `/cases/${caseId}/evidence/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  async listEvidence(caseId: string): Promise<EvidenceListItem[]> {
    const response = await apiClient.get<EvidenceListItem[]>(`/cases/${caseId}/evidence`);
    return response.data;
  },

  async getEvidenceStatus(caseId: string, artifactId: string): Promise<EvidenceStatusResponse> {
    const response = await apiClient.get<EvidenceStatusResponse>(`/cases/${caseId}/evidence/${artifactId}`);
    return response.data;
  },

  async triggerProcessing(caseId: string, artifactId: string): Promise<{ artifact_id: string; processing_status: string; message: string }> {
    const response = await apiClient.post(`/cases/${caseId}/evidence/${artifactId}/process`);
    return response.data;
  }
};
