import { apiGet, apiPost } from './api';
import { Rubric, Criterion } from "@/features/rubric/types/rubric";
import { CheckComplexityType } from "@/features/rubric/types/check_complexity";

export interface CheckKeyValuePair {
    key: string;
    value: string[];
}

export interface CheckKeyValueType {
    pairs: CheckKeyValuePair[];
    key_label: string;
    value_label: string;
}

export interface CheckSelectionPair {
    label: string;
    type: string;
}

export interface CheckSelectionType {
    placeholder: string;
    accepted_values: string[];
    pairs: CheckSelectionPair[];
}

export interface CheckInput {
    input_type: string;
    input_label: string;
    key_label?: string;
    value_label?: string;
    multiple?: boolean;
    data?: string | number | CheckKeyValueType | CheckSelectionType;
}

export interface AnalysisNode {
    key: string;
    data: {
        id: string;
        name: string;
        description: string;
    };
    children?: AnalysisNode[];
}

export interface GradeSubmissionResponse {
    criteria: Rubric['criteria'];
}

export interface Check {
    id: string;
    name: string;
    description: string;
    check_complexity: CheckComplexityType;
    inputs?: CheckInput[];
}

export const checkService = {
    async getChecks(): Promise<Check[]> {
        return apiGet<Check[]>('/checks');
    },

    async gradeSubmission(filename: string): Promise<GradeSubmissionResponse> {
        const result = await apiPost<GradeSubmissionResponse>(
            `/checks/analyze?filename=${filename}`,
            undefined,
            'application/xml'
        );
        result.criteria = result.criteria.map(
            (c: Criterion) => ({ ...c, check_complexity: String(c.check_complexity) as CheckComplexityType })
        );
        return result;
    },

    async analyzeFile(file: File): Promise<AnalysisNode[]> {
        return apiPost<AnalysisNode[]>('/checks/analyze/all', file);
    },
};
