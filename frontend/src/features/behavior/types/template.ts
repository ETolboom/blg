import type { Edge, Node } from "@vue-flow/core";

export interface BehavioralRule {
    id: string;
    name: string;
    description: string;
    maxPoints: number;
    nodes: Node[];
    edges: Edge[];
}