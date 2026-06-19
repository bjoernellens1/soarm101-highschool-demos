from __future__ import annotations

import asyncio
from dataclasses import replace

from fastapi import APIRouter, Body, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from ...commands import (
    build_calibrate_follower,
    build_calibrate_leader,
    build_record,
    build_replay,
    build_reset,
    build_safe_home,
    build_teleop,
    shell_join,
)
from ...config import get_rig, list_rigs, resolve_rig_name
from ..auth import require_token
from ..models import (
    ActionResult,
    OrchestraParams,
    ProcessStatus,
    RecordParams,
    ReplayParams,
    TeleopParams,
)
from ..service import manager
from ..settings import get_settings

router = APIRouter(prefix="/api", dependencies=[Depends(require_token)])


def _rig(rig: str):
    try:
        return get_rig(rig, get_settings().config_path)
    except KeyError:
        raise HTTPException(404, f"Unknown rig: {rig}")


async def _start(rig: str, action: str, cmd: list[str]) -> ActionResult:
    # Normalise station_N aliases so process keys are always the canonical rigNN.
    key = f"{resolve_rig_name(rig)}/{action}"
    rp = await manager.start(key, cmd)
    return ActionResult(key=key, pid=rp.pid, cmd=shell_join(cmd))


@router.post("/rigs/{rig}/teleop", response_model=ActionResult)
async def start_teleop(rig: str, params: TeleopParams = Body(default=TeleopParams())):
    r = _rig(rig)
    if params.no_cameras:
        r = replace(r, cameras={})
    return await _start(rig, "teleop", build_teleop(r, display_data=params.display_data))


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
        r,
        hf_user=params.hf_user,
        dataset_name=params.dataset_name,
        episodes=params.episodes,
        episode_time_s=params.episode_time_s,
        reset_time_s=params.reset_time_s,
        push_to_hub=params.push_to_hub,
        resume=params.resume,
        display_data=params.display_data,
    )
    return await _start(rig, "record", cmd)


@router.post("/rigs/{rig}/replay", response_model=ActionResult)
async def start_replay(rig: str, params: ReplayParams):
    return await _start(rig, "replay", build_replay(_rig(rig), params.repo_id, params.episode))


@router.post("/rigs/{rig}/safe-home", response_model=ActionResult)
async def start_safe_home(rig: str):
    return await _start(rig, "safe-home", build_safe_home(_rig(rig)))


@router.post("/rigs/{rig}/reset", response_model=ActionResult)
async def start_reset(rig: str):
    """Reset/recover the rig's motor buses: ping IDs and release torque locks."""
    return await _start(rig, "reset", build_reset(_rig(rig)))


@router.post("/orchestra/play", response_model=list[ActionResult])
async def orchestra_play(params: OrchestraParams):
    """Robot Orchestra: replay the same dataset on every station's follower,
    launched back-to-back so the arms move (near-)synchronously."""
    cfg = get_settings().config_path
    stations = params.stations or list_rigs(cfg)
    results = []
    for station in stations:
        r = _rig(station)
        cmd = build_replay(r, params.repo_id, params.episode)
        results.append(await _start(r.name, "orchestra", cmd))
    return results


# Catch-all registered AFTER the specific actions above so a bad action name
# returns a clean 404 rather than 405 (from the static mount) or a route miss.
@router.post("/rigs/{rig}/{action}")
async def unknown_action(rig: str, action: str):
    raise HTTPException(404, f"Unknown action: {action}")


@router.get("/processes", response_model=dict[str, ProcessStatus])
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


@router.get("/processes/{rig}/{action}/logs")
async def stream_logs(rig: str, action: str):
    key = f"{rig}/{action}"
    log_path = manager.log_path(key)

    async def gen():
        last = 0
        for _ in range(6000):  # ~10 min cap at 0.1s/iter
            if log_path.exists():
                with log_path.open("r", errors="replace") as f:
                    f.seek(last)
                    new = f.read()
                    last = f.tell()
                for line in new.splitlines():
                    yield {"data": line}
            st = manager.status().get(key)
            alive = bool(st and st["alive"])
            if not alive and log_path.exists() and last >= log_path.stat().st_size:
                break
            await asyncio.sleep(0.1)

    return EventSourceResponse(gen())
