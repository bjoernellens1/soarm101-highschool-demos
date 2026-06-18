#!/usr/bin/env bash
set -euo pipefail
source scripts/_load_env.sh

# display_data=true gives a lightweight live view through LeRobot/Rerun.
CAMERA_ARGS=()
if python -c 'import cv2; cap=cv2.VideoCapture(0); cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640); exit(0 if cap.get(cv2.CAP_PROP_FRAME_WIDTH) > 0 else 1)' 2>/dev/null; then
  CAMERA_ARGS=("--robot.cameras=$CAMERA_CONFIG")
else
  echo "Warning: OpenCV cannot initialize camera 0, running without cameras."
fi

lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id="$FOLLOWER_ID" \
  "${CAMERA_ARGS[@]}" \
  --teleop.type=so101_leader \
  --teleop.port="$LEADER_PORT" \
  --teleop.id="$LEADER_ID" \
  --display_data=true
