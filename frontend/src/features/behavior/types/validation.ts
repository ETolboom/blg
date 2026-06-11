/**
 * Match details for a single workflow node
 */
export interface MatchDetail {
  workflow_node_id: string;
  workflow_label: string;
  bpmn_element_id: string;
  bpmn_label: string;
  match_score: number;
  distance: number;
  ideal_distance: number;
  max_distance: number;
  minimal_match_threshold: number;  // Minimum acceptable threshold (0.6)
  ideal_match_threshold: number;    // Ideal threshold (0.8)
  is_correct: boolean;               // True if match_score >= minimal_match_threshold
  is_ideal_distance: boolean;        // True if distance == ideal_distance
  is_ideal_match: boolean;           // True if match_score >= ideal_match_threshold
}

/**
 * Validation result from backend
 */
export interface ValidationResult {
  fulfilled: boolean;
  confidence: number;
  total_matches: number;
  earned_points: number;
  match_details: MatchDetail[];
  problematic_elements: string[];
}

/**
 * Group affected by re-evaluation. Mirrors the backend AffectedGroup, which
 * sends only the identifier and name (no scores).
 */
export interface AffectedGroup {
  group_id: string;
  group_name: string;
}

/**
 * Complete validation response
 */
export interface ValidationResponse {
  rule_id: string;
  rule_name: string;
  validation_result: ValidationResult;
  affected_groups: AffectedGroup[];
}

/**
 * Node validation state (for UI visualization)
 */
export interface NodeValidationState {
  nodeId: string;
  matchDetail: MatchDetail | null;
  validationStatus: 'perfect' | 'good-wrong-position' | 'acceptable-not-ideal' | 'incorrect';
}
