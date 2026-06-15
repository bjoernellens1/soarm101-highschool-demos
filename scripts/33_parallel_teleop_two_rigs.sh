#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
LEFT_RIG="${1:-rig01}"
RIGHT_RIG="${2:-rig02}"

mkdir -p logs
soarm-workshop --rig "$LEFT_RIG" teleop >"logs/${LEFT_RIG}_teleop.log" 2>&1 &
left_pid=$!
soarm-workshop --rig "$RIGHT_RIG" teleop >"logs/${RIGHT_RIG}_teleop.log" 2>&1 &
right_pid=$!

echo "Started $LEFT_RIG teleop PID=$left_pid"
echo "Started $RIGHT_RIG teleop PID=$right_pid"
echo "Press Ctrl+C to stop both."
trap 'kill "$left_pid" "$right_pid" 2>/dev/null || true; wait || true' INT TERM EXIT
wait
