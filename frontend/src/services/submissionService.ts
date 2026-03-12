import { apiGet, apiPatch, handleResponse } from './api';
import { Criterion } from "@/features/rubric/types/rubric";

export interface Submission {
    filename: string;
    name: string;
}

export const submissionService = {
    async getSubmissions(): Promise<Submission[]> {
        return apiGet<Submission[]>('/submissions');
    },

    async getSubmission(filename: string): Promise<string> {
        return apiGet<string>(`/submissions/${filename}`);
    },

    async saveSubmission(filename: string, criteria: Criterion[]): Promise<void> {
        return apiPatch<void>(
            `/submissions/${filename}`,
            JSON.stringify(criteria),
            'application/json'
        );
    },

    async uploadSubmissions(files: File[]): Promise<Submission[]> {
        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }

        const response = await fetch('/api/submissions', {
            method: 'POST',
            body: formData,
        });
        return handleResponse<Submission[]>(response);
    },
};
