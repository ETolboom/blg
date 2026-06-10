import type { Node, Edge } from "@vue-flow/core";
import { Check } from "@/services/checkService.ts";
import { GroupCondition, RuleEvaluationResult } from "@/features/behavior/types/group";

// A rubric criterion is a Check (id/name/description/check_complexity/inputs)
// enriched with per-model grading state and the optional Template/Behavior and
// Group fields. Behavioral rules and groups both live under the COMPLEX
// category and are told apart by the `group:` id prefix (see isGroup()).
export interface Criterion extends Check {
    fulfilled: boolean;
    default_points: number;
    score: number | null;
    problematic_elements: string[];

    // Task Coverage info pop-up: expected tasks absent from the submission, and
    // submission tasks that matched no expected task.
    coverage_detail?: {
        missing: string[];
        unexpected: string[];
    };

    // Template/Behavior specific
    nodes?: Node[];
    edges?: Edge[];

    // Group specific
    condition?: GroupCondition;
    rule_ids?: string[];
    rule_results?: RuleEvaluationResult[];
    best_rule_id?: string;
    overall_confidence?: number;
    maxPoints?: number;
    rules?: {
        id: string;
        name: string;
        description: string;
        maxPoints: number;
    }[];

    // Per-model group evaluation breakdown (composed onto group criteria by the backend)
    group_result?: {
        best_rule_id?: string | null;
        earned_points: number;
        rule_results: RuleEvaluationResult[];
    };
}

export interface Assignment {
    reference_xml: string;
    id: string;
}

export interface Rubric {
    assignment: Assignment;
    criteria: Criterion[];
}