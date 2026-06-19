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
    monkeypatch.setattr(proc, "build_teleop", lambda rig, **k: ["bash", "-c", "sleep 5"])
    monkeypatch.setattr(proc, "manager", ProcessManager(logs_dir=tmp_path, pidfile=tmp_path / "p.json"))
    app = create_app()
    app.dependency_overrides[require_token] = lambda: None
    return TestClient(app)


def test_start_status_stop(client):
    r = client.post("/api/rigs/rig01/teleop", json={})
    assert r.status_code == 200
    key = r.json()["key"]
    assert key == "rig01/teleop"
    st = client.get("/api/processes").json()
    assert st[key]["alive"] is True
    assert client.post(f"/api/processes/{key}/stop").status_code == 200


def test_unknown_action_404(client):
    assert client.post("/api/rigs/rig01/bogus", json={}).status_code == 404


def test_unknown_rig_404(client):
    assert client.post("/api/rigs/nope/teleop", json={}).status_code == 404


def test_record_validation_422(client):
    r = client.post("/api/rigs/rig01/record", json={"episodes": 0})
    assert r.status_code == 422


def test_stop_all(client):
    client.post("/api/rigs/rig01/teleop", json={})
    assert client.post("/api/processes/stop-all").status_code == 200


def test_auth_required():
    get_settings.cache_clear()
    c = TestClient(create_app())
    assert c.get("/api/processes").status_code == 401
