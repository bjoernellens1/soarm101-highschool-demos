from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Arm:
    role: str
    type: str
    id: str
    port: str
    serial_hint: str = ""


@dataclass(frozen=True)
class Rig:
    name: str
    label: str
    task_text: str
    follower: Arm
    leader: Arm
    cameras: dict[str, dict[str, Any]]


def load_config(path: str | Path = "configs/arms.yaml") -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing {p}. Copy/edit configs/arms.yaml first.")
    return yaml.safe_load(p.read_text())


def list_rigs(path: str | Path = "configs/arms.yaml") -> list[str]:
    cfg = load_config(path)
    return sorted(cfg.get("rigs", {}).keys())


def get_rig(name: str = "rig01", path: str | Path = "configs/arms.yaml") -> Rig:
    cfg = load_config(path)
    rigs = cfg.get("rigs", {})
    if name not in rigs:
        valid = ", ".join(sorted(rigs)) or "<none>"
        raise KeyError(f"Unknown rig {name!r}. Valid rigs: {valid}")
    raw = rigs[name]
    follower = Arm(role="follower", **raw["follower"])
    leader = Arm(role="leader", **raw["leader"])
    return Rig(
        name=name,
        label=raw.get("label", name),
        task_text=raw.get("task_text", "Pick up the cube and place it in the bin"),
        follower=follower,
        leader=leader,
        cameras=raw.get("cameras", {}),
    )


def camera_cli_value(cameras: dict[str, dict[str, Any]]) -> str:
    """Return LeRobot CLI camera mapping syntax.

    LeRobot examples use an OmegaConf-like mapping string:
      "{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}"
    """
    if not cameras:
        return "{}"
    chunks: list[str] = []
    for name, cam in cameras.items():
        inner = ", ".join(f"{k}: {v!r}" if isinstance(v, str) else f"{k}: {v}" for k, v in cam.items())
        # LeRobot's CLI examples do not quote keys. Values may be strings.
        inner = inner.replace("'", "")
        chunks.append(f"{name}: {{{inner}}}")
    return "{ " + ", ".join(chunks) + " }"


def default_dataset_name(rig_name: str, base: str = "cube-sort") -> str:
    return f"hs-so101-{rig_name}-{base}"
