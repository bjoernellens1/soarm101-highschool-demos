from __future__ import annotations

import asyncio
import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..commands import shell_join


@dataclass
class RunningProc:
    key: str
    cmd: list[str]
    process: subprocess.Popen
    pid: int
    pgid: int
    started_at: float = field(default_factory=time.time)


def _read_log_tail(log_path: Path, max_bytes: int = 4000, max_lines: int = 20) -> str:
    if not log_path.exists():
        return ""
    try:
        with log_path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - max_bytes))
            text = f.read().decode("utf-8", errors="replace")
        return "\n".join(text.splitlines()[-max_lines:])
    except OSError as e:
        return f"<log read error: {e}>"


class ProcessManager:
    """Async-safe registry of child process groups for rig operations.

    Single-worker only (serial ports are exclusive). The pgid is captured at
    spawn time so the whole group can always be killed even after the parent
    exits, and running entries are persisted to a pidfile so a restart can reap
    orphans.
    """

    def __init__(self, logs_dir: Path = Path("logs"), pidfile: Path | None = None):
        self.logs_dir = Path(logs_dir)
        self.pidfile = Path(pidfile) if pidfile else self.logs_dir / ".processes.json"
        self._procs: dict[str, RunningProc] = {}
        self._lock = asyncio.Lock()

    def log_path(self, key: str) -> Path:
        return self.logs_dir / f"{key.replace('/', '_')}.log"

    def _persist(self) -> None:
        data = {k: {"pid": p.pid, "pgid": p.pgid, "cmd": p.cmd} for k, p in self._procs.items()}
        self.pidfile.parent.mkdir(parents=True, exist_ok=True)
        self.pidfile.write_text(json.dumps(data))

    async def start(self, key: str, cmd: list[str]) -> RunningProc:
        await self.stop(key)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.log_path(key)
        async with self._lock:
            with log_path.open("ab") as log:
                log.write(("\n\n=== " + time.strftime("%Y-%m-%d %H:%M:%S") + " ===\n").encode())
                log.write(("+ " + shell_join(cmd) + "\n").encode())
                log.flush()
                proc = subprocess.Popen(
                    cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
                )
            rp = RunningProc(key=key, cmd=cmd, process=proc, pid=proc.pid, pgid=proc.pid)
            self._procs[key] = rp
            self._persist()
        return rp

    @staticmethod
    def _kill_group(pgid: int) -> None:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except OSError:
            return
        for _ in range(30):
            try:
                os.killpg(pgid, 0)
            except OSError:
                return
            time.sleep(0.1)
        try:
            os.killpg(pgid, signal.SIGKILL)
        except OSError:
            pass

    async def stop(self, key: str) -> bool:
        async with self._lock:
            rp = self._procs.get(key)
            if not rp:
                return False
            if rp.process.poll() is None:
                # _kill_group blocks up to ~3s on the SIGTERM grace wait; run it off
                # the event loop so health checks / status stay responsive.
                await asyncio.to_thread(self._kill_group, rp.pgid)
            self._procs.pop(key, None)
            self._persist()
        return True

    async def stop_all(self) -> None:
        for key in list(self._procs):
            await self.stop(key)

    def clear(self, key: str) -> None:
        self._procs.pop(key, None)
        self._persist()

    def status(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for key, rp in list(self._procs.items()):
            alive = rp.process.poll() is None
            out[key] = {
                "key": key,
                "alive": alive,
                "returncode": rp.process.returncode,
                "started_at": rp.started_at,
                "cmd": shell_join(rp.cmd),
                "log": _read_log_tail(self.log_path(key)),
            }
        return out

    async def reconcile(self) -> int:
        """On startup, kill any process groups left running from a previous run."""
        if not self.pidfile.exists():
            return 0
        try:
            data = json.loads(self.pidfile.read_text())
        except (OSError, ValueError):
            return 0
        killed = 0
        for entry in data.values():
            pgid = entry.get("pgid")
            if pgid is None:
                continue
            try:
                os.killpg(pgid, 0)
            except OSError:
                continue
            self._kill_group(pgid)
            killed += 1
        self.pidfile.write_text("{}")
        return killed


manager = ProcessManager()
