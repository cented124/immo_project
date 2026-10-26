#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install --cache-dir /tmp/raumwerk-pip-cache -r backend/requirements.txt
npm --prefix frontend --cache /tmp/raumwerk-npm-cache ci --no-audit --no-fund
.venv/bin/alembic -c backend/alembic.ini upgrade head
printf '\nDependencies and database are ready. See README.md to create the first administrator.\n'
