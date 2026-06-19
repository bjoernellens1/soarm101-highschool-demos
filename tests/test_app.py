from fastapi.testclient import TestClient

from soarm101_workshop.api.app import create_app
from soarm101_workshop.api.settings import get_settings


def test_openapi():
    get_settings.cache_clear()
    c = TestClient(create_app())
    assert c.get("/openapi.json").status_code == 200


def test_health_open():
    get_settings.cache_clear()
    c = TestClient(create_app())
    assert c.get("/api/health").status_code == 200
