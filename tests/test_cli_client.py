import httpx
import pytest

from soarm101_workshop.client.http import ApiClient


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/api/rigs":
        return httpx.Response(
            200,
            json=[{"name": "rig01", "label": "x", "follower": {}, "leader": {}, "cameras": {}}],
        )
    if path == "/api/rigs/nope":
        return httpx.Response(404, text="Unknown rig")
    if request.method == "POST" and path == "/api/rigs/rig01/teleop":
        return httpx.Response(200, json={"key": "rig01/teleop", "pid": 123, "cmd": "x"})
    if path == "/api/processes/rig01/teleop/stop":
        return httpx.Response(200, json={"stopped": "rig01/teleop"})
    return httpx.Response(200, json={})


def _client() -> ApiClient:
    return ApiClient("http://test", "t", transport=httpx.MockTransport(_handler))


def test_list_rigs():
    data = _client().get("/api/rigs")
    assert any(r["name"] == "rig01" for r in data)


def test_post_teleop_returns_key():
    assert _client().post("/api/rigs/rig01/teleop", {})["key"] == "rig01/teleop"


def test_sends_bearer_token():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json={})

    ApiClient("http://test", "tok", transport=httpx.MockTransport(handler)).get("/api/health")
    assert captured["auth"] == "Bearer tok"


def test_api_error_raises():
    with pytest.raises(SystemExit):
        _client().get("/api/rigs/nope")
