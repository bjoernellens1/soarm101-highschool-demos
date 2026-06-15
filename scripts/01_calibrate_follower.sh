#!/usr/bin/env bash
set -euo pipefail
source scripts/_load_env.sh
lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id="$FOLLOWER_ID"
