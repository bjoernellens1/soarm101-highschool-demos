#!/usr/bin/env bash
# Workshop doc: safe_home.sh [station] — move follower(s) to a safe pose and hold.
# Default: station_1. Pass a station (station_1..5) for a specific one.
set -euo pipefail
cd "$(dirname "$0")/.."
STATION="${1:-station_1}"
exec soarm-workshop --rig "$STATION" safe-home
