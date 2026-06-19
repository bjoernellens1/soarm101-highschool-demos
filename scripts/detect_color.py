#!/usr/bin/env python3
"""Workshop-doc alias for the colour-detection demo.

Thin wrapper around scripts/06_color_sort_cv.py so the command in the workshop
document (`./scripts/detect_color.py --camera 0`) works as written.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    target = Path(__file__).parent / "06_color_sort_cv.py"
    raise SystemExit(subprocess.run([sys.executable, str(target), *sys.argv[1:]]).returncode)
