#!/usr/bin/env python3
"""Print a portable snapshot of connected serial/video devices.

Use this before a workshop to map physical arms to stable names. The output is
plain text so teachers can paste it into an issue, README, or setup notes.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        return f"<unavailable: {' '.join(cmd)}: {exc}>"


def list_dir(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for item in sorted(p.iterdir()):
        try:
            target = os.path.realpath(item)
        except OSError:
            target = "?"
        out.append(f"{item} -> {target}")
    return out


def main() -> None:
    print("# SO-ARM101 device snapshot")
    print()
    print("## Host")
    print(run(["hostnamectl"]))
    print()

    print("## USB summary")
    print(run(["lsusb"]))
    print()

    print("## Serial by-id symlinks")
    lines = list_dir("/dev/serial/by-id")
    print("\n".join(lines) if lines else "<none>")
    print()

    print("## Serial by-path symlinks")
    lines = list_dir("/dev/serial/by-path")
    print("\n".join(lines) if lines else "<none>")
    print()

    print("## ACM/USB devices")
    for glob in ("/dev/ttyACM*", "/dev/ttyUSB*", "/dev/video*"):
        items = sorted(Path("/dev").glob(Path(glob).name))
        for item in items:
            print(item)
    print()

    print("## LeRobot port helper")
    print(run(["lerobot-find-port"]))


if __name__ == "__main__":
    main()
