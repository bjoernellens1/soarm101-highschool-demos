#!/usr/bin/env bash
# Workshop doc: record_episode.sh <station> <name> — record one named episode.
set -euo pipefail
cd "$(dirname "$0")/.."
STATION="${1:?usage: record_episode.sh <station> <name>}"
NAME="${2:?usage: record_episode.sh <station> <name>}"
exec soarm-workshop --rig "$STATION" record \
  --dataset-name "$NAME" --episodes 1 --episode-time-s 20 --reset-time-s 5 --no-cameras
