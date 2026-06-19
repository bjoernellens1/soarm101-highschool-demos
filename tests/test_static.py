from fastapi.testclient import TestClient

from soarm101_workshop.api.app import create_app
from soarm101_workshop.api.settings import get_settings


def test_index_served():
    get_settings.cache_clear()
    c = TestClient(create_app())
    r = c.get("/")
    assert r.status_code == 200 and "SO-ARM101" in r.text


def test_appjs_served():
    get_settings.cache_clear()
    c = TestClient(create_app())
    assert c.get("/app.js").status_code == 200
