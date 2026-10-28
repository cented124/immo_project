"""Publish a fixed source snapshot in its own GitHub folder, without runtime/data."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.builder import add_sources
from app.version import VERSION

folder = ROOT / "fertige-version" / VERSION
folder.mkdir(parents=True, exist_ok=True)
target = folder / f"Raumwerk-{VERSION}-Quellpaket.zip"
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
    add_sources(archive, "Raumwerk/")
    names = archive.namelist()
    if any(name.startswith(("Raumwerk/DATEN/", "Raumwerk/.local/", "Raumwerk/.runtime/", "Raumwerk/SICHERUNGEN/")) or name.endswith(("/.env", "/app.db", "/encryption.key")) for name in names):
        raise RuntimeError("Source export unexpectedly contains private data")
digest = hashlib.sha256(target.read_bytes()).hexdigest()
(folder / "SHA256SUMS.txt").write_text(digest + "  " + target.name + "\n", encoding="utf-8")
(folder / "versionsinfo.json").write_text(json.dumps({"product": "Raumwerk", "version": VERSION, "source_package": target.name, "sha256": digest, "files": len(names), "windows_ready": f"https://github.com/cented124/immo_project/releases/download/v{VERSION}/Raumwerk-Windows-ohne-Docker.zip", "development": "https://github.com/cented124/immo_project/tree/entwicklung"}, indent=2) + "\n", encoding="utf-8")
print(f"Version {VERSION}: {len(names)} source files, {target.stat().st_size} bytes; no user data.")
