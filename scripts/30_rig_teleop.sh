#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
RIG_NAME="${1:-${RIG:-rig01}}"
soarm-workshop --rig "$RIG_NAME" teleop
