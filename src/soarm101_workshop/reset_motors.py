"""Reset / recover the motor buses of a rig without a physical power-cycle.

Feetech servos can wedge after an abrupt kill or an overload lock, showing up as
"Missing motor ID" on the next connect. This utility opens each arm's bus
*without* the full handshake (which would abort on a missing motor), pings to
report exactly which IDs respond, and toggles torque off on the ones that do —
which clears soft/torque locks and resets the serial connection state.

It cannot revive a truly unpowered servo (check the arm's power supply / the
daisy-chain connector for the missing IDs it reports).
"""
from __future__ import annotations

import argparse

from soarm101_workshop.config import get_rig
from soarm101_workshop.lerobot_compat import import_so101_follower, import_so101_leader


def reset_bus(bus, label: str) -> tuple[list[int], list[int]]:
    """Ping a bus, report present/missing IDs, and release torque on present ones."""
    expected = {name: m.id for name, m in bus.motors.items()}
    bus._connect(handshake=False)
    try:
        try:
            bus.set_baudrate(bus.default_baudrate)
        except Exception:
            pass
        found = bus.broadcast_ping() or {}
        present = sorted(found)
        missing = sorted(mid for mid in expected.values() if mid not in found)
        print(f"{label}: present IDs {present or '[]'}; missing IDs {missing or '[]'}")
        for name, mid in expected.items():
            if mid in found:
                try:
                    bus.disable_torque(name)
                except Exception as e:  # noqa: BLE001 - best effort recovery
                    print(f"  {label} {name}(id {mid}): torque release failed: {e}")
        return present, missing
    finally:
        try:
            bus.disconnect(disable_torque=False)
        except Exception:
            pass


def _make_bus(import_fn, port: str, rid: str):
    cfg_cls, cls = import_fn()
    try:
        dev = cls(cfg_cls(port=port, id=rid, use_degrees=True))
    except TypeError:
        dev = cls(cfg_cls(port=port, id=rid))
    return dev.bus


def main() -> None:
    p = argparse.ArgumentParser(description="Reset/recover a rig's motor buses (ping + torque release).")
    p.add_argument("--rig", default="rig01", help="rigNN or station_N")
    args = p.parse_args()
    rig = get_rig(args.rig)

    print(f"Resetting motor buses for {rig.name} ({rig.label})")
    ok = True
    for label, arm, import_fn in (
        ("follower", rig.follower, import_so101_follower),
        ("leader", rig.leader, import_so101_leader),
    ):
        try:
            present, missing = reset_bus(_make_bus(import_fn, arm.port, arm.id), label)
            if missing or not present:
                ok = False
        except Exception as e:  # noqa: BLE001
            print(f"{label}: bus error: {type(e).__name__}: {e}")
            ok = False
    print("RESET COMPLETE" if ok else "RESET INCOMPLETE — check power/daisy-chain for missing IDs")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
