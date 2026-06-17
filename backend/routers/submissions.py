from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from pydantic import BaseModel

from checks.manager import CheckRegistry
from dependencies import (
    get_check_registry,
    get_rubric,
    get_rule_manager,
    get_submission_service,
)
from rubric import Rubric, RubricDefinition, SubmissionCriterionResult
from rules.manager import BehavioralRuleManager
from services.evaluation import evaluate_criterion
from services.submissions import SubmissionService

router = APIRouter()


@router.get("/submissions")
async def get_submissions_list(
    service: SubmissionService = Depends(get_submission_service),
) -> list[dict]:
    """Return a list of all uploaded student submissions."""
    return service.list_submissions()


class ExportRequest(BaseModel):
    filenames: list[str]
    include_thresholds: bool = True
    include_internal_notes: bool = True
    include_feedback_notes: bool = True


@router.post("/submissions/export")
async def export_submissions(
    body: ExportRequest,
    service: SubmissionService = Depends(get_submission_service),
) -> Response:
    """Export the selected submissions into one .xlsx workbook, a worksheet per
    submission. The Threshold/notes columns are included per the request flags."""
    content = service.export_submissions(
        body.filenames,
        include_thresholds=body.include_thresholds,
        include_internal_notes=body.include_internal_notes,
        include_feedback_notes=body.include_feedback_notes,
    )

    # A single submission gets a file named after it; multiple share one workbook.
    if len(body.filenames) == 1:
        download_name = body.filenames[0].replace(".bpmn", ".xlsx")
    else:
        download_name = "submissions.xlsx"

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={download_name}"},
    )


@router.post("/submissions")
async def upload_submissions(
    files: list[UploadFile],
    service: SubmissionService = Depends(get_submission_service),
) -> list[dict]:
    """Upload one or more BPMN files to the submissions folder."""
    return await service.upload_submissions(files)


@router.get("/submissions/{filename}")
async def get_submission(
    filename: str, service: SubmissionService = Depends(get_submission_service)
) -> Response:
    """Return the raw BPMN XML for a specific submission."""
    xml = service.get_submission_xml(filename)
    return Response(content=xml, media_type="application/xml")


@router.patch("/submissions/{filename}")
async def update_submission(
    filename: str,
    criteria: list[SubmissionCriterionResult],
    service: SubmissionService = Depends(get_submission_service),
) -> None:
    """Manually update criterion results for a specific submission."""
    service.update_submission_criteria(filename, criteria)


class ThresholdOverrideRequest(BaseModel):
    # None resets the respective cut-off to the check's class default.
    threshold: float | None = None
    ideal_threshold: float | None = None


@router.post("/submissions/{filename}/criteria/{criterion_id}/regrade")
async def regrade_criterion_threshold(
    filename: str,
    criterion_id: str,
    body: ThresholdOverrideRequest,
    rubric: RubricDefinition = Depends(get_rubric),
    registry: CheckRegistry = Depends(get_check_registry),
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
    service: SubmissionService = Depends(get_submission_service),
) -> Rubric:
    crit = next((c for c in rubric.criteria if c.id == criterion_id), None)
    if crit is None:
        raise HTTPException(
            status_code=404, detail=f"Criterion '{criterion_id}' not found in rubric"
        )
    meta = registry.threshold_meta(criterion_id)
    if not meta.supports:
        raise HTTPException(
            status_code=400,
            detail=f"Criterion '{criterion_id}' does not support a threshold override",
        )

    # Record a submission override only when it differs from the *effective*
    # default (the project threshold when set, otherwise the global default), so
    # a value left at the inherited level reads as "no deviation" downstream.
    def _deviation(value: float | None, default: float | None) -> float | None:
        return None if value is None or value == default else value

    eff_default = (
        crit.project_threshold
        if crit.project_threshold is not None
        else meta.default_threshold
    )
    eff_ideal_default = (
        crit.project_ideal_threshold
        if crit.project_ideal_threshold is not None
        else meta.default_ideal_threshold
    )
    threshold = _deviation(body.threshold, eff_default)
    ideal_threshold = _deviation(body.ideal_threshold, eff_ideal_default)

    model_xml = service.get_submission_xml(filename)
    manager = registry.create_manager(model_xml)
    result = evaluate_criterion(
        crit,
        manager,
        model_xml,
        rule_manager,
        threshold=threshold,
        ideal_threshold=ideal_threshold,
    )
    service.apply_criterion_result(filename, result)

    return service.compose_rubric(filename)
