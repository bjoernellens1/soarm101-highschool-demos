#!/usr/bin/env bash
set -euo pipefail
source scripts/_load_env.sh
: "${HF_USER:?Set HF_USER in configs/arms.env or use dataset.push_to_hub=False manually}"
DATASET_NAME="${DATASET_NAME:-hs-so101-cube-sort}"
TASK_TEXT="${TASK_TEXT:-Pick up the red cube and place it in the left bin}"

CAMERA_ARGS=()
if python -c 'import cv2; cap=cv2.VideoCapture(0); cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640); exit(0 if cap.get(cv2.CAP_PROP_FRAME_WIDTH) > 0 else 1)' 2>/dev/null; then
  CAMERA_ARGS=("--robot.cameras=$CAMERA_CONFIG")
else
  echo "Warning: OpenCV cannot initialize camera 0, running without cameras."
fi

lerobot-record \
  --robot.type=so101_follower \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id="$FOLLOWER_ID" \
  "${CAMERA_ARGS[@]}" \
  --teleop.type=so101_leader \
  --teleop.port="$LEADER_PORT" \
  --teleop.id="$LEADER_ID" \
  --display_data=true \
  --dataset.repo_id="${HF_USER}/${DATASET_NAME}" \
  --dataset.num_episodes=5 \
  --dataset.episode_time_s=20 \
  --dataset.reset_time_s=10 \
  --dataset.single_task="$TASK_TEXT" \
  --dataset.streaming_encoding=true \
  --dataset.encoder_threads=2
