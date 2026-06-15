#!/usr/bin/env bash
set -euo pipefail
source scripts/_load_env.sh
: "${HF_USER:?Set HF_USER in configs/arms.env or use dataset.push_to_hub=False manually}"
DATASET_NAME="${DATASET_NAME:-hs-so101-cube-sort}"
TASK_TEXT="${TASK_TEXT:-Pick up the red cube and place it in the left bin}"

lerobot-record \
  --robot.type=so101_follower \
  --robot.port="$FOLLOWER_PORT" \
  --robot.id="$FOLLOWER_ID" \
  --robot.cameras="$CAMERA_CONFIG" \
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
