import { apiClient } from './client';
import type { GraphResponse } from '../types/api';

export const graphApi = {
  async getCaseGraph(caseId: string, depth = 1, nodeLimit = 100, relLimit = 200): Promise<GraphResponse> {
    const response = await apiClient.get<GraphResponse>(`/cases/${caseId}/graph`, {
      params: {
        depth,
        node_limit: nodeLimit,
        rel_limit: relLimit
      }
    });
    return response.data;
  }
};
