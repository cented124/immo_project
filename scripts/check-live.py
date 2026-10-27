"""Read-only HTTPS reachability check. No credentials and no message sending."""
import argparse
import json
import re
import urllib.request
import urllib.error

parser = argparse.ArgumentParser()
parser.add_argument("--domain", required=True)
args = parser.parse_args()
domain = args.domain.strip().lower().encode("idna").decode("ascii")
if not re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", domain) or len(domain) > 253:
    raise SystemExit("Bitte nur den Domainnamen ohne https:// oder Pfad angeben.")
failed = False
for route in ["/", "/admin", "/api/health"]:
    try:
        with urllib.request.urlopen("https://" + domain + route, timeout=15) as response:
            if response.status != 200:
                raise ValueError()
            if route == "/api/health" and json.load(response).get("status") != "ok":
                raise ValueError()
        print("OK:", route)
    except (urllib.error.URLError, ValueError, TimeoutError, OSError):
        failed = True
        print("Nicht bestätigt:", route, "– DNS, HTTPS, Firewall und Containerstatus prüfen.")
raise SystemExit(1 if failed else 0)
