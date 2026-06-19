from __future__ import annotations

from fastapi import HTTPException, Request

from .settings import get_settings

_LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def require_token(request: Request) -> None:
    settings = get_settings()
    if (
        settings.allow_localhost_no_auth
        and request.client
        and request.client.host in _LOOPBACK
    ):
        return
    header = request.headers.get("Authorization", "")
    token = header[7:] if header.startswith("Bearer ") else ""
    if not settings.token or token != settings.token:
        raise HTTPException(status_code=401, detail="Missing or invalid API token")
