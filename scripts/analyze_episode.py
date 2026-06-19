#!/usr/bin/env python3
"""Analyse recorded episodes for motion smoothness (Good vs Bad Demo).

Computes a smoothness score from the action trajectory of a LeRobot dataset.
Lower jerk => smoother => higher score. Pass one or two datasets (a path to a
dataset dir, or a repo_id like ``local/hs-so101-rig01-cube-sort``) to compare.
"""
from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path

import numpy as np


def _dataset_dir(arg: str) -> Path:
    p = Path(arg)
    if (p / "data").is_dir():
        return p
    cache = Path(os.environ.get("HF_LEROBOT_HOME", Path.home() / ".cache/huggingface/lerobot"))
    cand = cache / arg
    if (cand / "data").is_dir():
        return cand
    raise SystemExit(f"No dataset found for {arg!r} (looked in {p} and {cand})")


def load_actions(arg: str) -> np.ndarray:
    """Return an (N_frames, N_joints) array of actions from a dataset."""
    import pandas as pd

    files = sorted(glob.glob(str(_dataset_dir(arg) / "data" / "**" / "*.parquet"), recursive=True))
    if not files:
        raise SystemExit(f"No parquet data files under {arg!r}")
    frames = [pd.read_parquet(f) for f in files]
    df = pd.concat(frames, ignore_index=True)
    col = "action" if "action" in df.columns else "observation.state"
    if col not in df.columns:
        raise SystemExit(f"No 'action'/'observation.state' column in {arg!r}")
    return np.array([np.asarray(row, dtype=float) for row in df[col].to_list()])


def smoothness(actions: np.ndarray, fps: int = 30) -> dict:
    """Smoothness metrics from a trajectory. Higher score = smoother."""
    if actions.ndim != 2 or len(actions) < 4:
        return {"frames": int(len(actions)), "mean_speed": 0.0, "mean_jerk": 0.0, "score": 0.0}
    vel = np.diff(actions, axis=0) * fps
    acc = np.diff(vel, axis=0) * fps
    jerk = np.diff(acc, axis=0) * fps
    mean_speed = float(np.mean(np.abs(vel)))
    mean_jerk = float(np.mean(np.abs(jerk)))
    score = float(1000.0 / (1.0 + mean_jerk))
    return {
        "frames": int(len(actions)),
        "mean_speed": round(mean_speed, 3),
        "mean_jerk": round(mean_jerk, 3),
        "score": round(score, 2),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Episode smoothness analysis (good vs bad demo).")
    p.add_argument("datasets", nargs="+", help="dataset dir(s) or repo_id(s)")
    p.add_argument("--fps", type=int, default=30)
    args = p.parse_args()

    results = {}
    for ds in args.datasets:
        m = smoothness(load_actions(ds), fps=args.fps)
        results[ds] = m
        print(f"{ds}: frames={m['frames']} mean_speed={m['mean_speed']} "
              f"mean_jerk={m['mean_jerk']} smoothness_score={m['score']}")
    if len(results) == 2:
        a, b = list(results)
        smoother = a if results[a]["score"] >= results[b]["score"] else b
        print(f"\nSmoother demo: {smoother} (higher score = cleaner motion).")


if __name__ == "__main__":
    main()
