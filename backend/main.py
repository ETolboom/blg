import logging
import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from checks.manager import CheckRegistry
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

    yield


app = FastAPI(lifespan=lifespan)

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
    app.mount("/assets", StaticFiles(directory=os.path.join(_FRONTEND_DIR, "assets")), name="assets")

    # Serve the favicon directly
    @app.get("/favicon.ico", include_in_schema=False)
    async def get_favicon():
        return FileResponse(os.path.join(_FRONTEND_DIR, "favicon.ico"))

    # Catch-all route to serve the SPA's index.html for any unhandled routes
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
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

    # logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(app, host="0.0.0.0", port=8000)
