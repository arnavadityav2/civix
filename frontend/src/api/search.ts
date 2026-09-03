import { apiClient } from './client';
import type { SearchResponse } from '../types/api';

export const searchApi = {
  async searchEntities(query: string, entityType?: string, limit = 20, offset = 0): Promise<SearchResponse> {
    const params: Record<string, any> = { q: query, limit, offset };
    if (entityType) {
      params.entity_type = entityType;
    }
    const response = await apiClient.get<SearchResponse>('/search', { params });
    return response.data;
  }
};
