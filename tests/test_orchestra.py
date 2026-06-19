import pytest
from fastapi.testclient import TestClient

import soarm101_workshop.api.routers.processes as proc
from soarm101_workshop.api.app import create_app
from soarm101_workshop.api.auth import require_token
from soarm101_workshop.api.service import ProcessManager
from soarm101_workshop.api.settings import get_settings
from soarm101_workshop.commands import build_reset, build_safe_home
from soarm101_workshop.config import get_rig


@pytest.fixture
def client(tmp_path, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setattr(proc, "build_replay", lambda rig, repo, ep: ["bash", "-c", "sleep 3"])
    monkeypatch.setattr(proc, "build_safe_home", lambda rig: ["bash", "-c", "sleep 1"])
    monkeypatch.setattr(proc, "build_reset", lambda rig: ["bash", "-c", "echo reset"])
    monkeypatch.setattr(proc, "manager", ProcessManager(logs_dir=tmp_path, pidfile=tmp_path / "p.json"))
    app = create_app()
    app.dependency_overrides[require_token] = lambda: None
    return TestClient(app)


def test_build_safe_home_uses_follower():
    cmd = build_safe_home(get_rig("rig01"))
    assert "soarm101_workshop.safe_home" in cmd
    assert "hs_rig01_follower" in cmd


def test_safe_home_endpoint(client):
    r = client.post("/api/rigs/station_1/safe-home")
    assert r.status_code == 200 and r.json()["key"] == "rig01/safe-home"


def test_build_reset_targets_rig():
    cmd = build_reset(get_rig("rig01"))
    assert cmd == ["python", "-m", "soarm101_workshop.reset_motors", "--rig", "rig01"]


def test_reset_endpoint(client):
    r = client.post("/api/rigs/station_1/reset")
    assert r.status_code == 200 and r.json()["key"] == "rig01/reset"


def test_orchestra_launches_all_listed(client):
    r = client.post(
        "/api/orchestra/play",
        json={"repo_id": "local/wave_demo", "stations": ["station_1", "rig02"]},
    )
    assert r.status_code == 200
    keys = {x["key"] for x in r.json()}
    assert keys == {"rig01/orchestra", "rig02/orchestra"}
