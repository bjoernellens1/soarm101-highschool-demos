from __future__ import annotations

import argparse
import json

import httpx

from .client.http import ApiClient


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="SO-ARM101 workshop API client")
    p.add_argument("--rig", default="rig01")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rigs", help="List configured stations")
    sub.add_parser("find-ports", help="Show discovered serial devices")
    sub.add_parser("status", help="Show running processes")
    sub.add_parser("teleop")
    sub.add_parser("calibrate-follower")
    sub.add_parser("calibrate-leader")
    sub.add_parser("safe-home")

    orch = sub.add_parser("orchestra")
    orch.add_argument("repo_id")
    orch.add_argument("--episode", type=int, default=0)
    orch.add_argument("--stations", nargs="+", help="default: all configured stations")

    rec = sub.add_parser("record")
    rec.add_argument("--episodes", type=int, default=5)
    rec.add_argument("--episode-time-s", type=int, default=20)
    rec.add_argument("--reset-time-s", type=int, default=10)
    rec.add_argument("--hf-user", default="local")
    rec.add_argument("--dataset-name")
    rec.add_argument("--push-to-hub", action="store_true")
    rec.add_argument("--resume", action="store_true")
    rec.add_argument("--display-data", action="store_true")
    rec.add_argument("--no-cameras", action="store_true")

    rep = sub.add_parser("replay")
    rep.add_argument("repo_id")
    rep.add_argument("--episode", type=int, default=0)

    stop = sub.add_parser("stop", help="Stop a specific action on --rig")
    stop.add_argument("action")
    sub.add_parser("stop-all")
    return p


def main() -> None:
    args = build_parser().parse_args()
    c = ApiClient()
    try:
        if args.cmd == "rigs":
            for r in c.get("/api/rigs"):
                print(f"{r['name']}: {r['label']}")
                print(f"  follower {r['follower']['id']} @ {r['follower']['port']}")
                print(f"  leader   {r['leader']['id']} @ {r['leader']['port']}")
        elif args.cmd == "find-ports":
            for d in c.get("/api/ports")["devices"]:
                print(d)
        elif args.cmd == "status":
            print(json.dumps(c.get("/api/processes"), indent=2))
        elif args.cmd == "teleop":
            print(c.post(f"/api/rigs/{args.rig}/teleop"))
        elif args.cmd in ("calibrate-follower", "calibrate-leader", "safe-home"):
            print(c.post(f"/api/rigs/{args.rig}/{args.cmd}"))
        elif args.cmd == "orchestra":
            print(
                c.post(
                    "/api/orchestra/play",
                    {"repo_id": args.repo_id, "episode": args.episode, "stations": args.stations},
                )
            )
        elif args.cmd == "record":
            print(
                c.post(
                    f"/api/rigs/{args.rig}/record",
                    {
                        "episodes": args.episodes,
                        "episode_time_s": args.episode_time_s,
                        "reset_time_s": args.reset_time_s,
                        "hf_user": args.hf_user,
                        "dataset_name": args.dataset_name,
                        "push_to_hub": args.push_to_hub,
                        "resume": args.resume,
                        "display_data": args.display_data,
                        "no_cameras": args.no_cameras,
                    },
                )
            )
        elif args.cmd == "replay":
            print(
                c.post(
                    f"/api/rigs/{args.rig}/replay",
                    {"repo_id": args.repo_id, "episode": args.episode},
                )
            )
        elif args.cmd == "stop":
            print(c.post(f"/api/processes/{args.rig}/{args.action}/stop"))
        elif args.cmd == "stop-all":
            print(c.post("/api/processes/stop-all"))
    except httpx.ConnectError:
        raise SystemExit("Cannot reach the API. Is it running?  Start it with: soarm-api")


if __name__ == "__main__":
    main()
