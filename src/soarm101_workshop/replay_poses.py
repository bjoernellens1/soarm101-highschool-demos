from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from soarm101_workshop.lerobot_compat import import_so101_follower


def extract_action(saved_observation: dict) -> dict:
    """Best-effort conversion from a saved observation to an action.

    LeRobot action schemas vary by version. For a real workshop, test this once
    with your installed LeRobot version and adjust here if needed. The official
    CLI replay path in scripts/05_replay_episode.sh is more stable.
    """
    obs = saved_observation["observation"]
    if "observation.state" in obs:
        state = obs["observation.state"]
        return {"action": state}
    # Many LeRobot versions expose joint names directly in the observation dict.
    joint_like = {k: v for k, v in obs.items() if isinstance(v, (int, float))}
    if joint_like:
        return joint_like
    raise ValueError("Could not infer action from saved observation. Use official lerobot-replay.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a tiny named-pose choreography.")
    parser.add_argument("--port", required=True)
    parser.add_argument("--id", default="hs_follower_01")
    parser.add_argument("--poses", default="recordings/poses.json")
    parser.add_argument("--sequence", nargs="+", default=["HOME", "PICK", "LIFT", "DROP", "HOME"])
    parser.add_argument("--pause", type=float, default=1.0)
    args = parser.parse_args()

    poses = json.loads(Path(args.poses).read_text())
    cfg_cls, robot_cls = import_so101_follower()
    robot = robot_cls(cfg_cls(port=args.port, id=args.id, use_degrees=True))
    robot.connect(calibrate=False)

    try:
        for name in args.sequence:
            if name not in poses:
                print(f"Skipping missing pose: {name}")
                continue
            action = extract_action(poses[name])
            print(f"Sending pose: {name}")
            robot.send_action(action)
            time.sleep(args.pause)
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
