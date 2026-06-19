from __future__ import annotations

import subprocess

from fastapi import APIRouter, Depends, HTTPException

from ...config import get_rig, list_rigs
from ..auth import require_token
from ..models import HealthInfo, PortInfo, RigInfo
from ..settings import get_settings

router = APIRouter(prefix="/api")
VERSION = "0.3.0"


def _rig_info(name: str, cfg: str) -> RigInfo:
    r = get_rig(name, cfg)
    return RigInfo(
        name=r.name,
        label=r.label,
        task_text=r.task_text,
        follower={
            "role": "follower",
            "type": r.follower.type,
            "id": r.follower.id,
            "port": r.follower.port,
        },
        leader={
            "role": "leader",
            "type": r.leader.type,
            "id": r.leader.id,
            "port": r.leader.port,
        },
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
        out = subprocess.run(
            ["python", "tools/snapshot_devices.py"], capture_output=True, text=True, timeout=30
        )
        lines = [ln for ln in out.stdout.splitlines() if "/dev/" in ln]
    except Exception:
        lines = []
    return PortInfo(devices=lines)
