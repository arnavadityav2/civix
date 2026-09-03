import { apiClient } from './client';
import type {
  InvestigativeLeadResponse,
  GenerateLeadsResponse,
  FindingResponse,
  LeadExplanationResponse,
  LeadProvenanceResponse,
  LeadDispositionRequest
} from '../types/api';

export const leadsApi = {
  async getCaseLeads(caseId: string): Promise<InvestigativeLeadResponse[]> {
    const response = await apiClient.get<InvestigativeLeadResponse[]>(`/cases/${caseId}/leads`);
    return response.data;
  },

  async generateLeads(caseId: string, hypothesisId?: string): Promise<GenerateLeadsResponse> {
    const response = await apiClient.post<GenerateLeadsResponse>(`/cases/${caseId}/leads/generate`, {
      hypothesis_id: hypothesisId || null
    });
    return response.data;
  },

  async disposeLead(caseId: string, leadId: string, req: LeadDispositionRequest): Promise<InvestigativeLeadResponse> {
    const response = await apiClient.post<InvestigativeLeadResponse>(
      `/cases/${caseId}/leads/${leadId}/disposition`,
      req
    );
    return response.data;
  },

  async getLeadFindings(caseId: string, leadId: string): Promise<FindingResponse[]> {
    const response = await apiClient.get<FindingResponse[]>(`/cases/${caseId}/leads/${leadId}/findings`);
    return response.data;
  },

  async getLeadExplanation(caseId: string, leadId: string): Promise<LeadExplanationResponse> {
    const response = await apiClient.get<LeadExplanationResponse>(`/cases/${caseId}/leads/${leadId}/explanation`);
    return response.data;
  },

  async getLeadProvenance(caseId: string, leadId: string): Promise<LeadProvenanceResponse> {
    const response = await apiClient.get<LeadProvenanceResponse>(`/cases/${caseId}/leads/${leadId}/provenance`);
    return response.data;
  }
};
