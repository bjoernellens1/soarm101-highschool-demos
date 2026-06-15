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

cat <<'MSG'

Install complete.

Activate with:
  source .venv/bin/activate

Then run:
  soarm-workshop rigs
  soarm-workshop find-ports
  soarm-web

MSG
