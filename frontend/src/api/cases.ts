import { apiClient } from './client';
import type { CaseListItem, CaseRegistryResponse, CaseRegistryParams, CaseCreateRequest, CaseEntityRoleRequest, CaseEntityRoleResponse, CaseEntityRoleListItem } from '../types/api';

export const casesApi = {
  async listCases(): Promise<CaseListItem[]> {
    const response = await apiClient.get<CaseListItem[]>('/cases');
    return response.data;
  },

  async getRegistry(params?: CaseRegistryParams): Promise<CaseRegistryResponse> {
    const response = await apiClient.get<CaseRegistryResponse>('/cases/registry', { params });
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
  },

  async getCaseEntities(caseId: string): Promise<CaseEntityRoleListItem[]> {
    const response = await apiClient.get(`/cases/${caseId}/entities`);
    return response.data;
  }
};
