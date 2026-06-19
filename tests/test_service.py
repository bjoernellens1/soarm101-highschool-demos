import asyncio

import pytest

from soarm101_workshop.api.service import ProcessManager


@pytest.mark.asyncio
async def test_start_status_stop(tmp_path):
    m = ProcessManager(logs_dir=tmp_path, pidfile=tmp_path / "p.json")
    rp = await m.start("t/teleop", ["bash", "-c", "echo hi; sleep 5"])
    assert rp.pid > 0
    st = m.status()["t/teleop"]
    assert st["alive"] is True
    assert await m.stop("t/teleop") is True
    await asyncio.sleep(0.2)
    assert "t/teleop" not in m.status()


@pytest.mark.asyncio
async def test_exit_is_reflected(tmp_path):
    m = ProcessManager(logs_dir=tmp_path, pidfile=tmp_path / "p.json")
    await m.start("t/x", ["bash", "-c", "echo done"])
    await asyncio.sleep(0.3)
    st = m.status()["t/x"]
    assert st["alive"] is False and st["returncode"] == 0


@pytest.mark.asyncio
async def test_stop_all_and_reconcile(tmp_path):
    pf = tmp_path / "p.json"
    m = ProcessManager(logs_dir=tmp_path, pidfile=pf)
    await m.start("t/a", ["bash", "-c", "sleep 5"])
    await m.start("t/b", ["bash", "-c", "sleep 5"])
    await m.stop_all()
    await asyncio.sleep(0.2)
    assert m.status() == {}
    m2 = ProcessManager(logs_dir=tmp_path, pidfile=pf)
    killed = await m2.reconcile()
    assert killed == 0


@pytest.mark.asyncio
async def test_reconcile_kills_leftover(tmp_path):
    pf = tmp_path / "p.json"
    m = ProcessManager(logs_dir=tmp_path, pidfile=pf)
    await m.start("t/live", ["bash", "-c", "sleep 30"])
    # Simulate a crashed server: a fresh manager reading the same pidfile.
    m2 = ProcessManager(logs_dir=tmp_path, pidfile=pf)
    killed = await m2.reconcile()
    assert killed == 1
    await asyncio.sleep(0.3)
    # original process group should be gone now
    await m.stop_all()
