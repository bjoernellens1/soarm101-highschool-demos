from __future__ import annotations

import os
import shlex
import subprocess
import threading
import time
import signal
from dataclasses import dataclass, field
from pathlib import Path

from .config import Rig, camera_cli_value, default_dataset_name, get_rig, list_rigs

def camera_exists(index_or_path: int | str) -> bool:
    try:
        import cv2
        # Use cv2 to check if camera is actually available and can be opened
        cap = cv2.VideoCapture(index_or_path)
        if not cap.isOpened():
            return False
        # Test if it can be configured to 640 width to catch virtual/stub cameras
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        success = cap.get(cv2.CAP_PROP_FRAME_WIDTH) > 0
        cap.release()
        return success
    except Exception:
        pass
    if isinstance(index_or_path, int):
        return Path(f"/dev/video{index_or_path}").exists()
    return Path(str(index_or_path)).exists()


@dataclass
class RunningCommand:
    key: str
    cmd: list[str]
    process: subprocess.Popen
    pgid: int | None = None
    started_at: float = field(default_factory=time.time)


_RUNNING: dict[str, RunningCommand] = {}
# Flask serves requests on multiple threads; guard the shared registry.
_RUNNING_LOCK = threading.Lock()


def build_calibrate_follower(rig: Rig) -> list[str]:
    return [
        "lerobot-calibrate",
        f"--robot.type={rig.follower.type}",
        f"--robot.port={rig.follower.port}",
        f"--robot.id={rig.follower.id}",
        "--robot.calibration_dir=.calibration",
    ]


def build_calibrate_leader(rig: Rig) -> list[str]:
    return [
        "lerobot-calibrate",
        f"--teleop.type={rig.leader.type}",
        f"--teleop.port={rig.leader.port}",
        f"--teleop.id={rig.leader.id}",
        "--teleop.calibration_dir=.calibration",
    ]


def build_teleop(rig: Rig, display_data: bool = False, check_cameras: bool = True) -> list[str]:
    cmd = [
        "lerobot-teleoperate",
        f"--robot.type={rig.follower.type}",
        f"--robot.port={rig.follower.port}",
        f"--robot.id={rig.follower.id}",
        "--robot.calibration_dir=.calibration",
        f"--teleop.type={rig.leader.type}",
        f"--teleop.port={rig.leader.port}",
        f"--teleop.id={rig.leader.id}",
        "--teleop.calibration_dir=.calibration",
    ]
    if rig.cameras:
        if check_cameras:
            available_cameras = {}
            for name, cam in rig.cameras.items():
                if camera_exists(cam.get("index_or_path", 0)):
                    available_cameras[name] = cam
                else:
                    print(f"Warning: Camera {name} at {cam.get('index_or_path', 0)} not found. Ignoring.")
            
            if available_cameras:
                cmd.append(f"--robot.cameras={camera_cli_value(available_cameras)}")
            else:
                print("Warning: No cameras found. Running without cameras.")
        else:
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
    display_data: bool = False,
    check_cameras: bool = True,
    resume: bool = False,
) -> list[str]:
    dataset_name = dataset_name or default_dataset_name(rig.name)
    repo_id = f"{hf_user}/{dataset_name}" if "/" not in dataset_name else dataset_name
    cmd = build_teleop(rig, display_data=display_data, check_cameras=check_cameras)
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
            f"--resume={'true' if resume else 'false'}",
        ]
    )
    return cmd


def build_replay(rig: Rig, repo_id: str, episode: int = 0) -> list[str]:
    return [
        "lerobot-replay",
        f"--robot.type={rig.follower.type}",
        f"--robot.port={rig.follower.port}",
        f"--robot.id={rig.follower.id}",
        "--robot.calibration_dir=.calibration",
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
    with log_path.open("ab") as log:
        log.write(("\n\n=== " + time.strftime("%Y-%m-%d %H:%M:%S") + " ===\n").encode())
        log.write(("+ " + shell_join(cmd) + "\n").encode())
        log.flush()
        # start_new_session=True makes the child its own session/group leader,
        # so its pid IS the process group id. Capture it now: looking it up later
        # via os.getpgid() fails once the child exits, orphaning its children.
        proc = subprocess.Popen(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    # The child inherited its own copy of the fd; close ours so it does not leak.
    running = RunningCommand(key=key, cmd=cmd, process=proc, pgid=proc.pid)
    with _RUNNING_LOCK:
        _RUNNING[key] = running
    return running


def stop_process(key: str) -> bool:
    with _RUNNING_LOCK:
        running = _RUNNING.get(key)
    if not running:
        return False
    proc = running.process
    if proc.poll() is None:
        # Prefer the pgid captured at spawn time; fall back to a live lookup only
        # if it was never recorded.
        pgid = running.pgid
        if pgid is None:
            try:
                pgid = os.getpgid(proc.pid)
            except OSError:
                pgid = None

        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGTERM)
            except OSError:
                pass

        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass

        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGKILL)
            except OSError:
                pass
        else:
            try:
                proc.kill()
            except OSError:
                pass

    with _RUNNING_LOCK:
        _RUNNING.pop(key, None)
    return True


def clear_process(key: str) -> None:
    with _RUNNING_LOCK:
        _RUNNING.pop(key, None)


def status() -> dict[str, dict[str, str | int | float | bool]]:
    out = {}
    with _RUNNING_LOCK:
        items = list(_RUNNING.items())
    for key, running in items:
        proc = running.process
        alive = proc.poll() is None
        
        log_text = ""
        log_path = Path("logs") / f"{key.replace('/', '_')}.log"
        if log_path.exists():
            try:
                with log_path.open("rb") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 4000))
                    log_text = f.read().decode("utf-8", errors="replace")
                    lines = log_text.splitlines()[-20:]
                    log_text = "\n".join(lines)
            except Exception as e:
                log_text = f"Error reading log: {e}"

        out[key] = {
            "alive": alive,
            "returncode": proc.returncode if proc.returncode is not None else "",
            "started_at": running.started_at,
            "cmd": shell_join(running.cmd),
            "log": log_text,
        }
    return out


def get_rig_from_env() -> Rig:
    return get_rig(os.environ.get("RIG", "rig01"), os.environ.get("ARMS_CONFIG", "configs/arms.yaml"))


def available_rigs() -> list[str]:
    return list_rigs(os.environ.get("ARMS_CONFIG", "configs/arms.yaml"))
