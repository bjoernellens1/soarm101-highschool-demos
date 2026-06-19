"""Shared HSV colour-detection core for the workshop vision demos.

Used by scripts/detect_color.py (GUI demo) and scripts/vision_hint.py (text
hint per station). Kept dependency-light: numpy + opencv only.
"""
from __future__ import annotations

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


DEFAULT_RULES = [
    ColorRule("red", (0, 80, 60), (10, 255, 255), (170, 80, 60), (180, 255, 255), "LEFT BIN"),
    ColorRule("blue", (95, 70, 50), (135, 255, 255), target="RIGHT BIN"),
    ColorRule("green", (35, 60, 50), (85, 255, 255), target="MIDDLE BIN"),
]


def mask_for_rule(hsv: np.ndarray, rule: ColorRule) -> np.ndarray:
    mask = cv2.inRange(hsv, np.array(rule.lower1), np.array(rule.upper1))
    if rule.lower2 and rule.upper2:
        mask |= cv2.inRange(hsv, np.array(rule.lower2), np.array(rule.upper2))
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def largest_blob(mask: np.ndarray, min_area: int = 700) -> tuple[int, int, int, int] | None:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < min_area:
        return None
    return cv2.boundingRect(contour)


def position_label(x: int, w: int, frame_width: int) -> str:
    center = x + w / 2
    third = frame_width / 3
    return "left" if center < third else "right" if center > 2 * third else "center"


def detect_dominant(frame_bgr: np.ndarray, rules: list[ColorRule] = DEFAULT_RULES) -> dict | None:
    """Return the largest detected coloured object, or None.

    {name, target, position(left/center/right), bbox(x,y,w,h)}.
    """
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    best = None
    for rule in rules:
        blob = largest_blob(mask_for_rule(hsv, rule))
        if blob is None:
            continue
        x, y, w, h = blob
        area = w * h
        if best is None or area > best[0]:
            best = (area, rule, blob)
    if best is None:
        return None
    _, rule, (x, y, w, h) = best
    return {
        "name": rule.name,
        "target": rule.target,
        "position": position_label(x, w, frame_bgr.shape[1]),
        "bbox": (x, y, w, h),
    }
