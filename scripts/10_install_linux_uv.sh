#!/usr/bin/env bash
set -euo pipefail

# Self-contained workshop install.
# Creates a local .venv inside the repo and installs this wrapper plus LeRobot.
# Use on the teacher PC / workshop laptop. Re-run after pulling updates.

cd "$(dirname "$0")/.."

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Installing uv into the current user account..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

uv venv --python 3.12 .venv
# shellcheck disable=SC1091
source .venv/bin/activate

uv pip install -U pip wheel setuptools
uv pip install -e '.[robot]'

# LeRobot pulls in opencv-python-headless, which shadows opencv-python and leaves
# cv2 without a GUI backend (cv2.imshow fails -> the color demo can't open a window).
# Force a GUI-capable build for scripts/06_color_sort_cv.py. The demo also has a
# --headless fallback, so this is best-effort.
uv pip uninstall opencv-python-headless 2>/dev/null || true
uv pip install --force-reinstall --no-deps opencv-python || true

cat <<'MSG'

Install complete.

Activate with:
  source .venv/bin/activate

Then run:
  soarm-workshop rigs
  soarm-workshop find-ports
  soarm-web

MSG
