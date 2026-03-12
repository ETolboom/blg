import {apiPost} from "@/services/api.ts";
import {GraphEdge, GraphNode} from "@vue-flow/core";

export interface WorkflowData {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

export interface AlgorithmResult {
    id: string;
    name: string;
    category: string;
    description: string;
    fulfilled: boolean;
    confidence: number;
    problematic_elements: string[];
    inputs: string[];
}

export const behaviorService = {
    async gradeBehavior(data: WorkflowData) {
        return apiPost<AlgorithmResult>(
            `/rubric/criteria/behavioral/analyze`,
            JSON.stringify(data),
            'application/json'
        );
    },
};
