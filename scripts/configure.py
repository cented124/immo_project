"""Generate deployment secrets once, without printing them or replacing user config."""

import argparse, base64, os, secrets
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--origin", default="http://localhost:3000")
args = parser.parse_args()
if not args.origin.startswith(("https://", "http://localhost:", "http://127.0.0.1:")):
    raise SystemExit("For a public host, supply an HTTPS origin.")
target = Path(__file__).resolve().parents[1] / ".env"
password = secrets.token_urlsafe(32)
content = f"""POSTGRES_PASSWORD={password}
DATABASE_URL=postgresql+psycopg://raumwerk:{password}@db:5432/raumwerk
ENCRYPTION_KEY={base64.urlsafe_b64encode(os.urandom(32)).decode()}
DATA_DIR=/data
PUBLIC_ORIGIN={args.origin.rstrip("/")}
COOKIE_SECURE={1 if args.origin.startswith("https://") else 0}
API_INTERNAL_URL=http://api:8000
DELIVERY_WORKER=1
"""
try:
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    raise SystemExit(".env already exists; preserved unchanged.")
with os.fdopen(fd, "w") as file:
    file.write(content)
print(".env created with independent random secrets. Never commit it.")
