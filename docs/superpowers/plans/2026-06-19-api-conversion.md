# API-Based Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the SO-ARM101 workshop project into a production-ready FastAPI service that is the single source of truth for all rig operations, with a thin static UI and a CLI HTTP client.

**Architecture:** FastAPI + Uvicorn (single worker, serial is exclusive). Pure command builders (`commands.py`) are composed by an async-safe `ProcessManager` (`api/service.py`). Routers expose JSON endpoints + an SSE log stream. Bearer-token auth. The CLI and a static SPA are clients of the API.

**Tech Stack:** FastAPI, Uvicorn, Pydantic v2 / pydantic-settings, httpx, sse-starlette, pytest, lerobot 0.4.4.

## Global Constraints

- Python >= 3.12.
- **Single worker only** — serial ports are exclusive; never run >1 worker.
- Reuse `config.py` and the pure builders in `commands.py`; do not duplicate the lerobot command construction.
- All `/api/*` routes require a Bearer token except `/api/health` and the OpenAPI docs; loopback may bypass when `SOARM_ALLOW_LOCALHOST_NO_AUTH=1`.
- Process keys are `"{rig}/{action}"`; action names hyphenated (`calibrate-follower`).
- `ruff check` (line-length 100) must pass; every task ends green.
- Tests must not require real hardware (use a fake fast subprocess); a separate manual hardware smoke is the final acceptance gate.

---

### Task 1: Dependencies, settings, package skeleton

**Files:**
- Modify: `pyproject.toml` (deps, scripts, pytest config)
- Create: `src/soarm101_workshop/api/__init__.py`
- Create: `src/soarm101_workshop/api/settings.py`
- Test: `tests/test_settings.py`

**Interfaces:**
- Produces: `Settings` (pydantic-settings) with `.token`, `.host`, `.port`, `.config_path`, `.allow_localhost_no_auth`, `.cors_origins`; `get_settings()` cached accessor.

- [ ] **Step 1: Update pyproject deps/scripts**

```toml
dependencies = [
  "fastapi>=0.110",
  "uvicorn[standard]>=0.29",
  "httpx>=0.27",
  "pydantic-settings>=2.2",
  "sse-starlette>=2.1",
  "opencv-python>=4.8",
  "numpy>=1.24",
  "pyyaml>=6.0",
]
# remove flask

[project.optional-dependencies]
robot = ["lerobot[feetech]"]
dev = ["ruff", "pytest", "pytest-asyncio", "httpx"]

[project.scripts]
soarm-api = "soarm101_workshop.api.app:run"
soarm-workshop = "soarm101_workshop.cli:main"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Write failing test**

```python
# tests/test_settings.py
from soarm101_workshop.api.settings import Settings

def test_defaults(monkeypatch):
    monkeypatch.delenv("SOARM_API_TOKEN", raising=False)
    s = Settings()
    assert s.host == "127.0.0.1"
    assert s.port == 7860
    assert s.config_path == "configs/arms.yaml"
    assert s.allow_localhost_no_auth is False

def test_env_override(monkeypatch):
    monkeypatch.setenv("SOARM_API_TOKEN", "secret")
    monkeypatch.setenv("SOARM_PORT", "9000")
    s = Settings()
    assert s.token == "secret"
    assert s.port == 9000
```

- [ ] **Step 3: Implement settings**

```python
# src/soarm101_workshop/api/settings.py
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SOARM_", env_file=".env", extra="ignore")
    token: str = ""
    host: str = "127.0.0.1"
    port: int = 7860
    config_path: str = "configs/arms.yaml"
    allow_localhost_no_auth: bool = False
    cors_origins: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Note: env var is `SOARM_API_TOKEN` (prefix `SOARM_` + field `api_token`)? No — field is `token`, so the env var is `SOARM_TOKEN`. To honor the spec name `SOARM_API_TOKEN`, add `validation_alias`:

```python
from pydantic import Field
    token: str = Field(default="", validation_alias="SOARM_API_TOKEN")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_settings.py -v`  Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/soarm101_workshop/api tests/test_settings.py
git commit -m "feat(api): deps, settings, api package skeleton"
```

---

### Task 2: Pydantic request/response models

**Files:**
- Create: `src/soarm101_workshop/api/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `TeleopParams`, `RecordParams`, `ReplayParams`, `CalibrateParams`,
  `ProcessStatus`, `RigInfo`, `ArmInfo`, `HealthInfo`, `PortInfo`, `ActionResult`.

- [ ] **Step 1: Failing test**

```python
# tests/test_models.py
import pytest
from pydantic import ValidationError
from soarm101_workshop.api.models import RecordParams, ReplayParams

def test_record_defaults():
    p = RecordParams()
    assert p.episodes == 5 and p.resume is False and p.display_data is False

def test_record_bounds():
    with pytest.raises(ValidationError):
        RecordParams(episodes=0)
    with pytest.raises(ValidationError):
        RecordParams(episode_time_s=10_000)

def test_replay_requires_repo_id():
    with pytest.raises(ValidationError):
        ReplayParams()
    assert ReplayParams(repo_id="local/x").episode == 0
```

- [ ] **Step 2: Run → FAIL (module missing)**

- [ ] **Step 3: Implement models**

```python
# src/soarm101_workshop/api/models.py
from __future__ import annotations
from pydantic import BaseModel, Field


class TeleopParams(BaseModel):
    display_data: bool = False
    no_cameras: bool = False


class CalibrateParams(BaseModel):
    pass


class RecordParams(BaseModel):
    hf_user: str = "local"
    dataset_name: str | None = None
    episodes: int = Field(5, ge=1, le=50)
    episode_time_s: int = Field(20, ge=5, le=600)
    reset_time_s: int = Field(10, ge=0, le=120)
    push_to_hub: bool = False
    resume: bool = False
    display_data: bool = False
    no_cameras: bool = False


class ReplayParams(BaseModel):
    repo_id: str
    episode: int = Field(0, ge=0)


class ArmInfo(BaseModel):
    role: str
    type: str
    id: str
    port: str


class RigInfo(BaseModel):
    name: str
    label: str
    task_text: str
    follower: ArmInfo
    leader: ArmInfo
    cameras: dict


class ProcessStatus(BaseModel):
    key: str
    alive: bool
    returncode: int | None
    started_at: float
    cmd: str
    log: str = ""


class ActionResult(BaseModel):
    key: str
    pid: int
    cmd: str


class HealthInfo(BaseModel):
    status: str = "ok"
    version: str


class PortInfo(BaseModel):
    devices: list[str]
```

- [ ] **Step 4: Run → PASS**
- [ ] **Step 5: Commit** `feat(api): pydantic models`

---

### Task 3: ProcessManager service (lifecycle moved out of commands.py)

**Files:**
- Create: `src/soarm101_workshop/api/service.py`
- Modify: `src/soarm101_workshop/commands.py` (remove module-global `_RUNNING`, `start_process`, `stop_process`, `clear_process`, `status`, `RunningCommand`; keep pure builders + `shell_join` + `camera_exists` + `run_blocking`)
- Test: `tests/test_service.py`

**Interfaces:**
- Consumes: builders from `commands.py`.
- Produces: `ProcessManager` with async methods `start(key, cmd) -> RunningProc`,
  `stop(key) -> bool`, `stop_all()`, `clear(key)`, `status() -> dict[str, dict]`,
  `reconcile()`; dataclass `RunningProc(key, cmd, pid, pgid, started_at)`. Module
  singleton `manager`.

- [ ] **Step 1: Failing tests (use a fake fast subprocess; no hardware)**

```python
# tests/test_service.py
import asyncio, time
import pytest
from soarm101_workshop.api.service import ProcessManager

@pytest.mark.asyncio
async def test_start_status_stop(tmp_path):
    m = ProcessManager(logs_dir=tmp_path, pidfile=tmp_path / "p.json")
    rp = await m.start("t/teleop", ["bash", "-c", "echo hi; sleep 5"])
    assert rp.pid > 0
    st = m.status()["t/teleop"]
    assert st["alive"] is True
    assert await m.stop("t/teleop") is True
    await asyncio.sleep(0.2)
    assert "t/teleop" not in m.status()

@pytest.mark.asyncio
async def test_exit_is_reflected(tmp_path):
    m = ProcessManager(logs_dir=tmp_path, pidfile=tmp_path / "p.json")
    await m.start("t/x", ["bash", "-c", "echo done"])
    await asyncio.sleep(0.3)
    st = m.status()["t/x"]
    assert st["alive"] is False and st["returncode"] == 0

@pytest.mark.asyncio
async def test_stop_all_and_reconcile(tmp_path):
    pf = tmp_path / "p.json"
    m = ProcessManager(logs_dir=tmp_path, pidfile=pf)
    await m.start("t/a", ["bash", "-c", "sleep 5"])
    await m.start("t/b", ["bash", "-c", "sleep 5"])
    await m.stop_all()
    await asyncio.sleep(0.2)
    assert m.status() == {}
    # pidfile cleared
    m2 = ProcessManager(logs_dir=tmp_path, pidfile=pf)
    killed = await m2.reconcile()
    assert killed == 0
```

- [ ] **Step 2: Run → FAIL**

- [ ] **Step 3: Implement service** (port the hardened logic; add async lock, pidfile)

```python
# src/soarm101_workshop/api/service.py
from __future__ import annotations
import asyncio, json, os, signal, subprocess, time
from dataclasses import dataclass, field
from pathlib import Path

from ..commands import shell_join


@dataclass
class RunningProc:
    key: str
    cmd: list[str]
    process: subprocess.Popen
    pid: int
    pgid: int
    started_at: float = field(default_factory=time.time)


def _read_log_tail(log_path: Path, max_bytes: int = 4000, max_lines: int = 20) -> str:
    if not log_path.exists():
        return ""
    try:
        with log_path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - max_bytes))
            text = f.read().decode("utf-8", errors="replace")
        return "\n".join(text.splitlines()[-max_lines:])
    except OSError as e:
        return f"<log read error: {e}>"


class ProcessManager:
    def __init__(self, logs_dir: Path = Path("logs"), pidfile: Path | None = None):
        self.logs_dir = Path(logs_dir)
        self.pidfile = Path(pidfile) if pidfile else self.logs_dir / ".processes.json"
        self._procs: dict[str, RunningProc] = {}
        self._lock = asyncio.Lock()

    def log_path(self, key: str) -> Path:
        return self.logs_dir / f"{key.replace('/', '_')}.log"

    def _persist(self) -> None:
        data = {k: {"pid": p.pid, "pgid": p.pgid, "cmd": p.cmd} for k, p in self._procs.items()}
        self.pidfile.parent.mkdir(parents=True, exist_ok=True)
        self.pidfile.write_text(json.dumps(data))

    async def start(self, key: str, cmd: list[str]) -> RunningProc:
        await self.stop(key)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.log_path(key)
        async with self._lock:
            with log_path.open("ab") as log:
                log.write(("\n\n=== " + time.strftime("%Y-%m-%d %H:%M:%S") + " ===\n").encode())
                log.write(("+ " + shell_join(cmd) + "\n").encode())
                log.flush()
                proc = subprocess.Popen(
                    cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
                )
            rp = RunningProc(key=key, cmd=cmd, process=proc, pid=proc.pid, pgid=proc.pid)
            self._procs[key] = rp
            self._persist()
        return rp

    @staticmethod
    def _kill_group(pgid: int) -> None:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(pgid, sig)
            except OSError:
                return
            if sig is signal.SIGTERM:
                for _ in range(30):
                    try:
                        os.killpg(pgid, 0)
                    except OSError:
                        return
                    time.sleep(0.1)

    async def stop(self, key: str) -> bool:
        async with self._lock:
            rp = self._procs.get(key)
            if not rp:
                return False
            if rp.process.poll() is None:
                self._kill_group(rp.pgid)
            self._procs.pop(key, None)
            self._persist()
        return True

    async def stop_all(self) -> None:
        for key in list(self._procs):
            await self.stop(key)

    def clear(self, key: str) -> None:
        self._procs.pop(key, None)
        self._persist()

    def status(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for key, rp in list(self._procs.items()):
            alive = rp.process.poll() is None
            out[key] = {
                "key": key,
                "alive": alive,
                "returncode": rp.process.returncode,
                "started_at": rp.started_at,
                "cmd": shell_join(rp.cmd),
                "log": _read_log_tail(self.log_path(key)),
            }
        return out

    async def reconcile(self) -> int:
        """On startup, kill any process groups left from a previous run."""
        if not self.pidfile.exists():
            return 0
        try:
            data = json.loads(self.pidfile.read_text())
        except (OSError, ValueError):
            return 0
        killed = 0
        for entry in data.values():
            pgid = entry.get("pgid")
            if pgid is None:
                continue
            try:
                os.killpg(pgid, 0)
            except OSError:
                continue
            self._kill_group(pgid)
            killed += 1
        self.pidfile.write_text("{}")
        return killed


manager = ProcessManager()
```

- [ ] **Step 4: Run → PASS** (`pytest tests/test_service.py -v`)
- [ ] **Step 5: Commit** `feat(api): async ProcessManager with pgid + pidfile reconcile`

---

### Task 4: Auth dependency

**Files:**
- Create: `src/soarm101_workshop/api/auth.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes: `get_settings`.
- Produces: `require_token(request)` FastAPI dependency raising `HTTPException(401)`.

- [ ] **Step 1: Failing test**

```python
# tests/test_auth.py
import pytest
from fastapi import HTTPException
from starlette.requests import Request
from soarm101_workshop.api import auth
from soarm101_workshop.api.settings import Settings

def _req(headers=None, client=("1.2.3.4", 0)):
    scope = {"type": "http", "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()], "client": client}
    return Request(scope)

def test_missing_token_401(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", lambda: Settings(token="secret"))
    with pytest.raises(HTTPException) as e:
        auth.require_token(_req())
    assert e.value.status_code == 401

def test_valid_token_ok(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", lambda: Settings(token="secret"))
    auth.require_token(_req({"Authorization": "Bearer secret"}))

def test_loopback_bypass(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", lambda: Settings(token="secret", allow_localhost_no_auth=True))
    auth.require_token(_req(client=("127.0.0.1", 0)))
```

- [ ] **Step 2: Run → FAIL**
- [ ] **Step 3: Implement**

```python
# src/soarm101_workshop/api/auth.py
from __future__ import annotations
from fastapi import HTTPException, Request
from .settings import get_settings

_LOOPBACK = {"127.0.0.1", "::1", "localhost"}


def require_token(request: Request) -> None:
    settings = get_settings()
    if settings.allow_localhost_no_auth and request.client and request.client.host in _LOOPBACK:
        return
    header = request.headers.get("Authorization", "")
    token = header[7:] if header.startswith("Bearer ") else ""
    if not settings.token or token != settings.token:
        raise HTTPException(status_code=401, detail="Missing or invalid API token")
```

- [ ] **Step 4: Run → PASS**
- [ ] **Step 5: Commit** `feat(api): bearer-token auth dependency`

---

### Task 5: rigs router

**Files:**
- Create: `src/soarm101_workshop/api/routers/__init__.py`
- Create: `src/soarm101_workshop/api/routers/rigs.py`
- Test: `tests/test_routes_rigs.py`

**Interfaces:**
- Produces: `router` (APIRouter) with `/health`, `/rigs`, `/rigs/{rig}`, `/ports`.
- Consumes: `config.list_rigs/get_rig`, `models`, `auth.require_token`.

- [ ] **Step 1: Failing test (TestClient with auth bypass)**

```python
# tests/test_routes_rigs.py
import pytest
from fastapi.testclient import TestClient
from soarm101_workshop.api.app import create_app
from soarm101_workshop.api.settings import Settings, get_settings

@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides = {}
    get_settings.cache_clear()
    import soarm101_workshop.api.settings as s
    s.get_settings = lambda: Settings(token="t", allow_localhost_no_auth=True, config_path="configs/arms.yaml")
    return TestClient(app)

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"

def test_rigs(client):
    r = client.get("/api/rigs", headers={"Authorization": "Bearer t"})
    assert r.status_code == 200
    names = [x["name"] for x in r.json()]
    assert "rig01" in names

def test_rig_404(client):
    r = client.get("/api/rigs/nope", headers={"Authorization": "Bearer t"})
    assert r.status_code == 404
```

- [ ] **Step 2: Run → FAIL**
- [ ] **Step 3: Implement rigs router**

```python
# src/soarm101_workshop/api/routers/rigs.py
from __future__ import annotations
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from ... import __version__ if False else None  # noqa
from ..auth import require_token
from ..models import HealthInfo, PortInfo, RigInfo
from ..settings import get_settings
from ...config import get_rig, list_rigs

router = APIRouter(prefix="/api")
VERSION = "0.3.0"


def _rig_info(name: str, cfg: str) -> RigInfo:
    r = get_rig(name, cfg)
    return RigInfo(
        name=r.name, label=r.label, task_text=r.task_text,
        follower={"role": "follower", "type": r.follower.type, "id": r.follower.id, "port": r.follower.port},
        leader={"role": "leader", "type": r.leader.type, "id": r.leader.id, "port": r.leader.port},
        cameras=r.cameras,
    )


@router.get("/health", response_model=HealthInfo)
def health() -> HealthInfo:
    return HealthInfo(version=VERSION)


@router.get("/rigs", response_model=list[RigInfo], dependencies=[Depends(require_token)])
def rigs() -> list[RigInfo]:
    cfg = get_settings().config_path
    return [_rig_info(n, cfg) for n in list_rigs(cfg)]


@router.get("/rigs/{rig}", response_model=RigInfo, dependencies=[Depends(require_token)])
def rig(rig: str) -> RigInfo:
    cfg = get_settings().config_path
    try:
        return _rig_info(rig, cfg)
    except KeyError:
        raise HTTPException(404, f"Unknown rig: {rig}")


@router.get("/ports", response_model=PortInfo, dependencies=[Depends(require_token)])
def ports() -> PortInfo:
    try:
        out = subprocess.run(["python", "tools/snapshot_devices.py"], capture_output=True, text=True, timeout=30)
        lines = [ln for ln in out.stdout.splitlines() if "/dev/" in ln]
    except Exception:
        lines = []
    return PortInfo(devices=lines)
```

(Remove the bogus `__version__` import line; use `VERSION` constant.)

- [ ] **Step 4: Run → PASS**
- [ ] **Step 5: Commit** `feat(api): rigs/health/ports router`

---

### Task 6: processes router (start/status/stop/clear/stop-all)

**Files:**
- Create: `src/soarm101_workshop/api/routers/processes.py`
- Test: `tests/test_routes_processes.py`

**Interfaces:**
- Consumes: `service.manager`, builders, models, `auth`.
- Produces: `router` with POST `/rigs/{rig}/{action}`, GET `/processes`, POST `/processes/{key}/stop`, `/processes/stop-all`, DELETE `/processes/{key}`.

- [ ] **Step 1: Failing test (monkeypatch builders to a fake fast command)**

```python
# tests/test_routes_processes.py
import asyncio
import pytest
from fastapi.testclient import TestClient
from soarm101_workshop.api.app import create_app
import soarm101_workshop.api.routers.processes as proc
import soarm101_workshop.api.settings as s
from soarm101_workshop.api.settings import Settings

@pytest.fixture
def client(tmp_path, monkeypatch):
    s.get_settings = lambda: Settings(token="t", allow_localhost_no_auth=True)
    # fake builders: harmless fast/long commands instead of lerobot
    monkeypatch.setattr(proc, "build_teleop", lambda rig, **k: ["bash", "-c", "sleep 5"])
    from soarm101_workshop.api.service import ProcessManager
    proc.manager = ProcessManager(logs_dir=tmp_path, pidfile=tmp_path / "p.json")
    return TestClient(create_app())

H = {"Authorization": "Bearer t"}

def test_start_status_stop(client):
    r = client.post("/api/rigs/rig01/teleop", headers=H, json={})
    assert r.status_code == 200
    key = r.json()["key"]
    st = client.get("/api/processes", headers=H).json()
    assert st[key]["alive"] is True
    assert client.post(f"/api/processes/{key}/stop", headers=H).status_code == 200

def test_unknown_action_404(client):
    assert client.post("/api/rigs/rig01/bogus", headers=H, json={}).status_code == 404

def test_record_validation_422(client):
    r = client.post("/api/rigs/rig01/record", headers=H, json={"episodes": 0})
    assert r.status_code == 422

def test_auth_required(client):
    assert client.get("/api/processes").status_code == 401
```

- [ ] **Step 2: Run → FAIL**
- [ ] **Step 3: Implement processes router**

```python
# src/soarm101_workshop/api/routers/processes.py
from __future__ import annotations
from dataclasses import replace
from fastapi import APIRouter, Body, Depends, HTTPException
from ..auth import require_token
from ..models import ActionResult, ProcessStatus, RecordParams, ReplayParams, TeleopParams
from ..service import manager
from ..settings import get_settings
from ...commands import build_calibrate_follower, build_calibrate_leader, build_record, build_replay, build_teleop, shell_join
from ...config import get_rig

router = APIRouter(prefix="/api", dependencies=[Depends(require_token)])


def _rig(rig: str):
    try:
        return get_rig(rig, get_settings().config_path)
    except KeyError:
        raise HTTPException(404, f"Unknown rig: {rig}")


@router.post("/rigs/{rig}/teleop", response_model=ActionResult)
async def start_teleop(rig: str, params: TeleopParams = Body(default=TeleopParams())):
    r = _rig(rig)
    if params.no_cameras:
        r = replace(r, cameras={})
    cmd = build_teleop(r, display_data=params.display_data)
    return await _start(rig, "teleop", cmd)


@router.post("/rigs/{rig}/calibrate-follower", response_model=ActionResult)
async def start_cal_follower(rig: str):
    return await _start(rig, "calibrate-follower", build_calibrate_follower(_rig(rig)))


@router.post("/rigs/{rig}/calibrate-leader", response_model=ActionResult)
async def start_cal_leader(rig: str):
    return await _start(rig, "calibrate-leader", build_calibrate_leader(_rig(rig)))


@router.post("/rigs/{rig}/record", response_model=ActionResult)
async def start_record(rig: str, params: RecordParams = Body(default=RecordParams())):
    r = _rig(rig)
    if params.no_cameras:
        r = replace(r, cameras={})
    cmd = build_record(
        r, hf_user=params.hf_user, dataset_name=params.dataset_name,
        episodes=params.episodes, episode_time_s=params.episode_time_s,
        reset_time_s=params.reset_time_s, push_to_hub=params.push_to_hub,
        resume=params.resume, display_data=params.display_data,
    )
    return await _start(rig, "record", cmd)


@router.post("/rigs/{rig}/replay", response_model=ActionResult)
async def start_replay(rig: str, params: ReplayParams):
    cmd = build_replay(_rig(rig), params.repo_id, params.episode)
    return await _start(rig, "replay", cmd)


async def _start(rig: str, action: str, cmd: list[str]) -> ActionResult:
    key = f"{rig}/{action}"
    rp = await manager.start(key, cmd)
    return ActionResult(key=key, pid=rp.pid, cmd=shell_join(cmd))


@router.get("/processes")
def processes() -> dict[str, ProcessStatus]:
    return {k: ProcessStatus(**v) for k, v in manager.status().items()}


@router.post("/processes/{rig}/{action}/stop")
async def stop_proc(rig: str, action: str):
    key = f"{rig}/{action}"
    if not await manager.stop(key):
        raise HTTPException(404, f"No such process: {key}")
    return {"stopped": key}


@router.post("/processes/stop-all")
async def stop_all():
    await manager.stop_all()
    return {"stopped": "all"}


@router.delete("/processes/{rig}/{action}")
def clear_proc(rig: str, action: str):
    manager.clear(f"{rig}/{action}")
    return {"cleared": f"{rig}/{action}"}
```

Note: because keys contain `/`, stop/clear use two path segments `{rig}/{action}` rather than a single `{key}`. Update the spec's `{key}` accordingly.

- [ ] **Step 4: Run → PASS**
- [ ] **Step 5: Commit** `feat(api): processes router (start/status/stop/clear)`

---

### Task 7: SSE log streaming

**Files:**
- Modify: `src/soarm101_workshop/api/routers/processes.py` (add SSE endpoint)
- Test: `tests/test_sse.py`

**Interfaces:**
- Produces: `GET /api/processes/{rig}/{action}/logs` → `text/event-stream` yielding appended log lines until the process exits.

- [ ] **Step 1: Failing test**

```python
# tests/test_sse.py
import pytest
from fastapi.testclient import TestClient
from soarm101_workshop.api.app import create_app
import soarm101_workshop.api.routers.processes as proc
import soarm101_workshop.api.settings as s
from soarm101_workshop.api.settings import Settings
from soarm101_workshop.api.service import ProcessManager

@pytest.fixture
def client(tmp_path, monkeypatch):
    s.get_settings = lambda: Settings(token="t", allow_localhost_no_auth=True)
    monkeypatch.setattr(proc, "build_teleop", lambda rig, **k: ["bash", "-c", "echo LINE1; echo LINE2; sleep 0.2"])
    proc.manager = ProcessManager(logs_dir=tmp_path, pidfile=tmp_path / "p.json")
    return TestClient(create_app())

H = {"Authorization": "Bearer t"}

def test_sse_streams_log_lines(client):
    client.post("/api/rigs/rig01/teleop", headers=H, json={})
    with client.stream("GET", "/api/processes/rig01/teleop/logs", headers=H) as r:
        body = ""
        for chunk in r.iter_text():
            body += chunk
            if "LINE2" in body:
                break
    assert "LINE1" in body and "LINE2" in body
```

- [ ] **Step 2: Run → FAIL**
- [ ] **Step 3: Implement SSE endpoint** (append to processes.py)

```python
import asyncio
from sse_starlette.sse import EventSourceResponse

@router.get("/processes/{rig}/{action}/logs")
async def stream_logs(rig: str, action: str):
    key = f"{rig}/{action}"
    log_path = manager.log_path(key)

    async def gen():
        last = 0
        for _ in range(6000):  # ~10 min cap at 0.1s
            if log_path.exists():
                with log_path.open("r", errors="replace") as f:
                    f.seek(last)
                    new = f.read()
                    last = f.tell()
                for line in new.splitlines():
                    yield {"data": line}
            alive = key in manager.status() and manager.status()[key]["alive"]
            if not alive and log_path.exists() and last >= log_path.stat().st_size:
                break
            await asyncio.sleep(0.1)

    return EventSourceResponse(gen())
```

- [ ] **Step 4: Run → PASS**
- [ ] **Step 5: Commit** `feat(api): SSE log streaming`

---

### Task 8: App factory, shutdown reaper, static mount, run()

**Files:**
- Create: `src/soarm101_workshop/api/app.py`
- Test: `tests/test_app.py`

**Interfaces:**
- Produces: `create_app() -> FastAPI`, `run()` (uvicorn entrypoint).
- Consumes: routers, `manager`, `get_settings`.

- [ ] **Step 1: Failing test**

```python
# tests/test_app.py
from fastapi.testclient import TestClient
from soarm101_workshop.api.app import create_app

def test_docs_and_openapi():
    c = TestClient(create_app())
    assert c.get("/openapi.json").status_code == 200

def test_cors_and_health_open():
    c = TestClient(create_app())
    assert c.get("/api/health").status_code == 200
```

- [ ] **Step 2: Run → FAIL**
- [ ] **Step 3: Implement app**

```python
# src/soarm101_workshop/api/app.py
from __future__ import annotations
import contextlib
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routers import rigs, processes
from .service import manager
from .settings import get_settings


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    killed = await manager.reconcile()
    if killed:
        print(f"Reaped {killed} orphaned process group(s) from a previous run.")
    yield
    await manager.stop_all()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="SO-ARM101 Workshop API", version=rigs.VERSION, lifespan=lifespan)
    if settings.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                           allow_methods=["*"], allow_headers=["*"])
    app.include_router(rigs.router)
    app.include_router(processes.router)
    static_dir = Path(__file__).parent.parent / "web" / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    return app


def run() -> None:
    import uvicorn
    s = get_settings()
    if not s.token and not s.allow_localhost_no_auth:
        print("WARNING: no SOARM_API_TOKEN set and loopback bypass disabled — all /api calls will 401.")
    uvicorn.run(create_app(), host=s.host, port=s.port, workers=1)
```

- [ ] **Step 4: Run → PASS** (also rerun rigs/processes/sse suites — they import `create_app`)
- [ ] **Step 5: Commit** `feat(api): app factory, lifespan reaper, static mount, run()`

---

### Task 9: CLI as HTTP client

**Files:**
- Create: `src/soarm101_workshop/client/__init__.py`
- Create: `src/soarm101_workshop/client/http.py`
- Rewrite: `src/soarm101_workshop/cli.py`
- Test: `tests/test_cli_client.py`

**Interfaces:**
- Produces: `ApiClient(base_url, token)` with `.get(path)`, `.post(path, json)`,
  `.delete(path)`; `cli.main()` mapping subcommands to calls.

- [ ] **Step 1: Failing test (drive CLI against the FastAPI app via httpx ASGITransport)**

```python
# tests/test_cli_client.py
import httpx, pytest
from soarm101_workshop.api.app import create_app
import soarm101_workshop.api.settings as s
from soarm101_workshop.api.settings import Settings
from soarm101_workshop.client.http import ApiClient

@pytest.fixture
def api_client():
    s.get_settings = lambda: Settings(token="t", allow_localhost_no_auth=True)
    transport = httpx.ASGITransport(app=create_app())
    return ApiClient("http://test", "t", transport=transport)

def test_list_rigs(api_client):
    data = api_client.get("/api/rigs")
    assert any(r["name"] == "rig01" for r in data)
```

- [ ] **Step 2: Run → FAIL**
- [ ] **Step 3: Implement client + CLI**

```python
# src/soarm101_workshop/client/http.py
from __future__ import annotations
import os, sys
import httpx


class ApiClient:
    def __init__(self, base_url: str | None = None, token: str | None = None, transport=None):
        self.base_url = base_url or os.environ.get("SOARM_API_URL", "http://127.0.0.1:7860")
        self.token = token if token is not None else os.environ.get("SOARM_API_TOKEN", "")
        self._client = httpx.Client(
            base_url=self.base_url, transport=transport, timeout=30,
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
```

```python
# src/soarm101_workshop/cli.py  (rewritten)
from __future__ import annotations
import argparse, json
import httpx
from .client.http import ApiClient


def main() -> None:
    p = argparse.ArgumentParser(description="SO-ARM101 workshop API client")
    p.add_argument("--rig", default="rig01")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rigs")
    sub.add_parser("find-ports")
    sub.add_parser("status")
    sub.add_parser("teleop")
    sub.add_parser("calibrate-follower")
    sub.add_parser("calibrate-leader")
    rec = sub.add_parser("record")
    rec.add_argument("--episodes", type=int, default=5)
    rec.add_argument("--episode-time-s", type=int, default=20)
    rec.add_argument("--reset-time-s", type=int, default=10)
    rec.add_argument("--hf-user", default="local")
    rec.add_argument("--dataset-name")
    rec.add_argument("--push-to-hub", action="store_true")
    rec.add_argument("--resume", action="store_true")
    rep = sub.add_parser("replay")
    rep.add_argument("repo_id")
    rep.add_argument("--episode", type=int, default=0)
    sub.add_parser("stop")          # stops --rig's matching action? use stop-all for simplicity
    sub.add_parser("stop-all")
    args = p.parse_args()

    c = ApiClient()
    try:
        if args.cmd == "rigs":
            for r in c.get("/api/rigs"):
                print(f"{r['name']}: {r['label']}\n  follower {r['follower']['id']} @ {r['follower']['port']}\n  leader   {r['leader']['id']} @ {r['leader']['port']}")
        elif args.cmd == "find-ports":
            for d in c.get("/api/ports")["devices"]:
                print(d)
        elif args.cmd == "status":
            print(json.dumps(c.get("/api/processes"), indent=2))
        elif args.cmd == "teleop":
            print(c.post(f"/api/rigs/{args.rig}/teleop"))
        elif args.cmd in ("calibrate-follower", "calibrate-leader"):
            print(c.post(f"/api/rigs/{args.rig}/{args.cmd}"))
        elif args.cmd == "record":
            print(c.post(f"/api/rigs/{args.rig}/record", {
                "episodes": args.episodes, "episode_time_s": args.episode_time_s,
                "reset_time_s": args.reset_time_s, "hf_user": args.hf_user,
                "dataset_name": args.dataset_name, "push_to_hub": args.push_to_hub,
                "resume": args.resume,
            }))
        elif args.cmd == "replay":
            print(c.post(f"/api/rigs/{args.rig}/replay", {"repo_id": args.repo_id, "episode": args.episode}))
        elif args.cmd == "stop-all":
            print(c.post("/api/processes/stop-all"))
    except httpx.ConnectError:
        raise SystemExit("Cannot reach the API. Is it running?  Start it with: soarm-api")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run → PASS**
- [ ] **Step 5: Commit** `feat(cli): CLI is now a thin API client`

---

### Task 10: Static SPA client

**Files:**
- Create: `src/soarm101_workshop/web/static/index.html`
- Create: `src/soarm101_workshop/web/static/app.js`
- Keep: `src/soarm101_workshop/web/static/style.css` (reuse)
- Delete: `src/soarm101_workshop/web_app.py`, `src/soarm101_workshop/web/templates/`
- Test: `tests/test_static.py`

**Interfaces:**
- Consumes: the JSON API; stores token in `sessionStorage`.

- [ ] **Step 1: Failing test**

```python
# tests/test_static.py
from fastapi.testclient import TestClient
from soarm101_workshop.api.app import create_app

def test_index_served():
    c = TestClient(create_app())
    r = c.get("/")
    assert r.status_code == 200 and "SO-ARM101" in r.text
```

- [ ] **Step 2: Run → FAIL**
- [ ] **Step 3: Implement index.html + app.js**

`index.html`: a token field, a rig `<select>`, action buttons (teleop, calibrate
follower/leader, record with number inputs, replay), a "Stop all" button, and a
`#status` container. Loads `app.js`.

`app.js` (vanilla):

```javascript
const $ = (s) => document.querySelector(s);
const token = () => sessionStorage.getItem("soarm_token") || "";
const headers = () => ({ "Authorization": "Bearer " + token(), "Content-Type": "application/json" });

async function api(path, method = "GET", body) {
  const r = await fetch("/api" + path, { method, headers: headers(), body: body ? JSON.stringify(body) : undefined });
  if (!r.ok) { alert("API " + r.status + ": " + (await r.text())); throw new Error(r.status); }
  return r.headers.get("content-type")?.includes("json") ? r.json() : {};
}

async function loadRigs() {
  const rigs = await api("/rigs");
  $("#rig").innerHTML = rigs.map(r => `<option value="${r.name}">${r.name} — ${r.label}</option>`).join("");
}
async function refresh() {
  const st = await api("/processes");
  $("#status").innerHTML = Object.values(st).map(p =>
    `<div class="proc ${p.alive ? "" : "stopped"}"><div class="proc-head"><strong class="proc-name">${p.key}</strong>${p.alive ? "" : `<span class="proc-exit">(exit ${p.returncode})</span>`}</div><code class="proc-cmd">${p.cmd}</code><pre class="proc-log">${p.log}</pre>${p.alive ? `<button onclick="stop('${p.key}')">Stop</button>` : ""}</div>`
  ).join("") || '<p class="hint italic">Nothing running.</p>';
}
const rig = () => $("#rig").value;
async function start(action, body) { await api(`/rigs/${rig()}/${action}`, "POST", body || {}); refresh(); }
async function stop(key) { await api(`/processes/${key}/stop`, "POST"); refresh(); }
async function stopAll() { await api("/processes/stop-all", "POST"); refresh(); }
function saveToken() { sessionStorage.setItem("soarm_token", $("#token").value); loadRigs(); }
window.addEventListener("load", () => { $("#token").value = token(); loadRigs(); refresh(); setInterval(refresh, 5000); });
```

Wire buttons via `onclick` (e.g. record reads the number inputs into a body object).

- [ ] **Step 4: Run → PASS**; delete Flask app and templates.

```bash
git rm src/soarm101_workshop/web_app.py
git rm -r src/soarm101_workshop/web/templates
```

- [ ] **Step 5: Commit** `feat(web): static SPA client; remove Flask app`

---

### Task 11: Deploy artifacts + scripts + docs

**Files:**
- Create: `deploy/soarm-api.service`
- Create: `deploy/Dockerfile`
- Modify: `scripts/32_web_launcher.sh` (now starts `soarm-api`)
- Modify: `README.md` (API usage, token, soarm-api, /docs)
- Delete: references to `soarm-web`

- [ ] **Step 1: systemd unit**

```ini
# deploy/soarm-api.service
[Unit]
Description=SO-ARM101 Workshop API
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/USER/git/soarm101-highschool-demos
EnvironmentFile=/home/USER/git/soarm101-highschool-demos/.env
ExecStart=/home/USER/git/soarm101-highschool-demos/.venv/bin/soarm-api
Restart=on-failure
# Single worker is mandatory (serial ports are exclusive).

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Dockerfile** (documented as advanced — needs `--device` passthrough)

```dockerfile
# deploy/Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e '.[robot]'
ENV SOARM_HOST=0.0.0.0
EXPOSE 7860
CMD ["soarm-api"]
# Run with: docker run --device=/dev/ttyACM0 --device=/dev/ttyACM1 -e SOARM_API_TOKEN=... -p 7860:7860 ...
```

- [ ] **Step 3: Update launcher + README**

`scripts/32_web_launcher.sh` body: `exec soarm-api`. README: document `soarm-api`,
`SOARM_API_TOKEN`, `/docs`, the CLI-as-client model, and that the server must run
for hardware ops.

- [ ] **Step 4: ruff + full pytest**

Run: `ruff check src tests && pytest -q`  Expected: all pass.

- [ ] **Step 5: Commit** `feat: deploy artifacts, scripts, README for API model`

---

### Task 12: Live hardware acceptance (manual)

**Files:** none (verification only).

- [ ] **Step 1:** `export SOARM_API_TOKEN=dev; soarm-api &`
- [ ] **Step 2:** `curl -H "Authorization: Bearer dev" localhost:7860/api/rigs` → rig01 listed.
- [ ] **Step 3:** `soarm-workshop teleop` (clear workspace) → `soarm-workshop status` shows alive; web `/` shows it; logs SSE streams 60 Hz lines.
- [ ] **Step 4:** `soarm-workshop stop-all` → process gone, `test -w /dev/ttyACM0` ok, no orphans (`pgrep -af lerobot`).
- [ ] **Step 5:** restart `soarm-api` while a process runs → reconcile reaps the orphan group on startup (verify log message + port free).

---

## Self-Review

- **Spec coverage:** settings/auth/models/service/routers/SSE/app/CLI/static/deploy/tests all mapped to Tasks 1–12. Orphan reconcile (Finding #7) → Task 3/8/12. Validation → Task 2/6. ✓
- **Placeholder scan:** none ("TBD"/"handle errors" absent); code shown in each step.
- **Type consistency:** `manager` API (`start/stop/stop_all/clear/status/reconcile/log_path`) consistent across Tasks 3,6,7,8. `ApiClient.get/post/delete` consistent Task 9. Process key `{rig}/{action}` consistent in routes/CLI/SSE (spec `{key}` note corrected in Task 6).
- **Known nit to fix during impl:** remove the stray `from ... import __version__ if False` line in Task 5 (use `VERSION` constant only).
