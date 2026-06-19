#!/usr/bin/env bash
# Reset/recover a station's motor buses: ping IDs, release torque locks, reset
# the serial connection. Works around wedged Feetech buses without a power-cycle.
# Reports which motor IDs are missing (check power/daisy-chain for those).
set -euo pipefail
cd "$(dirname "$0")/.."
STATION="${1:-station_1}"
exec soarm-workshop --rig "$STATION" reset
