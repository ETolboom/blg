import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel

from checks import (
    CheckComplexity,
    CheckFormInput,
    CheckResult,
    StringFormInput,
)
from checks.implementations.behavioral import WorkflowData, BehavioralRuleCheck
from checks.manager import CheckRegistry
from dependencies import (
    get_check_registry,
    get_rubric,
    get_rule_manager,
    get_submission_service,
    save_rubric,
)
from rubric import (
    CriterionDefinition,
    OnboardingRubric,
    Rubric,
    RubricDefinition,
)
from rules.manager import BehavioralRule, BehavioralRuleManager
from schemas import (
    DeleteCriterionResponse,
    MessageResponse,
    SupplementUploadResponse,
)
from services.submissions import REFERENCE_FILENAME, SubmissionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/rubric")
async def get_current_rubric(
    _rubric: RubricDefinition = Depends(get_rubric),
    submission_service: SubmissionService = Depends(get_submission_service),
) -> Rubric:
    """Return the composed reference rubric (definitions + reference evaluation)."""
    return submission_service.compose_rubric(REFERENCE_FILENAME)


class ReferenceUpdateRequest(BaseModel):
    reference_xml: str


@router.put("/rubric/reference")
async def update_reference(
    body: ReferenceUpdateRequest,
    request: Request,
    rubric: RubricDefinition = Depends(get_rubric),
    submission_service: SubmissionService = Depends(get_submission_service),
) -> MessageResponse:
    """Overwrite reference.bpmn on disk and update app state."""
    with open(os.path.join(submission_service.base_path, "reference.bpmn"), "w") as f:
        f.write(body.reference_xml)

    rubric.assignment.reference_xml = body.reference_xml
    save_rubric(request, rubric)

    return MessageResponse(message="Reference updated successfully")


@router.post("/rubric")
async def handle_onboarding_rubric(
    onboarding_rubric: OnboardingRubric,
    request: Request,
    registry: CheckRegistry = Depends(get_check_registry),
    submission_service: SubmissionService = Depends(get_submission_service),
) -> Rubric:
    """Create and persist a new rubric definition from an onboarding payload.

    A first-pass ``analyze(inputs=None)`` is run per selected check only to
    extract its default configuration (e.g. reference task labels), which is
    stored as the criterion *definition*. Scoring is left to the reference
    evaluation that ``save_rubric`` triggers. Requires an active project (no
    existing rubric required — this creates it).
    """
    base_path = submission_service.base_path

    ref_xml = (
        onboarding_rubric.assignment.reference_xml
        if onboarding_rubric.assignment and onboarding_rubric.assignment.reference_xml
        else ""
    )
    manager = registry.create_manager(ref_xml)

    definitions: list[CriterionDefinition] = []
    for algorithm in onboarding_rubric.checks:
        check = manager.get_check(algorithm)
        result = check.analyze(inputs=None)
        definitions.append(
            CriterionDefinition(
                id=result.id,
                name=result.name,
                description=result.description,
                check_complexity=result.check_complexity,
                inputs=result.inputs,
                default_points=1.0 if check.awards_points else 0.0,
            )
        )

    new_rubric = RubricDefinition(
        criteria=definitions,
        assignment=onboarding_rubric.assignment,
    )

    # Write reference XML to separate file before persisting (so the reference
    # evaluation triggered by save_rubric can read it).
    if ref_xml:
        with open(os.path.join(base_path, "reference.bpmn"), "w") as f:
            f.write(ref_xml)

    save_rubric(request, new_rubric)

    return submission_service.compose_rubric(REFERENCE_FILENAME)


@router.post("/rubric/criteria/behavioral/analyze")
def analyze_behavioral_criteria(
    data: WorkflowData,
    rubric: RubricDefinition = Depends(get_rubric),
) -> CheckResult:
    """Run a behavioral rule check against the reference BPMN and return the result."""
    alg = BehavioralRuleCheck(model_xml=rubric.assignment.reference_xml)
    return alg.check_behavior(workflow=data)


@router.post("/rubric/criteria/behavioral/{behavioral_id}")
async def add_behavioral_criteria(
    behavioral_id: str,
    inputs: BehavioralRule,
    request: Request,
    rubric: RubricDefinition = Depends(get_rubric),
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
    submission_service: SubmissionService = Depends(get_submission_service),
) -> Rubric:
    """Save a behavioral rule and add (or replace) it as a criterion in the rubric."""
    # If no nodes/edges provided, try loading existing rule or seeding from template
    if len(inputs.nodes) == 0 and len(inputs.edges) == 0:
        template = rule_manager.get_template(inputs.id)
        if template is not None:
            inputs = template

    # Prevent any duplicates by removing old instances of the algorithm.
    index = next(
        (
            i
            for i, criterion in enumerate(rubric.criteria)
            if criterion.id == behavioral_id
        ),
        -1,
    )
    if index != -1:
        del rubric.criteria[index]

    # Save rule to disk
    rule_manager.save_rule(inputs)

    # Store only a reference to the rule ID in the rubric definition.
    # The actual rule data is loaded from disk when needed.
    rubric.criteria.append(
        CriterionDefinition(
            id=inputs.id,
            name=inputs.name,
            description=inputs.description,
            check_complexity=CheckComplexity.COMPLEX,
            inputs=[
                StringFormInput(
                    input_label="template_id",
                    data=inputs.id,  # Only store the rule ID
                ),
            ],
            default_points=inputs.maxPoints,
        )
    )

    save_rubric(request, rubric)

    return submission_service.compose_rubric(REFERENCE_FILENAME)


@router.post("/rubric/criteria/{algorithm_id}")
async def update_criteria(
    algorithm_id: str,
    inputs: list[CheckFormInput],
    request: Request,
    rubric: RubricDefinition = Depends(get_rubric),
    registry: CheckRegistry = Depends(get_check_registry),
    submission_service: SubmissionService = Depends(get_submission_service),
) -> Rubric:
    """Run a standard check with the provided inputs and upsert the result as a rubric criterion."""
    # Prevent any duplicates by removing old instances of the algorithm.
    index = next(
        (
            i
            for i, criterion in enumerate(rubric.criteria)
            if criterion.id == algorithm_id
        ),
        -1,
    )
    if index != -1:
        del rubric.criteria[index]

    if rubric and rubric.assignment and rubric.assignment.reference_xml:
        manager = registry.create_manager(rubric.assignment.reference_xml)
    else:
        manager = registry.create_manager("")
    # Run the check once to capture its configured inputs as the definition.
    check = manager.get_check(algorithm_id)
    result = check.analyze(inputs=inputs)
    rubric.criteria.append(
        CriterionDefinition(
            id=algorithm_id,
            name=result.name,
            description=result.description,
            check_complexity=result.check_complexity,
            inputs=result.inputs,
            default_points=1.0 if check.awards_points else 0.0,
        )
    )

    save_rubric(request, rubric)

    return submission_service.compose_rubric(REFERENCE_FILENAME)


@router.post("/rubric/supplement")
async def upload_supplement(
    file: UploadFile,
    submission_service: SubmissionService = Depends(get_submission_service),
) -> SupplementUploadResponse:
    """Upload a supplement PDF for the rubric."""
    base_path = submission_service.base_path

    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF document")

    # Validate content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {file.content_type}. Expected application/pdf",
        )

    # Read and validate file size (10MB limit)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=400, detail="PDF file size must not exceed 10MB"
        )

    # Save to disk
    supplement_path = os.path.join(base_path, "supplement.pdf")
    with open(supplement_path, "wb") as f:
        f.write(content)

    logger.info("Supplement PDF uploaded successfully")

    return SupplementUploadResponse(
        message="Supplement uploaded successfully", filename="supplement.pdf"
    )


@router.get("/rubric/supplement")
async def get_supplement(
    submission_service: SubmissionService = Depends(get_submission_service),
) -> Response:
    """Retrieve the supplement PDF if it exists."""
    supplement_path = os.path.join(submission_service.base_path, "supplement.pdf")

    if not os.path.exists(supplement_path):
        raise HTTPException(status_code=404, detail="No supplement PDF found")

    with open(supplement_path, "rb") as f:
        content = f.read()

    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=supplement.pdf"},
    )


@router.delete("/rubric/supplement")
async def delete_supplement(
    submission_service: SubmissionService = Depends(get_submission_service),
) -> MessageResponse:
    """Delete the supplement PDF."""
    supplement_path = os.path.join(submission_service.base_path, "supplement.pdf")

    if not os.path.exists(supplement_path):
        raise HTTPException(status_code=404, detail="No supplement PDF found")

    os.remove(supplement_path)
    logger.info("Supplement PDF deleted")

    return MessageResponse(message="Supplement deleted successfully")


@router.delete("/rubric/criteria/{criterion_id}")
async def delete_rubric_criterion(
    criterion_id: str,
    request: Request,
    rubric: RubricDefinition = Depends(get_rubric),
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
) -> DeleteCriterionResponse:
    """Delete a rubric criterion; for group criteria, restores the individual templates first."""
    # Find criterion
    index = next((i for i, c in enumerate(rubric.criteria) if c.id == criterion_id), -1)

    if index == -1:
        raise HTTPException(
            status_code=404,
            detail=f"Criterion '{criterion_id}' not found in rubric",
        )

    # Check if group (needs unmerge) or individual template (simple delete)
    if criterion_id.startswith("group:"):
        return await _unmerge_and_delete_group(
            criterion_id, index, rubric, request, rule_manager
        )
    else:
        # Simple deletion for individual templates
        del rubric.criteria[index]

        save_rubric(request, rubric)

        return DeleteCriterionResponse(
            message=f"Criterion '{criterion_id}' deleted successfully"
        )


async def _unmerge_and_delete_group(
    criterion_id: str,
    index: int,
    rubric: RubricDefinition,
    request: Request,
    rule_manager: BehavioralRuleManager,
) -> DeleteCriterionResponse:
    """Remove a group criterion and restore its constituent template criteria in the rubric."""
    # Extract group_id (remove "group:" prefix)
    group_id = criterion_id[6:]

    # Load group from disk
    group = rule_manager.get_group(group_id)

    if group is None:
        # Group file not found - cleanup orphaned reference
        del rubric.criteria[index]

        save_rubric(request, rubric)

        return DeleteCriterionResponse(
            message=f"Group criterion '{criterion_id}' deleted (group file not found)",
            warning="Group metadata not found - could not restore rules",
        )

    # Restore templates at group's position
    restored = []
    missing = []
    insert_position = index  # Insert where the group was

    for template_id in group.rule_ids:
        template = rule_manager.get_rule(template_id)

        if template is None:
            missing.append(template_id)
            logger.warning("[Unmerge] Template '%s' not found on disk", template_id)
            continue

        # Check if already in rubric (avoid duplicates)
        exists = any(c.id == template_id for c in rubric.criteria)
        if exists:
            logger.info(
                "[Unmerge] Template '%s' already in rubric, skipping", template_id
            )
            continue

        # Insert template at group's position
        rubric.criteria.insert(
            insert_position,
            CriterionDefinition(
                id=template.id,
                name=template.name,
                description=template.description,
                check_complexity=CheckComplexity.COMPLEX,
                inputs=[
                    StringFormInput(
                        input_label="template_id",
                        data=template.id,
                    ),
                ],
                default_points=template.maxPoints,
            ),
        )

        restored.append(template_id)
        insert_position += 1  # Next template inserts after this one
        logger.info(
            "[Unmerge] Restored template '%s' at position %d",
            template_id,
            insert_position - 1,
        )

    # Delete group criterion (now at insert_position due to insertions)
    del rubric.criteria[insert_position]

    save_rubric(request, rubric)

    return DeleteCriterionResponse(
        message=f"Group '{criterion_id}' deleted and unmerged",
        unmerged_rules=restored,
        warning=f"Some rules not found: {missing}" if missing else None,
    )
