import { apiGet, apiPost, apiPut, apiDelete, ApiError } from './api';
import type { BehavioralRule } from '@/features/behavior/types/template';
import type { ValidationResponse } from '@/features/behavior/types/validation';

export const behavioralRuleService = {
  /**
   * Fetch all available behavioral rules (summary)
   */
  async getBehavioralRules(): Promise<BehavioralRule[]> {
    return apiGet<BehavioralRule[]>('/behavioral-rules');
  },

  /**
   * Fetch all available behavioral rule templates
   */
  async getBehavioralRuleTemplates(): Promise<BehavioralRule[]> {
    return apiGet<BehavioralRule[]>('/behavioral-rule-templates');
  },

  /**
   * Fetch a specific behavioral rule by ID with full nodes/edges
   */
  async getBehavioralRule(id: string): Promise<BehavioralRule> {
    return apiGet<BehavioralRule>(`/behavioral-rules/${encodeURIComponent(id)}`);
  },

  /**
   * Create a new behavioral rule
   */
  async createBehavioralRule(rule: BehavioralRule): Promise<BehavioralRule> {
    return apiPost<BehavioralRule>(
      '/behavioral-rules',
      JSON.stringify(rule),
      'application/json'
    );
  },

  /**
   * Update an existing behavioral rule
   */
  async updateBehavioralRule(id: string, rule: BehavioralRule): Promise<BehavioralRule> {
    if (id !== rule.id) {
      throw new Error('Behavioral Rule ID mismatch');
    }
    return apiPut<BehavioralRule>(
      `/behavioral-rules/${encodeURIComponent(id)}`,
      JSON.stringify(rule),
      'application/json'
    );
  },

  /**
   * Delete a behavioral rule
   */
  async deleteBehavioralRule(id: string): Promise<{ message: string }> {
    return apiDelete<{ message: string }>(`/behavioral-rules/${encodeURIComponent(id)}`);
  },

  /**
   * Validate behavioral rule against reference BPMN or a specific submission and update rubric
   */
  async validateBehavioralRule(id: string, filename?: string): Promise<ValidationResponse> {
    const url = filename
      ? `/behavioral-rules/${id}/validate?filename=${encodeURIComponent(filename)}`
      : `/behavioral-rules/${id}/validate`;

    return apiPost<ValidationResponse>(
      url,
      undefined,
      undefined
    );
  },

  /**
   * Save or update behavioral rule (smart upsert)
   */
  async saveBehavioralRule(rule: BehavioralRule): Promise<BehavioralRule> {
    try {
      // Try to fetch existing rule
      await this.getBehavioralRule(rule.id);
      // If it exists, update it
      return this.updateBehavioralRule(rule.id, rule);
    } catch (error) {
      // Only a genuine 404 means "doesn't exist yet" -> create. Any other
      // error (network, 500) must propagate, otherwise a transient failure on
      // the GET would trigger a create that clobbers existing server state.
      if (error instanceof ApiError && error.status === 404) {
        return this.createBehavioralRule(rule);
      }
      throw error;
    }
  }
};
