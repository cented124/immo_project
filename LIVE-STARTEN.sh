#!/usr/bin/env bash
# Ubuntu 24.04 LTS VPS. Re-running preserves data, secrets and the first import.
set -euo pipefail
cd "$(dirname "$0")"
command -v docker >/dev/null || { echo 'Docker fehlt. Siehe docs/DEPLOYMENT.md.'; exit 1; }
command -v python3 >/dev/null || { echo 'Python 3 fehlt: sudo apt install python3'; exit 1; }
docker compose version >/dev/null
docker info >/dev/null
mkdir -p project
if [[ ! -f .env ]]; then
  suggested=$(python3 -c 'import json,pathlib; p=pathlib.Path("deployment.json"); print(json.loads(p.read_text()).get("domain", "") if p.exists() else "")')
  read -r -p "Deine Domain (ohne https://) [${suggested}]: " chosen_domain
  chosen_domain=${chosen_domain:-$suggested}
  python3 scripts/configure.py --origin "https://${chosen_domain}" --domain "$chosen_domain"
fi
docker compose -f compose.yaml -f compose.production.yaml config --quiet
echo 'Website und Admin werden gestartet. Der erste Build kann einige Minuten dauern.'
docker compose -f compose.yaml -f compose.production.yaml up -d --build --wait --wait-timeout 300
set +e
docker compose exec -T api python -m app.cli admin-exists
account_result=$?
set -e
if [[ "$account_result" == 10 ]]; then
  read -r -p 'E-Mail für deinen neuen Administrator: ' admin_email
  docker compose exec api python -m app.cli create-admin --email "$admin_email"
elif [[ "$account_result" != 0 ]]; then
  echo 'Adminprüfung fehlgeschlagen. Containerstatus prüfen.'
  exit 1
fi
python3 - <<'PY'
from pathlib import Path
values = dict(line.split('=', 1) for line in Path('.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
domain = values.get('DOMAIN', '')
if not domain:
    raise SystemExit('DOMAIN fehlt in .env. Anleitung: docs/DEPLOYMENT.md')
print(f'Website: https://{domain}\nAdmin: https://{domain}/admin')
print('DNS muss auf diesen VPS zeigen und TCP 80/443 erreichbar sein. Caddy beschafft dann automatisch das HTTPS-Zertifikat.')
print('Anschließend Anmeldung, Rechtstexte, Formulare und Backups prüfen. Integrationen bei Bedarf neu einrichten.')
PY
