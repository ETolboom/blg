import os

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from checks import Check, CheckFormInput
from checks.manager import CheckRegistry
from dependencies import (
    get_check_registry,
    get_rubric,
    get_rule_manager,
    get_submission_service,
)
from rubric import Rubric, RubricDefinition
from rules.manager import BehavioralRuleManager
from services.evaluation import evaluate_model
from services.submissions import REFERENCE_FILENAME, SubmissionService
from utils import safe_join

router = APIRouter()


class NodeData(BaseModel):
    id: str
    name: str
    description: str


class Node(BaseModel):
    key: str
    data: NodeData
    children: list["Node"] | None = None


@router.get("/checks")
async def list_checks(
    registry: CheckRegistry = Depends(get_check_registry),
) -> list[dict[str, str | list[CheckFormInput]]]:
    """Return metadata for all registered checks."""
    return registry.list_checks()


@router.post("/checks/analyze", response_model=None)
async def analyze_submission(
    filename: str,
    rubric: RubricDefinition = Depends(get_rubric),
    registry: CheckRegistry = Depends(get_check_registry),
    rule_manager: BehavioralRuleManager = Depends(get_rule_manager),
    submission_service: SubmissionService = Depends(get_submission_service),
) -> Rubric:
    """Analyze a student submission against the rubric and return the composed result."""
    if filename == "":
        raise HTTPException(status_code=404, detail="No filename provided")

    if filename == REFERENCE_FILENAME:
        return submission_service.compose_rubric(REFERENCE_FILENAME)

    submission = safe_join(submission_service.submissions_path, filename)

    if os.path.exists(submission + ".json"):
        # We already have an analyzed result.
        return submission_service.compose_rubric(filename)

    if not os.path.exists(submission):
        raise HTTPException(status_code=404, detail="Submission not found")

    with open(submission, encoding="utf-8") as f:
        model_xml = f.read()

    result = evaluate_model(model_xml, rubric.criteria, registry, rule_manager)
    submission_service.write_eval(filename, result)

    return submission_service.compose_rubric(filename)


@router.post("/checks/analyze/all")
async def analyze_all(
    req: Request, registry: CheckRegistry = Depends(get_check_registry)
) -> list[Node]:
    """Return all applicable checks for a given BPMN model, grouped by complexity category."""
    model_xml = await req.body()
    if not model_xml:
        raise HTTPException(status_code=400, detail="request body is missing")

    manager = registry.create_manager(model_xml.decode())
    available_checks = manager.list_checks()

    applicable_checks: dict[str, list[Check]] = {}
    for entry in available_checks:
        check_id = str(entry["id"])
        check = manager.get_check(check_id)
        if check.is_applicable():
            # We order checks by category
            if check.check_complexity in applicable_checks:
                applicable_checks[check.check_complexity].append(check)
            else:
                applicable_checks[check.check_complexity] = [check]

    nodes: list[Node] = []

    node_idx = 0
    for category in applicable_checks:
        inner_nodes = []
        for inner_node_idx, check in enumerate(applicable_checks[category]):
            inner_nodes.append(
                Node(
                    key=str(node_idx) + "-" + str(inner_node_idx),
                    data=NodeData(
                        id=check.id,
                        name=check.name,
                        description=check.description,
                    ),
                )
            )

        nodes.append(
            Node(
                key=str(node_idx),
                data=NodeData(
                    id="",
                    name=category,
                    description="",
                ),
                children=inner_nodes,
            )
        )

        node_idx += 1

    return nodes
