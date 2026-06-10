import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from checks.implementations.behavioral import (
    MatchDetail,
    WorkflowData,
    BehavioralRuleCheck,
)
from dependencies import (
    get_rule_manager,
    get_submission_service,
    recompute_reference_eval,
)
from rules.manager import BehavioralRule, BehavioralRuleManager
from schemas import MessageResponse
from services.submissions import SubmissionService
from utils import safe_join

router = APIRouter()


class AffectedGroup(BaseModel):
    """A group re-evaluated as a side effect of validating one of its rules."""

    group_id: str
    group_name: str


class ValidationResult(BaseModel):
    """Per-node match results for a single rule validation.

    Reuses the ``MatchDetail`` dataclass directly as the item type (Pydantic v2
    serializes stdlib dataclasses), so the match shape isn't duplicated here.
    """

    fulfilled: bool
    confidence: float
    total_matches: int
    earned_points: float
    match_details: list[MatchDetail] = []
    problematic_elements: list[str] = []


class RuleValidationResponse(BaseModel):
    rule_id: str
    rule_name: str
    validation_result: ValidationResult
    affected_groups: list[AffectedGroup] = []


@router.get("/behavioral-rule-templates")
async def get_templates(
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
) -> list[dict]:
    """List all available rule templates"""
    return rule_manager.list_templates()


@router.get("/behavioral-rules")
async def get_rules(
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
) -> list[dict]:
    """List all available rules"""
    return rule_manager.list_rules()


@router.get("/behavioral-rules/{rule_id}")
async def get_rule(
    rule_id: str, rule_manager: BehavioralRuleManager = Depends(get_rule_manager)
) -> BehavioralRule:
    """Get a specific rule by ID"""
    rule = rule_manager.get_rule(rule_id)

    if rule is None:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")

    return rule


@router.post("/behavioral-rules")
async def create_rule(
    rule: BehavioralRule,
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
) -> BehavioralRule:
    """Create a new behavioral rule."""
    # Check if rule already exists
    if rule_manager.rule_exists(rule.id):
        raise HTTPException(
            status_code=409,
            detail=f"Rule with ID '{rule.id}' already exists. Use PUT to update.",
        )

    return rule_manager.save_rule(rule)


@router.put("/behavioral-rules/{rule_id}")
async def update_rule(
    rule_id: str,
    rule: BehavioralRule,
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
) -> BehavioralRule:
    """Update an existing behavioral rule."""
    # Ensure the rule ID in the URL matches the one in the body
    if rule.id != rule_id:
        raise HTTPException(
            status_code=400,
            detail=f"Rule ID in URL ('{rule_id}') doesn't match ID in body ('{rule.id}')",
        )

    # Check if rule exists
    if not rule_manager.rule_exists(rule_id):
        raise HTTPException(
            status_code=404,
            detail=f"Rule '{rule_id}' not found. Use POST to create.",
        )

    return rule_manager.save_rule(rule)


@router.delete("/behavioral-rules/{rule_id}")
async def delete_rule(
    rule_id: str, rule_manager: BehavioralRuleManager = Depends(get_rule_manager)
) -> MessageResponse:
    """Delete a behavioral rule by ID."""
    if not rule_manager.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")

    return MessageResponse(message=f"Rule '{rule_id}' deleted successfully")


@router.post("/behavioral-rules/{rule_id}/validate")
async def validate_rule(
    rule_id: str,
    request: Request,
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
    submission_service: SubmissionService = Depends(get_submission_service),
    filename: str | None = None,
) -> RuleValidationResponse:
    """
    Validate a behavioral rule against a BPMN model.

    When `filename` is provided, evaluates against that submission (read-only, no rubric changes).
    When omitted, evaluates against the reference BPMN and updates the rubric entry and any
    affected groups.
    """
    base_path = submission_service.base_path
    # rubric is optional here: only the reference branch needs it.
    rubric = request.app.state.rubric

    # Get the rule
    rule = rule_manager.get_rule(rule_id)

    if rule is None:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")

    # Resolve the BPMN XML to evaluate against
    if filename is not None:
        submission_path = safe_join(os.path.join(base_path, "submissions"), filename)
        if not os.path.exists(submission_path):
            raise HTTPException(
                status_code=404, detail=f"Submission '{filename}' not found"
            )
        with open(submission_path, encoding="utf-8") as f:
            model_xml = f.read()
    else:
        if not rubric or not rubric.assignment or not rubric.assignment.reference_xml:
            raise HTTPException(
                status_code=400,
                detail="No reference BPMN model loaded. Please load a rubric first.",
            )
        model_xml = rubric.assignment.reference_xml

    # Convert rule to WorkflowData
    workflow_data = WorkflowData(nodes=rule.nodes, edges=rule.edges)

    # Run behavioral analysis
    checker = BehavioralRuleCheck(model_xml=model_xml)
    result = checker.check_behavior(workflow=workflow_data)

    affected_groups: list[AffectedGroup] = []

    if filename is None:
        # Validating against the reference: the rule definition on disk may
        # have just changed, so recompute the whole reference evaluation
        # (this rule + any groups containing it) and invalidate cached
        # submission evaluations. Nothing is written into the rubric
        # definition or group files anymore.
        recompute_reference_eval(request.app)
        submission_service.invalidate_all_results()

        for group_info in rule_manager.list_groups():
            if rule_id in group_info.get("rule_ids", []):
                affected_groups.append(
                    AffectedGroup(
                        group_id=group_info["group_id"],
                        group_name=group_info["name"],
                    )
                )

    return RuleValidationResponse(
        rule_id=rule_id,
        rule_name=rule.name,
        validation_result=ValidationResult(
            fulfilled=result.fulfilled,
            confidence=result.confidence,
            total_matches=result.total_matches,
            earned_points=result.earned_points,
            match_details=result.match_details,
            problematic_elements=result.problematic_elements,
        ),
        affected_groups=affected_groups,
    )
