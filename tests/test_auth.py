import pytest
from fastapi import HTTPException
from starlette.requests import Request

from soarm101_workshop.api import auth
from soarm101_workshop.api.settings import Settings


def _req(headers=None, client=("1.2.3.4", 0)):
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": client,
    }
    return Request(scope)


def test_missing_token_401(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", lambda: Settings(token="secret"))
    with pytest.raises(HTTPException) as e:
        auth.require_token(_req())
    assert e.value.status_code == 401


def test_valid_token_ok(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", lambda: Settings(token="secret"))
    auth.require_token(_req({"Authorization": "Bearer secret"}))


def test_wrong_token_401(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", lambda: Settings(token="secret"))
    with pytest.raises(HTTPException):
        auth.require_token(_req({"Authorization": "Bearer nope"}))


def test_loopback_bypass(monkeypatch):
    monkeypatch.setattr(
        auth, "get_settings", lambda: Settings(token="secret", allow_localhost_no_auth=True)
    )
    auth.require_token(_req(client=("127.0.0.1", 0)))
