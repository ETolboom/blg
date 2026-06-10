import { apiGet, apiPost } from './api';
import { Rubric } from "@/features/rubric/types/rubric";
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

export type CheckInputType = 'string' | 'integer' | 'key-value' | 'selection';

interface BaseCheckInput {
    input_label: string;
    multiple?: boolean;
}

// Discriminated union on `input_type`, mirroring the backend's CheckFormInput
// variants (checks/__init__.py). Narrowing on `input_type` gives a correctly
// typed `data` with no casts. `multiple` string/integer inputs carry an array.
export interface StringCheckInput extends BaseCheckInput {
    input_type: 'string';
    data: string | string[];
}

export interface IntegerCheckInput extends BaseCheckInput {
    input_type: 'integer';
    data: number | number[];
}

export interface KeyValueCheckInput extends BaseCheckInput {
    input_type: 'key-value';
    data: CheckKeyValueType;
}

export interface SelectionCheckInput extends BaseCheckInput {
    input_type: 'selection';
    data: CheckSelectionType;
}

export type CheckInput =
    | StringCheckInput
    | IntegerCheckInput
    | KeyValueCheckInput
    | SelectionCheckInput;

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
        return apiPost<GradeSubmissionResponse>(
            `/checks/analyze?filename=${encodeURIComponent(filename)}`,
            undefined,
            'application/xml'
        );
    },

    async analyzeFile(file: File): Promise<AnalysisNode[]> {
        return apiPost<AnalysisNode[]>('/checks/analyze/all', file);
    },
};
