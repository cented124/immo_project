"""Generate deployment secrets once, without printing them or replacing user config."""

import argparse, base64, os, secrets
from pathlib import Path
from urllib.parse import urlsplit
import re

parser = argparse.ArgumentParser()
parser.add_argument("--origin", default="http://localhost:3000")
parser.add_argument("--domain", default="")
args = parser.parse_args()
origin = urlsplit(args.origin)
try:
    origin_port = origin.port
except ValueError:
    raise SystemExit("Invalid origin port.")
if any(c in args.origin for c in "\r\n\t ") or origin.username or origin.password or origin.path not in {"", "/"} or origin.query or origin.fragment or not origin.hostname:
    raise SystemExit("Supply one valid origin without path, userinfo or whitespace.")
if not (origin.scheme == "https" or (origin.scheme == "http" and origin.hostname in {"localhost", "127.0.0.1"})):
    raise SystemExit("For a public host, supply an HTTPS origin.")
if args.domain:
    args.domain = args.domain.strip().lower().encode("idna").decode("ascii")
    if not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", args.domain) or len(args.domain) > 253 or origin.hostname.encode("idna").decode("ascii") != args.domain or origin.scheme != "https" or origin_port not in {None, 443}:
        raise SystemExit("Domain must be a valid hostname matching the origin.")
    args.origin = f"https://{args.domain}"
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
if args.domain:
    content += f"DOMAIN={args.domain}\n"
try:
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    raise SystemExit(".env already exists; preserved unchanged.")
with os.fdopen(fd, "w") as file:
    file.write(content)
print(".env created with independent random secrets. Never commit it.")
