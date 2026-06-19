from __future__ import annotations

import argparse
import os
import subprocess
from dataclasses import replace
from pathlib import Path

from .commands import (
    build_calibrate_follower,
    build_calibrate_leader,
    build_record,
    build_replay,
    build_teleop,
    run_blocking,
    shell_join,
)
from .config import get_rig, list_rigs


def main() -> None:
    parser = argparse.ArgumentParser(description="SO-ARM101 high-school workshop convenience CLI")
    parser.add_argument("--config", default=os.environ.get("ARMS_CONFIG", "configs/arms.yaml"))
    parser.add_argument("--rig", default=os.environ.get("RIG", "rig01"))
    parser.add_argument("--no-cameras", action="store_true", default=os.environ.get("NO_CAMERAS") == "1", help="Tolerate no cameras connected")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("rigs", help="List configured stations")
    sub.add_parser("find-ports", help="Show USB serial devices")
    sub.add_parser("calibrate-follower")
    sub.add_parser("calibrate-leader")
    tel = sub.add_parser("teleop")
    tel.add_argument("--display-data", action="store_true", help="Open the Rerun live view (spawns a viewer that outlives the run)")

    rec = sub.add_parser("record")
    rec.add_argument("--hf-user", default=os.environ.get("HF_USER", "local"))
    rec.add_argument("--dataset-name", default=os.environ.get("DATASET_NAME"))
    rec.add_argument("--episodes", type=int, default=5)
    rec.add_argument("--episode-time-s", type=int, default=20)
    rec.add_argument("--reset-time-s", type=int, default=10)
    rec.add_argument("--push-to-hub", action="store_true")
    rec.add_argument("--resume", action="store_true", help="Append to an existing dataset instead of failing if it exists")
    rec.add_argument("--display-data", action="store_true", help="Open the Rerun live view")

    replay = sub.add_parser("replay")
    replay.add_argument("repo_id")
    replay.add_argument("--episode", type=int, default=0)

    sub.add_parser("web")
    sub.add_parser("color-demo")

    args = parser.parse_args()

    if args.cmd == "rigs":
        for name in list_rigs(args.config):
            rig = get_rig(name, args.config)
            print(f"{name}: {rig.label}")
            print(f"  follower {rig.follower.id} @ {rig.follower.port}")
            print(f"  leader   {rig.leader.id} @ {rig.leader.port}")
        return

    if args.cmd == "find-ports":
        script = Path("tools/snapshot_devices.py")
        if script.exists():
            subprocess.run(["python", str(script)], check=True)
        else:
            subprocess.run(["lerobot-find-port"], check=True)
        return

    if args.cmd == "web":
        from .web_app import main as web_main

        web_main()
        return

    if args.cmd == "color-demo":
        subprocess.run(["python", "scripts/06_color_sort_cv.py"], check=True)
        return

    rig = get_rig(args.rig, args.config)
    if args.no_cameras:
        rig = replace(rig, cameras={})
    builders = {
        "calibrate-follower": build_calibrate_follower,
        "calibrate-leader": build_calibrate_leader,
    }
    if args.cmd in builders:
        cmd = builders[args.cmd](rig)
        print(shell_join(cmd))
        raise SystemExit(run_blocking(cmd))

    if args.cmd == "teleop":
        cmd = build_teleop(rig, display_data=args.display_data)
        print(shell_join(cmd))
        raise SystemExit(run_blocking(cmd))

    if args.cmd == "record":
        cmd = build_record(
            rig,
            hf_user=args.hf_user,
            dataset_name=args.dataset_name,
            episodes=args.episodes,
            episode_time_s=args.episode_time_s,
            reset_time_s=args.reset_time_s,
            push_to_hub=args.push_to_hub,
            resume=args.resume,
            display_data=args.display_data,
        )
        print(shell_join(cmd))
        raise SystemExit(run_blocking(cmd))

    if args.cmd == "replay":
        cmd = build_replay(rig, args.repo_id, args.episode)
        print(shell_join(cmd))
        raise SystemExit(run_blocking(cmd))


if __name__ == "__main__":
    main()
