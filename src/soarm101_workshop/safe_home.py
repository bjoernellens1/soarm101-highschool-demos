"""Move a follower arm to a safe neutral pose and hold it.

Used by the pre-class checklist (`scripts/safe_home.sh`) and the API
``/api/rigs/{rig}/safe-home`` endpoint. The follower is moved gradually to a
configurable home pose (joint centres in degrees, gripper half-open) and torque
is left ENABLED so the arm holds position instead of going limp and dropping.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

from soarm101_workshop.lerobot_compat import import_so101_follower

DEFAULT_HOME = {
    "shoulder_pan.pos": 0.0,
    "shoulder_lift.pos": 0.0,
    "elbow_flex.pos": 0.0,
    "wrist_flex.pos": 0.0,
    "wrist_roll.pos": 0.0,
    "gripper.pos": 50.0,
}


def interpolate(start: dict, target: dict, steps: int):
    for i in range(1, steps + 1):
        t = i / steps
        yield {k: start.get(k, target[k]) + (target[k] - start.get(k, target[k])) * t for k in target}


def main() -> None:
    parser = argparse.ArgumentParser(description="Move a follower to a safe home pose and hold.")
    parser.add_argument("--port", required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--duration", type=float, default=2.0)
    args = parser.parse_args()

    cfg_cls, robot_cls = import_so101_follower()
    try:
        robot = robot_cls(
            cfg_cls(
                port=args.port,
                id=args.id,
                calibration_dir=Path(".calibration"),
                use_degrees=True,
                disable_torque_on_disconnect=False,  # hold the home pose
            )
        )
    except TypeError:
        robot = robot_cls(cfg_cls(port=args.port, id=args.id, use_degrees=True))

    robot.connect(calibrate=False)
    try:
        obs = robot.get_observation()
        start = {k: float(v) for k, v in obs.items() if k in DEFAULT_HOME}
        dt = args.duration / args.steps
        for action in interpolate(start, DEFAULT_HOME, args.steps):
            robot.send_action(action)
            time.sleep(dt)
        print(f"{args.id} moved to safe home pose and holding.")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
