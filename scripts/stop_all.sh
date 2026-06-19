#!/usr/bin/env bash
# Workshop doc: stop_all.sh — stop every running process on every station.
set -euo pipefail
cd "$(dirname "$0")/.."
exec soarm-workshop stop-all
