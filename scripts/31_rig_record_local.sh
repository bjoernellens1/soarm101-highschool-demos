#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
RIG_NAME="${1:-${RIG:-rig01}}"
EPISODES="${EPISODES:-5}"
EPISODE_TIME_S="${EPISODE_TIME_S:-20}"
RESET_TIME_S="${RESET_TIME_S:-10}"
HF_USER="${HF_USER:-local}"
soarm-workshop --rig "$RIG_NAME" record \
  --hf-user "$HF_USER" \
  --episodes "$EPISODES" \
  --episode-time-s "$EPISODE_TIME_S" \
  --reset-time-s "$RESET_TIME_S"
