#!/usr/bin/env python3
"""Backup and restore LeRobot calibration/configuration data for workshops.

The exact calibration cache path has changed across LeRobot versions. This tool
therefore backs up all common calibration locations plus the local workshop config.
It stores a tar.gz with metadata so a teacher can move a calibrated setup to a
new laptop or recover after a reinstall.
"""
from __future__ import annotations

import argparse
import getpass
import json
import platform
import shutil
import subprocess
import tarfile
import time
from pathlib import Path

COMMON_CALIBRATION_DIRS = [
    # Local project calibration dir (the layout this repo's scripts use via
    # --robot.calibration_dir=.calibration). Listed first so it is always captured.
    ".calibration",
    "~/.cache/huggingface/lerobot/calibration",
    "~/.cache/lerobot/calibration",
    "~/.cache/calibration",
]
PROJECT_FILES = [
    "configs/arms.yaml",
    "configs/arms.env",
    "configs/arms.env.example",
]


def expand(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def existing_backup_paths(extra: list[str]) -> list[Path]:
    candidates = [expand(p) for p in COMMON_CALIBRATION_DIRS]
    candidates += [expand(p) for p in extra]
    candidates += [Path(p).resolve() for p in PROJECT_FILES if Path(p).exists()]
    # Keep parents before children from duplicating content.
    unique: list[Path] = []
    for p in candidates:
        if p.exists() and not any(_is_relative_to(p, parent) for parent in unique):
            unique.append(p)
    return unique


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # noqa: BLE001 - metadata should be best effort
        return f"<unavailable: {' '.join(cmd)}: {exc}>"


def rel_name(path: Path) -> str:
    home = Path.home().resolve()
    cwd = Path.cwd().resolve()
    if _is_relative_to(path, home):
        return "HOME/" + str(path.relative_to(home))
    if _is_relative_to(path, cwd):
        return "PROJECT/" + str(path.relative_to(cwd))
    return "ABS/" + str(path).lstrip("/")


def path_from_rel(
    name: str, target_home: Path, target_project: Path, allow_absolute: bool = False
) -> Path | None:
    """Resolve an archive member name to a destination path.

    Guards against path traversal: a crafted archive could contain
    ``HOME/../../etc/passwd`` or ``ABS/etc/passwd`` to write outside the intended
    roots. We resolve the candidate and require it to stay within its declared
    root; ``ABS/`` entries are refused unless explicitly allowed.
    """
    if name.startswith("HOME/"):
        root, dest = target_home, (target_home / name[len("HOME/") :]).resolve()
    elif name.startswith("PROJECT/"):
        root, dest = target_project, (target_project / name[len("PROJECT/") :]).resolve()
    elif name.startswith("ABS/"):
        if not allow_absolute:
            print(f"refusing absolute archive path (use --allow-absolute): {name}")
            return None
        return (Path("/") / name[len("ABS/") :]).resolve()
    else:
        return None
    if not _is_relative_to(dest, root.resolve()):
        print(f"refusing path-traversal archive entry: {name}")
        return None
    return dest


def backup(args: argparse.Namespace) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    archive = out_dir / f"so101-calibration-backup-{stamp}.tar.gz"
    paths = existing_backup_paths(args.extra_path or [])

    metadata = {
        "created_at": stamp,
        "host": platform.node(),
        "user": getpass.getuser(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cwd": str(Path.cwd()),
        "home": str(Path.home()),
        "paths": [str(p) for p in paths],
        "serial_by_id": run(["bash", "-lc", "ls -l /dev/serial/by-id 2>/dev/null || true"]),
        "serial_by_path": run(["bash", "-lc", "ls -l /dev/serial/by-path 2>/dev/null || true"]),
        "lerobot_version": run(["bash", "-lc", "python - <<'PY'\ntry:\n import lerobot\n print(getattr(lerobot, '__version__', 'unknown'))\nexcept Exception as e:\n print('unavailable:', e)\nPY"]),
        "note": args.note or "",
    }

    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("METADATA.json")
        data = json.dumps(metadata, indent=2).encode()
        info.size = len(data)
        tar.addfile(info, fileobj=__import__("io").BytesIO(data))
        for path in paths:
            tar.add(path, arcname=rel_name(path))

    print(f"Created {archive}")
    if not paths:
        print("Warning: no known calibration/configuration paths existed. Check your LeRobot version/cache path.")


def restore(args: argparse.Namespace) -> None:
    archive = Path(args.archive).resolve()
    if not archive.exists():
        raise FileNotFoundError(archive)
    target_home = expand(args.target_home or str(Path.home()))
    target_project = Path.cwd().resolve()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    pre_dir = Path(args.pre_restore_backup_dir or "calibration_backups/pre_restore") / stamp

    with tarfile.open(archive, "r:gz") as tar:
        members = [m for m in tar.getmembers() if m.name != "METADATA.json"]
        print(f"Archive contains {len(members)} path entries")
        for member in members:
            dest = path_from_rel(member.name, target_home, target_project, args.allow_absolute)
            if dest is None:
                print(f"skip unknown archive path: {member.name}")
                continue
            print(f"{member.name} -> {dest}")

        if args.dry_run:
            print("Dry run only; nothing restored.")
            return

        pre_dir.mkdir(parents=True, exist_ok=True)
        # Backup current destinations first.
        for member in members:
            dest = path_from_rel(member.name, target_home, target_project, args.allow_absolute)
            if dest and dest.exists():
                backup_dest = pre_dir / member.name
                backup_dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.is_dir():
                    shutil.copytree(dest, backup_dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(dest, backup_dest)

        for member in members:
            dest = path_from_rel(member.name, target_home, target_project, args.allow_absolute)
            if dest is None:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            src = tar.extractfile(member) if member.isfile() else None
            if member.isdir():
                dest.mkdir(parents=True, exist_ok=True)
            elif src is not None:
                with src, dest.open("wb") as out:
                    shutil.copyfileobj(src, out)

    print(f"Restore complete. Previous files, if any, were copied to {pre_dir}")


def list_archive(args: argparse.Namespace) -> None:
    with tarfile.open(args.archive, "r:gz") as tar:
        for member in tar.getmembers():
            print(member.name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup/restore SO-101 LeRobot calibration data")
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backup")
    b.add_argument("--out-dir", default="calibration_backups")
    b.add_argument("--extra-path", action="append", help="Additional calibration/cache path to include")
    b.add_argument("--note", default="")
    b.set_defaults(func=backup)

    r = sub.add_parser("restore")
    r.add_argument("archive")
    r.add_argument("--target-home", default=None)
    r.add_argument("--pre-restore-backup-dir", default=None)
    r.add_argument("--dry-run", action="store_true")
    r.add_argument(
        "--allow-absolute",
        action="store_true",
        help="Permit restoring ABS/ archive entries to absolute paths (off by default for safety)",
    )
    r.set_defaults(func=restore)

    lst = sub.add_parser("list")
    lst.add_argument("archive")
    lst.set_defaults(func=list_archive)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
