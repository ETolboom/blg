import { apiGet, apiPost, apiPut, apiDelete } from './api';
import type { BehavioralRuleGroup, GroupEvaluationResult } from '@/features/behavior/types/group';
import type { Rubric } from '@/features/rubric/types/rubric';

export const groupService = {
    /**
     * List all behavioral rule groups
     */
    async getGroups(): Promise<BehavioralRuleGroup[]> {
        return apiGet<BehavioralRuleGroup[]>('/behavioral-rule-groups');
    },

    /**
     * Get specific group, optionally evaluated against a submission
     */
    async getGroup(groupId: string, filename?: string): Promise<BehavioralRuleGroup> {
        const url = filename
            ? `/behavioral-rule-groups/${groupId}?filename=${encodeURIComponent(filename)}`
            : `/behavioral-rule-groups/${groupId}`;
        return apiGet<BehavioralRuleGroup>(url);
    },

    /**
     * Create group
     */
    async createGroup(group: BehavioralRuleGroup): Promise<BehavioralRuleGroup> {
        return apiPost<BehavioralRuleGroup>(
            '/behavioral-rule-groups',
            JSON.stringify(group),
            'application/json'
        );
    },

    /**
     * Update group
     */
    async updateGroup(groupId: string, group: BehavioralRuleGroup): Promise<BehavioralRuleGroup> {
        return apiPut<BehavioralRuleGroup>(
            `/behavioral-rule-groups/${groupId}`,
            JSON.stringify(group),
            'application/json'
        );
    },

    /**
     * Delete group
     */
    async deleteGroup(groupId: string): Promise<{ message: string }> {
        return apiDelete<{ message: string }>(`/behavioral-rule-groups/${groupId}`);
    },

    /**
     * Test evaluate a group
     */
    async testEvaluateGroup(group: BehavioralRuleGroup): Promise<GroupEvaluationResult> {
        return apiPost<GroupEvaluationResult>(
            '/rubric/criteria/behavioral-group/analyze',
            JSON.stringify(group),
            'application/json'
        );
    },

    /**
     * Add group to rubric
     */
    async addGroupToRubric(group: BehavioralRuleGroup): Promise<Rubric> {
        return apiPost<Rubric>(
            `/rubric/criteria/behavioral-group/${group.group_id}`,
            JSON.stringify(group),
            'application/json'
        );
    }
};
