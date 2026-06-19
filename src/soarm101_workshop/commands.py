from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from .config import Rig, camera_cli_value, default_dataset_name

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


def build_reset(rig: Rig) -> list[str]:
    return ["python", "-m", "soarm101_workshop.reset_motors", "--rig", rig.name]


def build_safe_home(rig: Rig) -> list[str]:
    return [
        "python",
        "-m",
        "soarm101_workshop.safe_home",
        "--port",
        rig.follower.port,
        "--id",
        rig.follower.id,
    ]


def shell_join(cmd: list[str]) -> str:
    return " ".join(shlex.quote(x) for x in cmd)


def run_blocking(cmd: list[str], *, cwd: str | Path | None = None) -> int:
    print("+", shell_join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=False).returncode

