import { apiClient } from './client';
import type { EntityResponse } from '../types/api';

export const entitiesApi = {
  async getEntity(entityId: string): Promise<EntityResponse> {
    const response = await apiClient.get<EntityResponse>(`/entities/${entityId}`);
    return response.data;
  }
};
