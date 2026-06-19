from __future__ import annotations

import os

import httpx


class ApiClient:
    def __init__(self, base_url: str | None = None, token: str | None = None, transport=None):
        self.base_url = base_url or os.environ.get("SOARM_API_URL", "http://127.0.0.1:7860")
        self.token = token if token is not None else os.environ.get("SOARM_API_TOKEN", "")
        self._client = httpx.Client(
            base_url=self.base_url,
            transport=transport,
            timeout=30,
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
        )

    def _handle(self, r: httpx.Response):
        if r.status_code >= 400:
            raise SystemExit(f"API error {r.status_code}: {r.text}")
        return r.json() if r.content else {}

    def get(self, path: str):
        return self._handle(self._client.get(path))

    def post(self, path: str, json: dict | None = None):
        return self._handle(self._client.post(path, json=json or {}))

    def delete(self, path: str):
        return self._handle(self._client.delete(path))
