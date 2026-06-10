import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request

from checks import CheckComplexity, StringFormInput
from checks.implementations.behavioral import (
    BehavioralGroupEvaluator,
    GroupEvaluationResult,
)
from dependencies import (
    get_rubric,
    get_rule_manager,
    get_submission_service,
    save_rubric,
)
from rubric import CriterionDefinition, RubricDefinition
from rules.manager import (
    BehavioralRuleGroup,
    BehavioralRuleManager,
)
from schemas import MessageResponse
from services.submissions import REFERENCE_FILENAME, SubmissionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/behavioral-rule-groups")
async def list_rule_groups(
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
) -> list[dict]:
    """List all available template groups"""
    return rule_manager.list_groups()


@router.get("/behavioral-rule-groups/{group_id}")
async def get_rule_group(
    group_id: str,
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
) -> BehavioralRuleGroup:
    """Retrieve an existing group definition."""
    group = rule_manager.get_group(group_id)
    if group is None:
        raise HTTPException(status_code=404, detail=f"Group '{group_id}' not found")
    return group


@router.post("/behavioral-rule-groups")
async def create_rule_group(
    group: BehavioralRuleGroup,
    request: Request,
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
) -> BehavioralRuleGroup:
    """Create a new group definition."""
    # Check if group already exists
    if rule_manager.group_exists(group.group_id):
        raise HTTPException(
            status_code=409,
            detail=f"Group with ID '{group.group_id}' already exists. Use PUT to update.",
        )

    # Validate that all referenced rules exist (raises ValueError -> 400)
    rule_manager.validate_group_rules(group)
    return rule_manager.save_group(group)


@router.put("/behavioral-rule-groups/{group_id}")
async def update_template_group(
    group_id: str,
    group: BehavioralRuleGroup,
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
) -> BehavioralRuleGroup:
    """Update existing template group"""
    # Ensure group_id matches
    if group.group_id != group_id:
        raise HTTPException(
            status_code=400,
            detail=f"Group ID in URL ('{group_id}') doesn't match ID in body ('{group.group_id}')",
        )

    # Check if group exists
    if not rule_manager.group_exists(group_id):
        raise HTTPException(
            status_code=404,
            detail=f"Group '{group_id}' not found. Use POST to create.",
        )

    # Validate that all templates exist (raises ValueError -> 400)
    rule_manager.validate_group_rules(group)
    return rule_manager.save_group(group)


@router.delete("/behavioral-rule-groups/{group_id}")
async def delete_rule_group(
    group_id: str, rule_manager: BehavioralRuleManager = Depends(get_rule_manager)
) -> MessageResponse:
    """Delete template group"""
    success = rule_manager.delete_group(group_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Group '{group_id}' not found")
    return MessageResponse(message=f"Group '{group_id}' deleted successfully")


@router.post("/rubric/criteria/behavioral-group/analyze")
def analyze_behavioral_group(
    group: BehavioralRuleGroup,
    request: Request,
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
    filename: str | None = None,
) -> GroupEvaluationResult:
    """Evaluate a group definition against a named submission, or the reference
    model when ``filename`` is omitted."""
    base_path = request.app.state.base_path

    if filename is not None:
        submission_path = os.path.join(base_path, "submissions", filename)
        if not os.path.exists(submission_path):
            raise HTTPException(
                status_code=404, detail=f"Submission '{filename}' not found"
            )
        with open(submission_path, encoding="utf-8") as f:
            model_xml = f.read()
    else:
        rubric = request.app.state.rubric
        if not rubric or not rubric.assignment or not rubric.assignment.reference_xml:
            raise HTTPException(status_code=400, detail="No reference model loaded")
        model_xml = rubric.assignment.reference_xml

    evaluator = BehavioralGroupEvaluator(model_xml=model_xml, rule_manager=rule_manager)
    return evaluator.evaluate_group(group)


@router.post("/rubric/criteria/behavioral-group/{group_id}")
async def add_behavioral_group_to_rubric(
    group_id: str,
    group: BehavioralRuleGroup,
    request: Request,
    rubric: RubricDefinition = Depends(get_rubric),
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
    submission_service: SubmissionService = Depends(get_submission_service),
):
    """Add template group as rubric criterion"""
    # Ensure group_id matches
    if group.group_id != group_id:
        raise HTTPException(
            status_code=400,
            detail=f"Group ID in URL ('{group_id}') doesn't match ID in body ('{group.group_id}')",
        )

    rule_manager.validate_group_rules(group)
    rule_manager.save_group(group)

    # Remove individual templates from rubric
    for rule_id in group.rule_ids:
        index = next((i for i, c in enumerate(rubric.criteria) if c.id == rule_id), -1)
        if index != -1:
            logger.info(
                "Removing template '%s' from rubric (consumed by group)", rule_id
            )
            del rubric.criteria[index]

    # Use "group:" prefix to distinguish from individual templates in rubric
    prefixed_group_id = f"group:{group.group_id}"

    # Remove duplicates (if group already in rubric)
    index = next(
        (i for i, c in enumerate(rubric.criteria) if c.id == prefixed_group_id), -1
    )
    if index != -1:
        del rubric.criteria[index]

    # Add the group to the rubric definition with a "group:" prefixed id
    # (the frontend identifies groups by that prefix). Scoring is handled by
    # the reference evaluation that save_rubric triggers.
    rubric.criteria.append(
        CriterionDefinition(
            id=prefixed_group_id,
            name=group.name,
            check_complexity=CheckComplexity.COMPLEX,
            inputs=[
                StringFormInput(
                    input_label="group_id",
                    data=group.group_id,
                )
            ],
            default_points=group.maxPoints or 0.0,
        )
    )

    save_rubric(request, rubric)

    return submission_service.compose_rubric(REFERENCE_FILENAME)
