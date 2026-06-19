#!/usr/bin/env bash
# Workshop doc: replay_all.sh <demo> — Robot Orchestra. Replay one dataset on
# every configured station's follower (near-)synchronously.
set -euo pipefail
cd "$(dirname "$0")/.."
DEMO="${1:?usage: replay_all.sh <demo_name>}"
REPO="$DEMO"
[[ "$DEMO" == */* ]] || REPO="local/$DEMO"
exec soarm-workshop orchestra "$REPO"
