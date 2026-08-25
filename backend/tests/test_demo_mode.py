import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from demo_mode import MAX_BODY_BYTES, register_demo_mode


def _build_app():
    app = FastAPI()
    register_demo_mode(app)

    @app.get("/api/thing")
    def get_thing():
        return {"ok": True}

    @app.post("/api/thing")
    def post_thing():
        return {"ok": True}

    @app.post("/api/projects")
    def create_project():
        return {"ok": True}

    @app.post("/api/projects/{name}/select")
    def select_project(name: str):
        return {"ok": True}

    @app.post("/api/checks/analyze/all")
    async def analyze_all(request: Request):
        await request.body()
        return {"ok": True}

    return app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("DEMO_PROJECT", raising=False)
    monkeypatch.setenv("DEMO_MODE", "1")
    app = _build_app()
    app.state.data_root = str(tmp_path)
    return TestClient(app), tmp_path


def test_get_requests_pass(client):
    c, _ = client
    assert c.get("/api/thing").status_code == 200


def test_mutating_post_blocked(client):
    c, _ = client
    r = c.post("/api/thing")
    assert r.status_code == 403
    assert r.json() == {"detail": "This action is disabled in the demo environment."}


def test_allowlisted_post_passes(client):
    c, _ = client
    assert c.post("/api/checks/analyze/all").status_code == 200


def test_project_select_passes(client):
    """Without this the landing screen can never open a project (403 on click)."""
    c, _ = client
    assert c.post("/api/projects/demo-assignment/select").status_code == 200


def test_pinned_project_is_the_only_one_selectable(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setenv("DEMO_PROJECT", "Webshop")
    app = _build_app()
    app.state.data_root = str(tmp_path)
    c = TestClient(app)

    assert c.post("/api/projects/Webshop/select").status_code == 200
    assert c.post("/api/projects/Other/select").status_code == 403


def test_project_creation_still_blocked(client):
    c, _ = client
    assert c.post("/api/projects").status_code == 403


def test_oversized_body_rejected(client):
    c, _ = client
    r = c.post(
        "/api/checks/analyze/all",
        content=b"x" * (MAX_BODY_BYTES + 1),
        headers={"content-type": "application/xml"},
    )
    assert r.status_code == 413


def test_oversized_chunked_body_rejected(client):
    """A chunked body carries no Content-Length, so the header check can't see it."""
    c, _ = client

    def chunks():
        for _ in range(3):
            yield b"x" * (MAX_BODY_BYTES // 2)

    r = c.post(
        "/api/checks/analyze/all",
        content=chunks(),
        headers={"content-type": "application/xml"},
    )
    assert r.status_code == 413


def test_body_at_limit_accepted(client):
    c, _ = client

    def chunks():
        yield b"x" * MAX_BODY_BYTES

    r = c.post(
        "/api/checks/analyze/all",
        content=chunks(),
        headers={"content-type": "application/xml"},
    )
    assert r.status_code == 200


def test_demo_mode_never_writes_to_the_data_root(client):
    """The demo data root is mounted read-only, so nothing may try to write it."""
    c, tmp_path = client
    c.get("/api/thing")
    c.post("/api/thing")
    c.post("/api/checks/analyze/all", content=b"<x/>")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("value", ["0", "false", "no", "", "off"])
def test_falsy_env_values_disable_demo_mode(tmp_path, monkeypatch, value):
    monkeypatch.setenv("DEMO_MODE", value)
    app = _build_app()
    app.state.data_root = str(tmp_path)
    assert TestClient(app).post("/api/thing").status_code == 200


def test_disabled_without_env_var(tmp_path, monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    app = _build_app()
    app.state.data_root = str(tmp_path)
    assert TestClient(app).post("/api/thing").status_code == 200
