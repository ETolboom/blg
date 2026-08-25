import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from defusedxml.common import DefusedXmlException
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from checks.implementations.behavioral import BehavioralEvaluationError
from checks.manager import CheckRegistry
from demo_mode import demo_mode_enabled, demo_project, register_demo_mode
from dependencies import set_active_project
from schemas import ErrorResponse
from routers import projects, submissions, rubric
from routers import checks as checks_router
from routers import behavioral_rules, behavioral_rule_groups

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize global app state on startup.

    Only the (global) check registry is loaded here. No project is active until
    the client selects one via the projects API — at which point the rubric,
    rule manager and submission service are built for that project.
    """
    registry = CheckRegistry()
    registry.load()
    app.state.check_registry = registry

    # Ensure the multi-project layout exists.
    os.makedirs(os.path.join(app.state.data_root, "assignments"), exist_ok=True)
    os.makedirs(os.path.join(app.state.data_root, "templates"), exist_ok=True)

    # No project active until one is selected.
    app.state.active_project = None
    app.state.base_path = None
    app.state.rubric = None
    app.state.rule_manager = None
    app.state.submission_service = None

    # A pinned demo deployment starts with its one assignment already selected,
    # so visitors land in the grading UI rather than a single-item picker. Never
    # fatal: a bad pin leaves the app in the normal "pick a project" state.
    pinned = demo_project()
    if pinned and demo_mode_enabled():
        try:
            set_active_project(app, pinned)
        except Exception:
            logger.exception("Could not preselect DEMO_PROJECT=%r", pinned)

    yield


app = FastAPI(lifespan=lifespan)
register_demo_mode(app)


# Centralized exception handling: map common domain errors to the right status
# code and always return FastAPI's `{detail: "<string>"}` shape so the frontend
# can present clean messages. Unexpected errors are logged server-side and
# reported generically rather than leaking `str(e)` (internal paths, etc.).
# (HTTPException and request-body validation keep FastAPI's default handlers.)
def _error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content=ErrorResponse(detail=detail).model_dump()
    )


@app.exception_handler(FileNotFoundError)
async def _file_not_found_handler(request: Request, exc: FileNotFoundError):
    return _error_response(404, str(exc))


@app.exception_handler(ValueError)
async def _value_error_handler(request: Request, exc: ValueError):
    return _error_response(400, str(exc))


@app.exception_handler(DefusedXmlException)
async def _defused_xml_handler(request: Request, exc: DefusedXmlException):
    # A DefusedXmlException is a ValueError, so without this it would surface as
    # the generic 400 carrying defusedxml's internal repr. Say what's actually
    # wrong instead — legitimate BPMN never declares entities or a DTD.
    return _error_response(400, "Unsupported XML: DTD or entity declarations are not allowed")


@app.exception_handler(ValidationError)
async def _validation_error_handler(request: Request, exc: ValidationError):
    return _error_response(422, str(exc))


@app.exception_handler(BehavioralEvaluationError)
async def _behavioral_eval_error_handler(
    request: Request, exc: BehavioralEvaluationError
):
    # Expected, user-facing condition (e.g. a rule that doesn't match the model):
    # surface the message instead of masking it as a generic 500.
    return _error_response(422, str(exc))


@app.exception_handler(Exception)
async def _unhandled_error_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled error processing %s %s", request.method, request.url.path
    )
    return _error_response(500, "Internal server error")


app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(submissions.router, prefix="/api", tags=["submissions"])
app.include_router(rubric.router, prefix="/api", tags=["rubric"])
app.include_router(checks_router.router, prefix="/api", tags=["checks"])
app.include_router(behavioral_rules.router, prefix="/api", tags=["behavioral-rules"])
app.include_router(
    behavioral_rule_groups.router, prefix="/api", tags=["behavioral-rule-groups"]
)

_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(_FRONTEND_DIR):
    from fastapi.responses import FileResponse

    # Mount the static directory itself to serve JS, CSS, images (if any match)
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(_FRONTEND_DIR, "assets")),
        name="assets",
    )

    # Serve the favicon directly
    @app.get("/favicon.ico", include_in_schema=False)
    async def get_favicon():
        return FileResponse(os.path.join(_FRONTEND_DIR, "favicon.ico"))

    # Catch-all route to serve the SPA's index.html for any unhandled routes.
    # Exclude the /api prefix so an unmatched API path returns a real 404 rather
    # than HTML with status 200 (misleading for a mistyped/removed endpoint).
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a data root folder path")
        print("Usage: python main.py <data root>")
        sys.exit(1)

    data_root = sys.argv[1]

    # Initialize the multi-project data layout: <root>/assignments + <root>/templates
    if not os.path.exists(data_root):
        print(f"Directory '{data_root}' not found. Creating it...")
    os.makedirs(os.path.join(data_root, "assignments"), exist_ok=True)
    os.makedirs(os.path.join(data_root, "templates"), exist_ok=True)

    # Validate checks load before serving (dependencies loaded automatically)
    try:
        registry = CheckRegistry()
        registry.load()
    except Exception as e:
        print(f"Could not load checks: {e}")
        sys.exit(1)

    # Set data_root before lifespan runs
    app.state.data_root = data_root

    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    uvicorn.run(app, host="0.0.0.0", port=8000)
