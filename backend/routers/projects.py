import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from dependencies import set_active_project
from schemas import ActiveProjectResponse, ProjectActionResponse

router = APIRouter()


def _assignments_dir(request: Request) -> str:
    return os.path.join(request.app.state.data_root, "assignments")


@router.get("/projects")
async def list_projects(request: Request) -> list[str]:
    """List available assignment projects (subdirectories of assignments/)."""
    assignments = _assignments_dir(request)
    if not os.path.isdir(assignments):
        return []
    return sorted(
        d
        for d in os.listdir(assignments)
        if os.path.isdir(os.path.join(assignments, d))
    )


@router.get("/projects/active")
async def get_active_project(request: Request) -> ActiveProjectResponse:
    """Return the currently active project (or null if none selected)."""
    return ActiveProjectResponse(active_project=request.app.state.active_project)


@router.post("/projects/{name}/select")
async def select_project(name: str, request: Request) -> ProjectActionResponse:
    """Select an existing project, (re)initializing app state for it."""
    try:
        set_active_project(request.app, name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")
    return ProjectActionResponse(
        message=f"Project '{name}' selected", active_project=name
    )


class CreateProjectRequest(BaseModel):
    name: str


@router.post("/projects")
async def create_project(
    body: CreateProjectRequest, request: Request
) -> ProjectActionResponse:
    """Create a new (empty) assignment project and make it active.

    The new project has no rubric yet — the client then runs onboarding
    (POST /rubric) to populate it.
    """
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name is required")

    project_dir = os.path.join(_assignments_dir(request), name)
    if os.path.exists(project_dir):
        raise HTTPException(
            status_code=409, detail=f"Project '{name}' already exists"
        )

    os.makedirs(os.path.join(project_dir, "submissions"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "rules"), exist_ok=True)

    set_active_project(request.app, name)
    return ProjectActionResponse(
        message=f"Project '{name}' created", active_project=name
    )
