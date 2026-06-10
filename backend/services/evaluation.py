import logging

from checks import CheckComplexity
from checks.implementations.behavioral import (
    BehavioralGroupEvaluator,
    BehavioralRuleCheck,
    WorkflowData,
)
from checks.manager import CheckRegistry
from rubric import (
    CriterionDefinition,
    GroupResultSummary,
    SubmissionCriterionResult,
    SubmissionResult,
)
from rules.manager import BehavioralRuleManager, RuleEvaluationSummary

logger = logging.getLogger(__name__)


def _problematic_from_matches(match_details) -> list[str]:
    """Collect BPMN element ids that are below threshold or at the wrong distance."""
    problematic: list[str] = []
    for match in match_details:
        if (
            not match.is_correct
            or not match.is_ideal_match
            or not match.is_ideal_distance
        ):
            if match.bpmn_element_id not in problematic:
                problematic.append(match.bpmn_element_id)
    return problematic


def evaluate_model(
    model_xml: str,
    criteria: list[CriterionDefinition],
    registry: CheckRegistry,
    rule_manager: BehavioralRuleManager,
) -> SubmissionResult:
    """Evaluate one BPMN model against the rubric definition.

    A criterion whose backing rule/group is missing on disk is recorded as
    unfulfilled (rather than aborting the whole evaluation), so one broken
    reference can't nuke an entire grade.
    """
    manager = registry.create_manager(model_xml)
    results: list[SubmissionCriterionResult] = []

    for crit in criteria:
        if crit.check_complexity != CheckComplexity.COMPLEX:
            # Standard, model-agnostic / configurable check
            result = manager.get_check(crit.id).analyze(inputs=crit.inputs)
            results.append(
                SubmissionCriterionResult(
                    id=result.id,
                    fulfilled=result.fulfilled,
                    confidence=result.confidence,
                    problematic_elements=result.problematic_elements,
                    score=None,
                    detail=result.detail,
                )
            )
            continue

        # COMPLEX → behavioral group or individual rule
        if crit.id.startswith("group:"):
            group = rule_manager.get_group(crit.id[len("group:") :])
            if group is None:
                logger.warning("Group for criterion '%s' missing on disk", crit.id)
                results.append(_unfulfilled(crit))
                continue

            evaluator = BehavioralGroupEvaluator(
                model_xml=model_xml, rule_manager=rule_manager
            )
            g = evaluator.evaluate_group(group)
            summary = GroupResultSummary(
                best_rule_id=g.best_rule_id or None,
                earned_points=g.earned_points,
                rule_results=[
                    RuleEvaluationSummary(
                        rule_id=r.rule_id,
                        rule_name=r.rule_name,
                        description=r.description,
                        earned_points=r.earned_points,
                        confidence=r.confidence,
                        success=r.success,
                        problematic_elements=_problematic_from_matches(r.match_details),
                    )
                    for r in g.rule_results
                ],
            )
            results.append(
                SubmissionCriterionResult(
                    id=crit.id,
                    fulfilled=g.fulfilled,
                    confidence=g.overall_confidence,
                    problematic_elements=g.problematic_elements,
                    score=_score_or_none(g.earned_points, group.maxPoints),
                    inputs=crit.inputs,
                    group_result=summary,
                )
            )
            continue

        # Individual behavioral rule
        rule = rule_manager.get_rule(crit.id)
        if rule is None:
            logger.warning("Rule for criterion '%s' missing on disk", crit.id)
            results.append(_unfulfilled(crit))
            continue

        checker = BehavioralRuleCheck(model_xml=model_xml)
        try:
            r = checker.check_behavior(
                workflow=WorkflowData(nodes=rule.nodes, edges=rule.edges)
            )
        except Exception as e:
            logger.warning("Rule '%s' evaluation failed: %s", crit.id, e)
            results.append(_unfulfilled(crit))
            continue

        results.append(
            SubmissionCriterionResult(
                id=crit.id,
                fulfilled=r.earned_points > 0,
                confidence=r.confidence,
                problematic_elements=_problematic_from_matches(r.match_details),
                score=_score_or_none(r.earned_points, rule.maxPoints),
                inputs=crit.inputs,
            )
        )

    return SubmissionResult(criteria=results)


def _unfulfilled(crit: CriterionDefinition) -> SubmissionCriterionResult:
    return SubmissionCriterionResult(
        id=crit.id,
        fulfilled=False,
        confidence=0.0,
        problematic_elements=[],
        score=None,
        inputs=crit.inputs,
    )


def _score_or_none(earned: float, max_points: float | None) -> float | None:
    """Store an explicit score only when it differs from the criterion's max.

    Matches existing behaviour: a full-marks result leaves ``score`` null so the
    rubric falls back to ``default_points``.
    """
    if round(earned, 2) == round(max_points or 0.0, 2):
        return None
    return earned
