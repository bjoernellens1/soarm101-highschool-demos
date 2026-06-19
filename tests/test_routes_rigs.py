import pytest
from fastapi.testclient import TestClient

from soarm101_workshop.api.app import create_app
from soarm101_workshop.api.auth import require_token
from soarm101_workshop.api.settings import get_settings


@pytest.fixture
def client():
    get_settings.cache_clear()
    app = create_app()
    app.dependency_overrides[require_token] = lambda: None
    return TestClient(app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_rigs(client):
    r = client.get("/api/rigs")
    assert r.status_code == 200
    assert "rig01" in [x["name"] for x in r.json()]


def test_rig_404(client):
    assert client.get("/api/rigs/nope").status_code == 404


def test_auth_required_without_override():
    get_settings.cache_clear()
    c = TestClient(create_app())  # token default "", no loopback bypass -> 401
    assert c.get("/api/rigs").status_code == 401
