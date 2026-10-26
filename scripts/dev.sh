#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/backend"
export NEXT_TELEMETRY_DISABLED=1
export DATA_DIR="${DATA_DIR:-$PWD/.local/data}"
.venv/bin/alembic -c backend/alembic.ini upgrade head
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT INT TERM
npm --prefix frontend run dev
