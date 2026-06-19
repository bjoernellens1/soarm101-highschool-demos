#!/usr/bin/env bash
# Workshop doc: replay_episode.sh <station> <name> — replay a named local episode.
set -euo pipefail
cd "$(dirname "$0")/.."
STATION="${1:?usage: replay_episode.sh <station> <name>}"
NAME="${2:?usage: replay_episode.sh <station> <name>}"
# Local datasets are stored under the "local/" namespace by record_episode.sh.
REPO="$NAME"
[[ "$NAME" == */* ]] || REPO="local/$NAME"
exec soarm-workshop --rig "$STATION" replay "$REPO"
