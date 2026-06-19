#!/usr/bin/env bash
set -euo pipefail

# Fallback install when uv is not desired. Python 3.12 is recommended for current LeRobot.

cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
"$PYTHON_BIN" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip wheel setuptools
python -m pip install -e '.[robot]'

# LeRobot pulls in opencv-python-headless, which shadows opencv-python and leaves
# cv2 without a GUI backend (cv2.imshow fails -> the color demo can't open a window).
# Force a GUI-capable build for scripts/06_color_sort_cv.py. The demo also has a
# --headless fallback, so this is best-effort.
python -m pip uninstall -y opencv-python-headless 2>/dev/null || true
python -m pip install --force-reinstall --no-deps opencv-python || true

cat <<'MSG'

Install complete.

Activate with:
  source .venv/bin/activate

Then run:
  soarm-workshop rigs
  soarm-workshop find-ports
  soarm-web

MSG
