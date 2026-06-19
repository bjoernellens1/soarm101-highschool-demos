#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# The API now serves the web UI itself at http://127.0.0.1:7860 (and /docs).
# Set SOARM_API_TOKEN (or SOARM_ALLOW_LOCALHOST_NO_AUTH=1 for local-only use).
exec soarm-api
