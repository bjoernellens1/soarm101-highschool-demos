#!/usr/bin/env python3
"""Vision hint: print a coarse colour/position hint for a station.

Bonus demo from the workshop doc — the camera only *hints* ("red cube left");
students still drive the arm. No GUI required (good for headless stations).
"""
from __future__ import annotations

import argparse
import time

import cv2

from soarm101_workshop.config import get_rig
from soarm101_workshop.vision import detect_dominant

POS_DE = {"left": "links", "center": "Mitte", "right": "rechts"}
NAME_DE = {"red": "roter", "blue": "blauer", "green": "gruener"}


def camera_index_for(station: str | None, fallback: int) -> int:
    if station is None:
        return fallback
    rig = get_rig(station)
    cam = next(iter(rig.cameras.values()), None)
    if cam and isinstance(cam.get("index_or_path"), int):
        return cam["index_or_path"]
    return fallback


def main() -> None:
    p = argparse.ArgumentParser(description="Coarse colour hint for a station camera.")
    p.add_argument("--station", help="station_N / rigNN (reads its camera index from config)")
    p.add_argument("--camera", type=int, default=0, help="camera index if --station not given")
    p.add_argument("--once", action="store_true", help="print one detection and exit")
    args = p.parse_args()

    index = camera_index_for(args.station, args.camera)
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {index}")
    print(f"Vision hint on camera {index}. Ctrl+C to stop.")
    last = None
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            det = detect_dominant(frame)
            hint = (
                f"{NAME_DE.get(det['name'], det['name'])} Wuerfel {POS_DE[det['position']]}"
                if det
                else "kein Objekt erkannt"
            )
            if hint != last:
                print(hint)
                last = hint
            if args.once:
                break
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()


if __name__ == "__main__":
    main()
