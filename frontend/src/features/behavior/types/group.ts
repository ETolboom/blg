
export type GroupCondition = "XOR" | "AND";

export interface BehavioralRuleGroup {
    group_id: string;
    name: string;
    maxPoints?: number;
    condition: GroupCondition;
    rule_ids: string[];
    rule_results: RuleEvaluationResult[];

    // Evaluation results (embedded after evaluation)
    last_evaluation?: string | null;    // ISO 8601 timestamp
    earned_points?: number | null;        // MAX score from templates
    best_rule_id?: string | null;   // Template with best score
    fulfilled?: boolean | null;         // Whether requirements met
    confidence?: number | null;         // Overall confidence (0.0-1.0)
    problematic_elements?: string[] | null;  // BPMN element IDs with issues
}

// Single source of truth lives in validation.ts; re-exported here so existing
// imports from this module keep working.
export type { MatchDetail } from "@/features/behavior/types/validation";
import type { MatchDetail } from "@/features/behavior/types/validation";

export interface RuleEvaluationResult {
    rule_id: string;
    rule_name: string;
    description?: string;
    earned_points: number;
    confidence: number;
    // Present on the live validate/analyze response, but NOT on the persisted
    // per-model group summary (which carries `problematic_elements` instead).
    match_details?: MatchDetail[];
    problematic_elements?: string[];
    success: boolean;
}

export interface GroupEvaluationResult {
    group_id: string;
    group_name: string;
    condition: GroupCondition;

    // Individual template results
    rule_results: RuleEvaluationResult[];

    // Aggregated results (MAX scoring)
    earned_points: number;           // MAX of template scores
    best_rule_id: string;      // Which template achieved max score
    overall_confidence: number;    // From best template

    // For rubric compatibility
    match_details: MatchDetail[];
    problematic_elements: string[];
    fulfilled: boolean;
}

export const isGroup = (criterion: { id?: string }): boolean => {
    return criterion.id?.startsWith('group:') ?? false;
};

export const getGroupId = (criterion: { id?: string }): string => {
    if (!isGroup(criterion)) {
        return criterion.id || '';
    }
    return criterion.id!.substring(6);
};
