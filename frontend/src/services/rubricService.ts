import { apiGet, apiPost, apiPut, apiDelete } from './api';
import type { Assignment, Rubric, Criterion } from "@/features/rubric/types/rubric";
import type { Check } from "@/services/checkService";
import { BehavioralRule } from "@/features/behavior/types/template.ts";

// The backend may return check_complexity as a number (0/1/2) even though our
// enum is now string-based. Normalize here so all comparisons work correctly.
const normalizeCriteria = (criteria: Criterion[]): Criterion[] =>
    criteria.map(c => ({ ...c, check_complexity: String(c.check_complexity) as any }));


export interface CreateRubricRequest {
    assignment: Assignment;
    checks: string[];
}

export interface DeleteCriterionResponse {
    message: string;
    unmerged_rules: string[];
    warning?: string;
}

export const rubricService = {
    async getRubric(): Promise<Rubric> {
        const rubric = await apiGet<Rubric>('/rubric');
        rubric.criteria = normalizeCriteria(rubric.criteria);
        return rubric;
    },

    async createRubric(request: CreateRubricRequest): Promise<Rubric> {
        return apiPost<Rubric>('/rubric', JSON.stringify(request), 'application/json');
    },

    async deleteCriterion(criterionId: string): Promise<DeleteCriterionResponse> {
        return apiDelete<DeleteCriterionResponse>(`/rubric/criteria/${criterionId}`);
    },

    async updateCheckCriterion(check: Check): Promise<Rubric> {
        return apiPost<Rubric>(
            `/rubric/criteria/${check.id}`,
            JSON.stringify(check.inputs),
            'application/json'
        );
    },

    async updateBehavioralCriterion(rule: BehavioralRule): Promise<Rubric> {
        return apiPost<Rubric>(
            `/rubric/criteria/behavioral/${rule.id}`,
            JSON.stringify({
                id: rule.id,
                name: rule.name,
                description: rule.description,
                maxPoints: rule.maxPoints,
                nodes: rule.nodes,  // Send as array, not stringified
                edges: rule.edges   // Send as array, not stringified
            }),
            'application/json'
        );
    },

    async uploadSupplement(file: File): Promise<{ message: string; filename: string }> {
        const formData = new FormData();
        formData.append('file', file);
        return apiPost<{ message: string; filename: string }>('/rubric/supplement', formData);
    },

    getSupplementUrl(): string {
        return '/api/rubric/supplement';
    },

    async deleteSupplement(): Promise<{ message: string }> {
        return apiDelete<{ message: string }>('/rubric/supplement');
    },

    async updateReference(xml: string): Promise<{ message: string }> {
        return apiPut<{ message: string }>(
            '/rubric/reference',
            JSON.stringify({ reference_xml: xml }),
            'application/json'
        );
    },
};
