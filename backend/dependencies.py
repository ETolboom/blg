import json
import logging
import os

from fastapi import HTTPException, Request

from checks.manager import CheckRegistry
from rubric import Assignment, RubricDefinition
from rules.manager import BehavioralRuleManager
from services.evaluation import evaluate_model
from services.submissions import REFERENCE_FILENAME, SubmissionService
from utils import safe_join

logger = logging.getLogger(__name__)


def get_check_registry(request: Request) -> CheckRegistry:
    """Return the global CheckRegistry (always available after startup)."""
    return request.app.state.check_registry


def get_submission_service(request: Request) -> SubmissionService:
    """Return the active project's SubmissionService, or 404 if none selected."""
    service = request.app.state.submission_service
    if service is None:
        raise HTTPException(status_code=404, detail="No project selected")
    return service


def get_rule_manager(request: Request) -> BehavioralRuleManager:
    """Return the active project's BehavioralRuleManager, or 404 if none selected."""
    manager = request.app.state.rule_manager
    if manager is None:
        raise HTTPException(status_code=404, detail="No project selected")
    return manager


def get_rubric(request: Request) -> RubricDefinition:
    """Return the active project's rubric definition, or 404 if none loaded.

    404 here is meaningful: a freshly created project has no rubric yet, which
    the frontend treats as "needs onboarding".
    """
    rubric = request.app.state.rubric
    if rubric is None:
        raise HTTPException(status_code=404, detail="No rubric loaded")
    return rubric


def recompute_reference_eval(app) -> None:
    """Re-evaluate the reference model and persist ``reference.bpmn.json``.

    The reference is treated as just another evaluated model, so re-running this
    after any rubric/reference change keeps the reference rubric in sync (and
    makes "recheck the reference" automatic).
    """
    rubric: RubricDefinition | None = app.state.rubric
    service: SubmissionService | None = app.state.submission_service
    if rubric is None or service is None:
        return

    ref_bpmn = os.path.join(service.base_path, "reference.bpmn")
    if not os.path.exists(ref_bpmn):
        return

    with open(ref_bpmn, encoding="utf-8") as f:
        model_xml = f.read()

    result = evaluate_model(
        model_xml, rubric.criteria, app.state.check_registry, app.state.rule_manager
    )
    service.write_eval(REFERENCE_FILENAME, result)


def load_rubric_definition(project_dir: str) -> RubricDefinition | None:
    """Load a RubricDefinition from a project dir, attaching the reference XML.

    Returns None if the project has no (valid) rubric yet.
    Which callers treat as "needs onboarding".
    """
    path = os.path.join(project_dir, "rubric.json")
    if not os.path.exists(path):
        return None

    try:
        with open(path, encoding="utf-8") as f:
            rubric = RubricDefinition(**json.load(f))
    except Exception as e:
        logger.error("Could not load rubric.json in %s: %s", project_dir, e)
        return None

    ref_path = os.path.join(project_dir, "reference.bpmn")
    if os.path.exists(ref_path):
        with open(ref_path, encoding="utf-8") as f:
            if rubric.assignment is None:
                rubric.assignment = Assignment()
            rubric.assignment.reference_xml = f.read()

    return rubric


def set_active_project(app, name: str) -> None:
    """Make ``name`` the active assignment: (re)build the rule manager,
    submission service and rubric for that project's directory."""
    data_root = app.state.data_root
    # `name` is client-supplied (landing screen) -> confine it under assignments/.
    project_dir = safe_join(os.path.join(data_root, "assignments"), name)
    if not os.path.isdir(project_dir):
        raise FileNotFoundError(f"Project '{name}' not found")

    rubric = load_rubric_definition(project_dir)

    app.state.active_project = name
    app.state.base_path = project_dir
    app.state.rule_manager = BehavioralRuleManager(
        rules_dir=os.path.join(project_dir, "rules"),
        templates_dir=os.path.join(data_root, "templates"),
    )
    app.state.rubric = rubric
    app.state.submission_service = SubmissionService(
        project_dir, rubric, check_registry=app.state.check_registry
    )

    # Populate the reference evaluation on first selection (cached thereafter;
    # kept fresh by save_rubric on any subsequent rubric/reference change).
    if rubric is not None and not os.path.exists(
        os.path.join(project_dir, "reference.bpmn.json")
    ):
        recompute_reference_eval(app)


def save_rubric(request: Request, rubric: RubricDefinition) -> None:
    """Persist the rubric *definition* to app state and disk, then invalidate
    cached submission results and recompute the reference evaluation."""
    service: SubmissionService = request.app.state.submission_service
    request.app.state.rubric = rubric
    service.rubric = rubric

    with open(os.path.join(service.base_path, "rubric.json"), "w") as f:
        f.write(rubric.to_disk_json())

    service.invalidate_all_results()
    recompute_reference_eval(request.app)
