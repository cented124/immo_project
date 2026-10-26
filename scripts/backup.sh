#!/usr/bin/env bash
set -euo pipefail
umask 077
cd "$(dirname "$0")/.."
command -v gpg >/dev/null || { echo 'Install GnuPG first.' >&2; exit 1; }
destination="${1:?Usage: bash scripts/backup.sh /secure/path/backup.tar.gpg}"
temporary=$(mktemp -d)
trap 'rm -rf "$temporary"' EXIT
# A maintenance window prevents an inconsistent database/file snapshot.
docker compose stop web api
trap 'docker compose start api web >/dev/null; rm -rf "$temporary"' EXIT
docker compose exec -T db pg_dump -U raumwerk -Fc raumwerk > "$temporary/database.dump"
docker compose cp api:/data "$temporary/files"
cp .env "$temporary/environment.env"
gpg_options=()
if [[ -n "${BACKUP_PASSPHRASE_FILE:-}" ]]; then
  [[ -r "$BACKUP_PASSPHRASE_FILE" ]] || { echo 'Passphrase file is not readable.' >&2; exit 1; }
  gpg_options=(--batch --pinentry-mode loopback --passphrase-file "$BACKUP_PASSPHRASE_FILE")
fi
tar -C "$temporary" -cf - database.dump files environment.env | gpg "${gpg_options[@]}" --symmetric --cipher-algo AES256 --output "$destination"
echo 'Encrypted backup created. Store its passphrase separately and perform a restore drill.'
