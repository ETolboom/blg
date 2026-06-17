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

    // Per-submission deviations from the rubric definition.
    // `supports_threshold`/`default_threshold`/`default_ideal_threshold` come from
    // the definition; the `*_override` values (non-default matching cut-offs this
    // submission was graded with) and the notes come from the evaluation. The ideal
    // fields are null for checks with a single threshold.
    supports_threshold?: boolean;
    default_threshold?: number | null;
    default_ideal_threshold?: number | null;
    // Project-level overrides (the middle tier between the global default and the
    // per-submission override). Set from the Reference tab; null = inherit global.
    project_threshold?: number | null;
    project_ideal_threshold?: number | null;
    threshold_override?: number | null;
    ideal_threshold_override?: number | null;
    // Grader annotations split by audience: internal (between graders) and
    // feedback (for the student).
    internal_notes?: string | null;
    feedback_notes?: string | null;
    // Per-check labels/help for the threshold override fields, so the gear popover
    // reads correctly (a check's "minimum" can mean opposite leniency directions).
    // Absent for checks without overridable thresholds.
    threshold_label?: string | null;
    ideal_threshold_label?: string | null;
    threshold_hint?: string | null;

    // Optional breakdown shown in the criterion's (i) info pop-up. Generic across
    // checks (Task Coverage: missing/extra tasks; duplicate checks: matched pairs).
    detail?: {
        sections: {
            label: string;
            severity: 'error' | 'warn' | 'info';
            items: string[];
        }[];
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