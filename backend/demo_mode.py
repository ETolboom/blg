import os
import re

from fastapi import FastAPI
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_BODY_BYTES = 2 * 1024 * 1024  # 2 MB

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Endpoints the frontend needs that use POST but don't persist anything. They
# accept arbitrary BPMN XML, so they stay protected by the body limit above
# (and, in the demo deployment, by Traefik rate limiting).
ALLOWED_POST_PATHS = frozenset(
    {
        "/api/checks/analyze",
        "/api/checks/analyze/all",
        "/api/rubric/criteria/behavioral/analyze",
        "/api/rubric/criteria/behavioral-group/analyze",
        "/api/submissions/export",
    }
)

# Selecting a project only swaps in-memory app state, so it's safe read-only --
# but a pinned deployment (DEMO_PROJECT) accepts its own project and nothing
# else. Handled separately from the set above because of the path parameter.
_SELECT_RE = re.compile(r"^/api/projects/([^/]+)/select$")

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def demo_mode_enabled() -> bool:
    """Whether read-only demo mode is on.

    The value is parsed rather than tested for emptiness so that the obvious
    ways of switching it off (``DEMO_MODE=0``, ``DEMO_MODE=false``) do.
    """
    return os.environ.get("DEMO_MODE", "").strip().lower() in _TRUTHY


def demo_project() -> str | None:
    """The single assignment a demo deployment is pinned to, if any.

    Pinning selects the project at startup (so visitors land straight in the
    grading UI) and makes it the only one that can be selected afterwards.
    """
    return os.environ.get("DEMO_PROJECT", "").strip() or None


def _post_allowed(path: str) -> bool:
    if path in ALLOWED_POST_PATHS:
        return True

    match = _SELECT_RE.match(path)
    if match is None:
        return False

    pinned = demo_project()
    return pinned is None or match.group(1) == pinned


async def _send_error(scope: Scope, send: Send, status_code: int, detail: str) -> None:
    await JSONResponse(status_code=status_code, content={"detail": detail})(
        scope, _no_receive, send
    )


async def _no_receive() -> Message:  # pragma: no cover - responses never read it
    return {"type": "http.disconnect"}


class _BodyTooLarge(Exception):
    """Raised from the wrapped receive channel once the body cap is exceeded."""


def _limited_receive(receive: Receive) -> Receive:
    """Wrap a receive channel so it counts the body bytes it hands out."""
    received = 0

    async def limited() -> Message:
        nonlocal received
        message = await receive()
        if message["type"] == "http.request":
            received += len(message.get("body", b""))
            if received > MAX_BODY_BYTES:
                raise _BodyTooLarge
        return message

    return limited


class DemoModeMiddleware:
    """Read-only guard for the public demo deployment.

    Written as raw ASGI rather than an ``@app.middleware("http")`` function so
    it can wrap the receive channel: a ``Content-Length`` header is optional
    (a chunked body has none), so the cap has to be enforced on the bytes that
    actually arrive rather than on what the client claims to be sending.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not demo_mode_enabled():
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        if not path.startswith("/api"):
            await self.app(scope, receive, send)
            return

        if scope["method"] not in SAFE_METHODS and not _post_allowed(path):
            await _send_error(
                scope, send, 403, "This action is disabled in the demo environment."
            )
            return

        # Reject early when the client declares an oversized body; the byte
        # counter below is what actually enforces the cap.
        content_length = Headers(scope=scope).get("content-length")
        if content_length and content_length.isdigit():
            if int(content_length) > MAX_BODY_BYTES:
                await _send_error(scope, send, 413, "Request body too large.")
                return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, _limited_receive(receive), send_wrapper)
        except _BodyTooLarge:
            if not response_started:
                await _send_error(scope, send, 413, "Request body too large.")


def register_demo_mode(app: FastAPI) -> None:
    app.add_middleware(DemoModeMiddleware)
