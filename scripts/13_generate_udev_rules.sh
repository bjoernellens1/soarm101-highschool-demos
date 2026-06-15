#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python tools/generate_udev_rules.py "$@"
