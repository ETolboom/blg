"""Shared Pydantic models for API response envelopes.

These describe the JSON shapes the API returns for acknowledgements and errors,
as opposed to the domain models (rubric, rules, checks). Keeping them typed lets
FastAPI document them in OpenAPI and keeps the wire contract in sync with the
frontend service types.
"""

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Generic success acknowledgement: ``{"message": "..."}``."""

    message: str


class ActiveProjectResponse(BaseModel):
    """The currently active project, or ``null`` when none is selected."""

    active_project: str | None
    # True when a demo deployment is pinned to a single project: the frontend
    # then skips the picker and hides the create/switch controls, since there
    # is nothing else to switch to.
    demo_locked: bool = False


class ProjectActionResponse(MessageResponse):
    """Acknowledgement for selecting/creating a project (always active after)."""

    active_project: str


class SupplementUploadResponse(MessageResponse):
    """Acknowledgement after uploading a rubric supplement PDF."""

    filename: str


class DeleteCriterionResponse(MessageResponse):
    """Result of deleting a rubric criterion.

    For group criteria, ``unmerged_rules`` lists the individual rules restored to
    the rubric and ``warning`` flags any that could not be restored.
    """

    unmerged_rules: list[str] = Field(default_factory=list)
    warning: str | None = None


class ErrorResponse(BaseModel):
    """Error envelope: ``{"detail": "..."}`` (matches FastAPI's HTTPException)."""

    detail: str
