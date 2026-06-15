#!/usr/bin/env bash
set -euo pipefail
source scripts/_load_env.sh

# display_data=true gives a lightweight live view through LeRobot/Rerun.
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id="$FOLLOWER_ID" \
  --robot.cameras="$CAMERA_CONFIG" \
  --teleop.type=so101_leader \
  --teleop.port="$LEADER_PORT" \
  --teleop.id="$LEADER_ID" \
  --display_data=true
