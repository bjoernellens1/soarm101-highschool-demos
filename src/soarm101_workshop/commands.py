from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import Rig, camera_cli_value, default_dataset_name, get_rig, list_rigs


@dataclass
class RunningCommand:
    key: str
    cmd: list[str]
    process: subprocess.Popen
    started_at: float = field(default_factory=time.time)


_RUNNING: dict[str, RunningCommand] = {}


def build_calibrate_follower(rig: Rig) -> list[str]:
    return [
        "lerobot-calibrate",
        f"--robot.type={rig.follower.type}",
        f"--robot.port={rig.follower.port}",
        f"--robot.id={rig.follower.id}",
    ]


def build_calibrate_leader(rig: Rig) -> list[str]:
    return [
        "lerobot-calibrate",
        f"--teleop.type={rig.leader.type}",
        f"--teleop.port={rig.leader.port}",
        f"--teleop.id={rig.leader.id}",
    ]


def build_teleop(rig: Rig, display_data: bool = True) -> list[str]:
    cmd = [
        "lerobot-teleoperate",
        f"--robot.type={rig.follower.type}",
        f"--robot.port={rig.follower.port}",
        f"--robot.id={rig.follower.id}",
        f"--teleop.type={rig.leader.type}",
        f"--teleop.port={rig.leader.port}",
        f"--teleop.id={rig.leader.id}",
    ]
    if rig.cameras:
        cmd.append(f"--robot.cameras={camera_cli_value(rig.cameras)}")
    if display_data:
        cmd.append("--display_data=true")
    return cmd


def build_record(
    rig: Rig,
    hf_user: str,
    dataset_name: str | None = None,
    episodes: int = 5,
    episode_time_s: int = 20,
    reset_time_s: int = 10,
    push_to_hub: bool = False,
    display_data: bool = True,
) -> list[str]:
    dataset_name = dataset_name or default_dataset_name(rig.name)
    repo_id = f"{hf_user}/{dataset_name}" if "/" not in dataset_name else dataset_name
    cmd = build_teleop(rig, display_data=display_data)
    cmd[0] = "lerobot-record"
    cmd.extend(
        [
            f"--dataset.repo_id={repo_id}",
            f"--dataset.num_episodes={episodes}",
            f"--dataset.episode_time_s={episode_time_s}",
            f"--dataset.reset_time_s={reset_time_s}",
            f"--dataset.single_task={rig.task_text}",
            "--dataset.streaming_encoding=true",
            "--dataset.encoder_threads=2",
            f"--dataset.push_to_hub={'true' if push_to_hub else 'false'}",
        ]
    )
    return cmd


def build_replay(rig: Rig, repo_id: str, episode: int = 0) -> list[str]:
    return [
        "lerobot-replay",
        f"--robot.type={rig.follower.type}",
        f"--robot.port={rig.follower.port}",
        f"--robot.id={rig.follower.id}",
        f"--dataset.repo_id={repo_id}",
        f"--dataset.episode={episode}",
    ]


def shell_join(cmd: list[str]) -> str:
    return " ".join(shlex.quote(x) for x in cmd)


def run_blocking(cmd: list[str], *, cwd: str | Path | None = None) -> int:
    print("+", shell_join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=False).returncode


def start_process(key: str, cmd: list[str], *, cwd: str | Path | None = None) -> RunningCommand:
    stop_process(key)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / f"{key.replace('/', '_')}.log"
    log = log_path.open("ab")
    log.write(("\n\n=== " + time.strftime("%Y-%m-%d %H:%M:%S") + " ===\n").encode())
    log.write(("+ " + shell_join(cmd) + "\n").encode())
    log.flush()
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    running = RunningCommand(key=key, cmd=cmd, process=proc)
    _RUNNING[key] = running
    return running


def stop_process(key: str) -> bool:
    running = _RUNNING.get(key)
    if not running:
        return False
    proc = running.process
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
    _RUNNING.pop(key, None)
    return True


def status() -> dict[str, dict[str, str | int | float | bool]]:
    out = {}
    for key, running in list(_RUNNING.items()):
        proc = running.process
        alive = proc.poll() is None
        out[key] = {
            "alive": alive,
            "returncode": proc.returncode if proc.returncode is not None else "",
            "started_at": running.started_at,
            "cmd": shell_join(running.cmd),
        }
        if not alive:
            _RUNNING.pop(key, None)
    return out


def get_rig_from_env() -> Rig:
    return get_rig(os.environ.get("RIG", "rig01"), os.environ.get("ARMS_CONFIG", "configs/arms.yaml"))


def available_rigs() -> list[str]:
    return list_rigs(os.environ.get("ARMS_CONFIG", "configs/arms.yaml"))
