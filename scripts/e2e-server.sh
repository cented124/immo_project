#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .local
export DATA_DIR
DATA_DIR=$(mktemp -d "$PWD/.local/e2e-run-XXXXXX")
export DATABASE_URL="sqlite:///$DATA_DIR/app.db"
export PYTHONPATH="$PWD/backend"
export PUBLIC_ORIGIN=http://localhost:3001
export API_INTERNAL_URL=http://127.0.0.1:8001
export NEXT_DIST_DIR=.next-e2e
export NEXT_TELEMETRY_DISABLED=1
export DELIVERY_WORKER=0
mkdir -p "$DATA_DIR"
.venv/bin/alembic -c backend/alembic.ini upgrade head
.venv/bin/python - <<'PY'
from app.main import initialize
from app.db import Session,User
from app.security import hasher
from sqlalchemy import select
initialize()
with Session() as db:
    if not db.scalar(select(User).where(User.email=='browser@example.com')):
        db.add(User(email='browser@example.com',password=hasher.hash('browser-test-only-123'),role='admin'));db.commit()
PY
.venv/bin/uvicorn app.main:app --port 8001 --no-access-log &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT INT TERM
npm --prefix frontend run dev -- --port 3001
