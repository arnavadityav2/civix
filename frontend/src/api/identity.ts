import { apiClient } from './client';
import type { IdentityCandidatesResponse } from '../types/api';

export const identityApi = {
  async getCandidates(): Promise<IdentityCandidatesResponse> {
    const response = await apiClient.get<IdentityCandidatesResponse>('/identity/candidates');
    return response.data;
  }
};
