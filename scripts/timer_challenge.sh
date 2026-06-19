#!/usr/bin/env bash
# Workshop doc: timer_challenge.sh <station> [name] — Speed vs Accuracy.
# Times a single recorded attempt and prints the wall-clock duration.
set -euo pipefail
cd "$(dirname "$0")/.."
STATION="${1:?usage: timer_challenge.sh <station> [name]}"
NAME="${2:-speed_attempt}"
echo "Timed attempt on $STATION — drive the leader. Go!"
start=$(date +%s)
soarm-workshop --rig "$STATION" record \
  --dataset-name "$NAME" --episodes 1 --episode-time-s 15 --reset-time-s 3 --no-cameras
end=$(date +%s)
echo "Elapsed: $((end - start))s  (count drops/collisions/hits by hand)"
