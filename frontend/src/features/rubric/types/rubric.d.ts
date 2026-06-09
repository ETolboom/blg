import { Check } from "@/services/checkService.ts";
import { GroupCondition, RuleEvaluationResult } from "@/features/behavior/types/group";
import { CheckComplexityType } from "@/features/rubric/types/check_complexity";

export interface Criterion {
    id?: string;
    name: string;
    description: string;
    fulfilled: boolean;
    default_points: number;
    score: number | null;
    problematic_elements: string[];
    check_complexity: CheckComplexityType;

    // Check specific
    inputs?: CheckInput[];

    // Template/Behavior specific
    nodes?: any[];
    edges?: any[];

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