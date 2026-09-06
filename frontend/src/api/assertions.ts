import { apiClient } from './client';
import type {
  ProposedAssertionPayload,
  AssertionProposalResponse,
  ReviewAssertionPayload,
  ReviewAssertionResponse,
  ProposedAssertionListItem,
} from '../types/graph';

export const assertionsApi = {
  async proposeAssertion(
    caseId: string,
    payload: ProposedAssertionPayload
  ): Promise<AssertionProposalResponse> {
    const response = await apiClient.post<AssertionProposalResponse>(
      `/cases/${caseId}/assertions`,
      payload
    );
    return response.data;
  },

  async reviewAssertion(
    caseId: string,
    assertionId: string,
    payload: ReviewAssertionPayload
  ): Promise<ReviewAssertionResponse> {
    const response = await apiClient.post<ReviewAssertionResponse>(
      `/cases/${caseId}/assertions/${assertionId}/review`,
      payload
    );
    return response.data;
  },

  async getProposedAssertions(caseId: string): Promise<ProposedAssertionListItem[]> {
    const response = await apiClient.get<ProposedAssertionListItem[]>(
      `/cases/${caseId}/assertions/proposed`
    );
    return response.data;
  },
};
