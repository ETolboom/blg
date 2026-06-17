import { ApiError, apiGet, apiPatch, apiPost, handleResponse } from './api';
import { Criterion, Rubric } from "@/features/rubric/types/rubric";

// Sentinel "filename" that refers to the reference model rather than a submission.
// Must match the backend REFERENCE_FILENAME (services/submissions.py).
export const REFERENCE_FILENAME = "Reference";

export interface Submission {
    filename: string;
    name: string;
    analyzed: boolean;
}

export const submissionService = {
    async getSubmissions(): Promise<Submission[]> {
        return apiGet<Submission[]>('/submissions');
    },

    async getSubmission(filename: string): Promise<string> {
        return apiGet<string>(`/submissions/${encodeURIComponent(filename)}`);
    },

    async saveSubmission(filename: string, criteria: Criterion[]): Promise<void> {
        return apiPatch<void>(
            `/submissions/${encodeURIComponent(filename)}`,
            JSON.stringify(criteria),
            'application/json'
        );
    },

    async regradeCriterionThreshold(
        filename: string,
        criterionId: string,
        threshold: number | null,
        idealThreshold: number | null
    ): Promise<Rubric> {
        return apiPost<Rubric>(
            `/submissions/${encodeURIComponent(filename)}/criteria/${encodeURIComponent(criterionId)}/regrade`,
            JSON.stringify({ threshold, ideal_threshold: idealThreshold }),
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

    // Download an .xlsx export of the selected submissions. The response is a
    // binary workbook (not JSON/text), so it bypasses the apiPost wrapper and
    // triggers a browser download from the returned blob.
    async exportSubmissions(
        filenames: string[],
        includeThresholds: boolean,
        includeNotes: boolean
    ): Promise<void> {
        const response = await fetch('/api/submissions/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filenames,
                include_thresholds: includeThresholds,
                include_notes: includeNotes,
            }),
        });

        if (!response.ok) {
            let detail = await response.text().catch(() => undefined);
            try {
                const parsed = detail ? JSON.parse(detail) : undefined;
                if (parsed && typeof parsed === 'object' && 'detail' in parsed) {
                    detail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail);
                }
            } catch {
                // Not JSON, leave detail as text.
            }
            throw new ApiError(response.status, response.statusText, detail);
        }

        const blob = await response.blob();
        const disposition = response.headers.get('content-disposition') ?? '';
        const match = disposition.match(/filename=([^;]+)/i);
        const downloadName = match?.[1]?.trim().replace(/^"|"$/g, '') || 'submissions.xlsx';

        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = downloadName;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    },
};
