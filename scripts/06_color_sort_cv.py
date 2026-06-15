#!/usr/bin/env python3
"""Camera-only color sorting demo for the SO-ARM101 workshop.

This intentionally does not move the robot. It teaches the sensing decision:
red -> left bin, blue -> right bin, green -> middle bin.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ColorRule:
    name: str
    lower1: tuple[int, int, int]
    upper1: tuple[int, int, int]
    lower2: tuple[int, int, int] | None = None
    upper2: tuple[int, int, int] | None = None
    target: str = "unknown"


def mask_for_rule(hsv: np.ndarray, rule: ColorRule) -> np.ndarray:
    mask = cv2.inRange(hsv, np.array(rule.lower1), np.array(rule.upper1))
    if rule.lower2 and rule.upper2:
        mask |= cv2.inRange(hsv, np.array(rule.lower2), np.array(rule.upper2))
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def largest_blob(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(contour)
    if area < 700:
        return None
    x, y, w, h = cv2.boundingRect(contour)
    return x, y, w, h


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", default="0", help="OpenCV camera index or path")
    args = parser.parse_args()

    camera: int | str
    try:
        camera = int(args.camera)
    except ValueError:
        camera = args.camera

    rules = [
        ColorRule("red", (0, 80, 60), (10, 255, 255), (170, 80, 60), (180, 255, 255), "LEFT BIN"),
        ColorRule("blue", (95, 70, 50), (135, 255, 255), target="RIGHT BIN"),
        ColorRule("green", (35, 60, 50), (85, 255, 255), target="MIDDLE BIN"),
    ]

    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera {args.camera!r}")

    print("Press q to quit. Show a red/blue/green object to the camera.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        best = None
        for rule in rules:
            blob = largest_blob(mask_for_rule(hsv, rule))
            if blob is None:
                continue
            x, y, w, h = blob
            area = w * h
            if best is None or area > best[0]:
                best = (area, rule, blob)

        if best:
            _, rule, (x, y, w, h) = best
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
            label = f"{rule.name.upper()} -> {rule.target}"
        else:
            label = "No object detected"

        cv2.putText(frame, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.imshow("SO-ARM101 color decision demo", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
