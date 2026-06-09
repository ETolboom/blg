import { apiGet, apiPost } from './api';

export interface ActiveProject {
    active_project: string | null;
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
