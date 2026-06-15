#!/usr/bin/env bash
set -euo pipefail
ENV_FILE="${ENV_FILE:-configs/arms.env}"
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
else
  echo "Missing $ENV_FILE. Copy configs/arms.env.example to configs/arms.env first." >&2
  exit 1
fi
: "${FOLLOWER_PORT:?Set FOLLOWER_PORT in configs/arms.env}"
: "${LEADER_PORT:?Set LEADER_PORT in configs/arms.env}"
: "${FOLLOWER_ID:?Set FOLLOWER_ID in configs/arms.env}"
: "${LEADER_ID:?Set LEADER_ID in configs/arms.env}"
