import axios from 'axios';

export interface HealthResponse {
  status: string;
  database: string;
}

export const healthApi = {
  async getHealthStatus(): Promise<HealthResponse> {
    const response = await axios.get<HealthResponse>('/health');
    return response.data;
  }
};
