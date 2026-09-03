import { apiClient } from './client';
import type { CaseListItem, CaseCreateRequest, CaseEntityRoleRequest, CaseEntityRoleResponse } from '../types/api';

export const casesApi = {
  async listCases(): Promise<CaseListItem[]> {
    const response = await apiClient.get<CaseListItem[]>('/cases');
    return response.data;
  },

  async getCase(caseId: string): Promise<CaseListItem> {
    const response = await apiClient.get<CaseListItem>(`/cases/${caseId}`);
    return response.data;
  },

  async createCase(data: CaseCreateRequest): Promise<{ case_id: string; case_number: string; title: string; status: string }> {
    const response = await apiClient.post('/cases', data);
    return response.data;
  },

  async linkEntityToCase(caseId: string, request: CaseEntityRoleRequest): Promise<CaseEntityRoleResponse> {
    const response = await apiClient.post<CaseEntityRoleResponse>(`/cases/${caseId}/entities`, request);
    return response.data;
  }
};
