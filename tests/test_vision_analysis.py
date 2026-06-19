import importlib.util
import sys
from pathlib import Path

import numpy as np

from soarm101_workshop.vision import detect_dominant, position_label

# Load scripts/analyze_episode.py (not a package module).
_spec = importlib.util.spec_from_file_location(
    "analyze_episode", Path(__file__).parent.parent / "scripts" / "analyze_episode.py"
)
analyze = importlib.util.module_from_spec(_spec)
sys.modules["analyze_episode"] = analyze
_spec.loader.exec_module(analyze)


def _swatch(bgr, x0=60, x1=140):
    import cv2

    frame = np.zeros((200, 300, 3), np.uint8)
    cv2.rectangle(frame, (x0, 60), (x1, 140), bgr, -1)
    return frame


def test_detect_color_and_target():
    assert detect_dominant(_swatch((0, 0, 255)))["name"] == "red"
    assert detect_dominant(_swatch((255, 0, 0)))["target"] == "RIGHT BIN"
    assert detect_dominant(np.zeros((200, 300, 3), np.uint8)) is None


def test_position_label():
    assert position_label(10, 20, 300) == "left"
    assert position_label(140, 20, 300) == "center"
    assert position_label(270, 20, 300) == "right"


def test_smoothness_ranks_smooth_above_jittery():
    t = np.linspace(0, 1, 100)
    smooth = np.stack([t, t * 2], axis=1)  # linear ramps -> ~zero jerk
    rng = np.random.default_rng(0)
    jittery = smooth + rng.normal(0, 0.2, smooth.shape)
    s_smooth = analyze.smoothness(smooth)
    s_jit = analyze.smoothness(jittery)
    assert s_smooth["score"] > s_jit["score"]
    assert s_smooth["frames"] == 100


def test_smoothness_handles_short_input():
    m = analyze.smoothness(np.zeros((2, 3)))
    assert m["score"] == 0.0
