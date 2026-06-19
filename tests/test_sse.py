import pytest
from fastapi.testclient import TestClient

import soarm101_workshop.api.routers.processes as proc
from soarm101_workshop.api.app import create_app
from soarm101_workshop.api.auth import require_token
from soarm101_workshop.api.service import ProcessManager
from soarm101_workshop.api.settings import get_settings


@pytest.fixture
def client(tmp_path, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setattr(
        proc, "build_teleop", lambda rig, **k: ["bash", "-c", "echo LINE1; echo LINE2; sleep 0.2"]
    )
    monkeypatch.setattr(proc, "manager", ProcessManager(logs_dir=tmp_path, pidfile=tmp_path / "p.json"))
    app = create_app()
    app.dependency_overrides[require_token] = lambda: None
    return TestClient(app)


def test_sse_streams_log_lines(client):
    client.post("/api/rigs/rig01/teleop", json={})
    with client.stream("GET", "/api/processes/rig01/teleop/logs") as r:
        body = ""
        for chunk in r.iter_text():
            body += chunk
            if "LINE2" in body:
                break
    assert "LINE1" in body and "LINE2" in body
