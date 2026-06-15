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

cat <<'MSG'

Install complete.

Activate with:
  source .venv/bin/activate

Then run:
  soarm-workshop rigs
  soarm-workshop find-ports
  soarm-web

MSG
