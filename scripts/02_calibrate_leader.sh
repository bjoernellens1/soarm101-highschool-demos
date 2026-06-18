#!/usr/bin/env bash
set -euo pipefail
source scripts/_load_env.sh
lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port="$LEADER_PORT" \
  --teleop.id="$LEADER_ID" \
  --teleop.calibration_dir=.calibration
