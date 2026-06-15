from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from soarm101_workshop.lerobot_compat import import_so101_follower


def main() -> None:
    parser = argparse.ArgumentParser(description="Record named joint poses from the SO-101 follower.")
    parser.add_argument("--port", required=True)
    parser.add_argument("--id", default="hs_follower_01")
    parser.add_argument("--out", default="recordings/poses.json")
    args = parser.parse_args()

    cfg_cls, robot_cls = import_so101_follower()
    robot = robot_cls(cfg_cls(port=args.port, id=args.id, use_degrees=True))
    robot.connect(calibrate=False)

    poses: dict[str, dict] = {}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    try:
        print("Move the follower manually only if torque is disabled / safe for your setup.")
        print("For each pose, type a name like HOME, PICK, LIFT, DROP. Empty name quits.")
        while True:
            name = input("Pose name> ").strip()
            if not name:
                break
            obs = robot.get_observation()
            poses[name] = {"time": time.time(), "observation": obs}
            Path(args.out).write_text(json.dumps(poses, indent=2, default=str))
            print(f"Saved {name} to {args.out}")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
