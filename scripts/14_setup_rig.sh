#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python tools/setup_rig.py "$@"
