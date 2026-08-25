import { apiGet, apiPost } from './api';

export interface ActiveProject {
    active_project: string | null;
    // Set by a demo deployment pinned to a single assignment: there is nothing
    // to pick or switch to, so the picker and create/switch controls are hidden.
    demo_locked?: boolean;
}

export const projectService = {
    async getProjects(): Promise<string[]> {
        return apiGet<string[]>('/projects');
    },

    async getActiveProject(): Promise<ActiveProject> {
        return apiGet<ActiveProject>('/projects/active');
    },

    async selectProject(name: string): Promise<ActiveProject> {
        return apiPost<ActiveProject>(`/projects/${encodeURIComponent(name)}/select`);
    },

    async createProject(name: string): Promise<ActiveProject> {
        return apiPost<ActiveProject>(
            '/projects',
            JSON.stringify({ name }),
            'application/json'
        );
    },
};
