import { apiClient } from './client';
import type { GraphResponse } from '../types/api';

export const graphApi = {
  async getCaseGraph(caseId: string, depth = 2, nodeLimit?: number, relLimit?: number): Promise<GraphResponse> {
    const params: Record<string, any> = { depth };
    if (nodeLimit !== undefined) params.node_limit = nodeLimit;
    if (relLimit !== undefined) params.rel_limit = relLimit;

    const response = await apiClient.get<GraphResponse>(`/cases/${caseId}/graph`, { params });
    return response.data;
  },

  async getCaseUniverse(caseId: string, depth = 3, nodeLimit = 250, relLimit = 500): Promise<GraphResponse> {
    const response = await apiClient.get<GraphResponse>(`/cases/${caseId}/universe`, {
      params: {
        depth,
        node_limit: nodeLimit,
        rel_limit: relLimit
      }
    });
    return response.data;
  }
};

