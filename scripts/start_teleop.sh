#!/usr/bin/env bash
# Workshop doc: start_teleop.sh <station>  (e.g. station_1). Puppet mode.
# Requires the API running (soarm-api) and SOARM_API_TOKEN set if auth is on.
set -euo pipefail
cd "$(dirname "$0")/.."
STATION="${1:-station_1}"
exec soarm-workshop --rig "$STATION" teleop
