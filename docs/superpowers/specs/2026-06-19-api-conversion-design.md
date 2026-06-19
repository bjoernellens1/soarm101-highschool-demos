# SO-ARM101 Workshop — API-based conversion design

**Date:** 2026-06-19
**Branch:** `api-conversion` (based on `eval-fixes`)

## Context

The project is a teaching wrapper around LeRobot for SO-ARM101 arms. Today it
exposes three overlapping interfaces: a `soarm-workshop` CLI (calls lerobot
directly), a Flask web launcher (server-rendered HTML, form POSTs, no JSON, no
auth, in-process state), and shell scripts. The user wants the whole project
**converted to an API-based architecture** that is **production ready**, found
the most efficient way.

Approved decisions (brainstorming):
- **Framework:** FastAPI + Uvicorn, **single worker** (serial ports are an
  exclusive resource; concurrency is impossible and would corrupt shared state).
- **UI:** pure JSON API is the source of truth; a thin static JS client consumes it.
- **CLI:** `soarm-workshop` becomes a thin HTTP client of the API.
- **Auth:** static Bearer token (`SOARM_API_TOKEN`); optional bypass on loopback.
- **Live updates:** polling JSON for status; **SSE** for live log tails.

## Goals / non-goals

**Goals:** one source of truth (the API) for every rig operation; typed
request/response with automatic validation; OpenAPI docs; token auth; live
status + log streaming; graceful shutdown that reaps child process groups;
a real automated test suite; deploy artifacts (systemd unit + Dockerfile).

**Non-goals:** multi-user accounts/roles; horizontal scaling (single PC, single
worker); training/inference pipelines; ROS2.

## Architecture

```
src/soarm101_workshop/
  config.py            # unchanged — rig registry (reused)
  commands.py          # builders kept PURE (build_teleop/record/replay/calibrate);
                       # process-lifecycle code moves out to api/service.py
  api/
    __init__.py
    settings.py        # pydantic-settings: token, host, port, config path,
                       #   allow_localhost_no_auth, cors_origins, dataset cache hints
    auth.py            # Bearer-token dependency; loopback bypass when configured
    models.py          # Pydantic models (requests + responses)
    service.py         # ProcessManager: async-safe registry, pgid-at-spawn,
                       #   log tailing, pidfile-based orphan reconciliation
    app.py             # FastAPI factory: routers, exception handlers,
                       #   startup/shutdown hooks, static client mount
    routers/
      rigs.py          # GET /api/health, /api/rigs, /api/rigs/{rig}, /api/ports
      processes.py     # POST /api/rigs/{rig}/{action}; GET /api/processes;
                       #   POST /api/processes/{key}/stop; /stop-all;
                       #   DELETE /api/processes/{key}; GET /api/processes/{key}/logs (SSE)
  client/
    __init__.py
    http.py            # httpx wrapper: base URL + token from env, error mapping
  cli.py               # thin client using client/http.py (same subcommands)
  web/
    static/            # SPA: index.html + app.js + style.css (calls the API)
```

### Process model & lifecycle

- `ProcessManager` holds the registry behind an `asyncio.Lock`. It reuses the
  hardened logic already on `eval-fixes`: `start_new_session=True`,
  **pgid captured at spawn**, SIGTERM→(3s)→SIGKILL on the **group**, log file
  written under `logs/<key>.log`, own fd closed after spawn.
- **Orphan reconciliation:** the manager persists running entries to a small
  JSON pidfile (`logs/.processes.json`: key→{pid, pgid, cmd}). On startup it
  reads the pidfile and, for any still-alive group, either re-attaches a stub
  status entry or (configurable, default) **kills the leftover group** so a
  restart never leaves an arm energized or a port held. Closes the cross-restart
  gap from the eval (Finding #7).
- **Graceful shutdown:** FastAPI shutdown hook calls `stop_all()`, killing every
  child process group, then clears the pidfile.
- Single worker is enforced by the `soarm-api` entrypoint (`--workers 1`);
  documented as a hard requirement (serial exclusivity).

### Endpoints (JSON unless noted)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness + version |
| GET | `/api/rigs` | list rigs with follower/leader/cameras/task |
| GET | `/api/rigs/{rig}` | one rig |
| GET | `/api/ports` | discovered serial devices (snapshot_devices/lerobot-find-port) |
| POST | `/api/rigs/{rig}/{action}` | start `teleop\|calibrate-follower\|calibrate-leader\|record\|replay`; body = typed params |
| GET | `/api/processes` | status of all tracked processes (alive, returncode, cmd, started_at, log tail) |
| POST | `/api/processes/{key}/stop` | stop one |
| POST | `/api/processes/stop-all` | emergency stop all |
| DELETE | `/api/processes/{key}` | clear a finished entry |
| GET | `/api/processes/{key}/logs` | **SSE** live log tail |

`{key}` is `"{rig}/{action}"`. Action names use hyphens in the path
(`calibrate-follower`) and map to the existing builders.

### Pydantic models (validation)

- `RecordParams` (episodes 1–50, episode_time_s 5–600, reset_time_s 0–120,
  hf_user, dataset_name?, push_to_hub, resume, display_data, no_cameras).
- `TeleopParams` (display_data, no_cameras).
- `ReplayParams` (repo_id, episode≥0).
- Response models: `RigInfo`, `ArmInfo`, `ProcessStatus`, `HealthInfo`,
  `PortInfo`. Invalid bodies → automatic `422` (no more hand-rolled int parsing).

### Auth

- `auth.py` provides `require_token` dependency on all `/api/*` routes (except
  `/api/health` and `/docs`). Token from `SOARM_API_TOKEN`. If
  `SOARM_ALLOW_LOCALHOST_NO_AUTH=1` and the request client is loopback, the
  dependency passes without a token (dev convenience). Missing/wrong token → `401`.

### CLI as client

- `cli.py` keeps subcommands (`rigs`, `find-ports`, `calibrate-*`, `teleop`,
  `record`, `replay`, plus `status`, `stop`, `stop-all`). Each maps to an HTTP
  call via `client/http.py`. Base URL `SOARM_API_URL` (default
  `http://127.0.0.1:7860`), token `SOARM_API_TOKEN`. Connection errors print a
  clear "is the API running? `soarm-api`" hint. `web` subcommand is dropped
  (the API serves the UI itself).

### Static client

- `web/static/index.html` + `app.js` + `style.css` (reuse the existing dark
  theme CSS). Fetches `/api/rigs` and `/api/processes`, posts actions, polls
  status every 5s while anything is alive, opens an `EventSource` to the SSE log
  endpoint for the selected process. Token entered once and kept in memory /
  `sessionStorage`.

### Interactive tools (scope)

- `color-demo`: exposed as `POST /api/rigs/{rig}/color-demo` running headless
  (the `--headless` path added on `eval-fixes`), streaming detections over SSE;
  GUI window remains CLI-only.
- `pose_recorder`/`replay_poses`: interactive stdin doesn't fit stateless HTTP.
  Kept as CLI-local utilities with a documented note; not part of the v1 API.
  (A future pose CRUD API is out of scope.)

## Testing strategy ("test all")

- **Unit (no hardware):** builders (`build_*`), `config.get_rig/camera_cli_value`,
  Pydantic model validation, auth dependency, `ProcessManager` against a fake
  fast subprocess (`sleep`/`echo`) — covers start/stop/pgid/stop-all/reconcile.
- **API (FastAPI `TestClient`):** every route — auth required/!required, 401,
  422 on bad bodies, 404 unknown rig/process, health, rigs listing,
  start→status→stop happy path with the fake command, SSE log stream yields lines.
- **CLI client:** point at the TestClient/an ephemeral server; assert each
  subcommand hits the right endpoint and renders output.
- **Live hardware smoke (manual, documented):** `soarm-api` up → `soarm-workshop
  teleop` → status shows 60 Hz → stop → ports released, no orphans. Run on the
  attached rig01 as the final acceptance gate.
- `ruff check` clean; CI-friendly `pytest` via `pyproject` `[dev]` extra.

## Deployment

- `soarm-api` console script → `uvicorn soarm101_workshop.api.app:app
  --host 127.0.0.1 --port 7860 --workers 1`.
- `deploy/soarm-api.service` systemd unit template (env file, restart policy,
  single worker).
- `deploy/Dockerfile` (optional) — note: USB/serial passthrough required
  (`--device`), so Docker is documented as advanced/optional.

## Dependencies

Add: `fastapi`, `uvicorn[standard]`, `httpx`, `pydantic-settings`,
`sse-starlette`. Remove: `flask`. Dev: `pytest`, `pytest-asyncio`, `ruff`
(already present). `opencv-python`, `numpy`, `pyyaml` unchanged.

## Migration / compatibility

- Flask `web_app.py` is removed; its behavior is superseded by the API + static
  client. Shell scripts that call `soarm-workshop` keep working (the CLI keeps
  its interface, now talking to the API). Scripts that call `lerobot-*` directly
  are unaffected.
- Calibration flat-layout and other `eval-fixes` changes are inherited via the
  branch base.

## Risks

- Single-worker is a correctness requirement, not a perf choice — must be
  enforced and documented or two clients could fight over a serial port.
- SSE through some reverse proxies needs buffering disabled — documented.
- `pose_recorder` interactivity intentionally left out of v1 API.
