#!/usr/bin/env bash
set -euo pipefail
source scripts/_load_env.sh
REPO_ID="${1:-${HF_USER:-your-hf-user}/${DATASET_NAME:-hs-so101-cube-sort}}"
EPISODE="${2:-0}"

lerobot-replay \
  --robot.type=so101_follower \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id="$FOLLOWER_ID" \
  --dataset.repo_id="$REPO_ID" \
  --dataset.episode="$EPISODE"
