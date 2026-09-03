import { apiClient } from './client';
import type { AuthenticatedUser } from '../types/api';

export const usersApi = {
  async getCurrentUser(): Promise<AuthenticatedUser> {
    const response = await apiClient.get<AuthenticatedUser>('/users/me');
    return response.data;
  }
};
