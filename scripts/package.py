"""Build the source distribution; never includes live configuration or data."""
import hashlib
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
from app.builder import add_sources

destination = root / "downloads"
destination.mkdir(exist_ok=True)
archive = destination / "Raumwerk-Windows.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
    add_sources(z, "Raumwerk/")
    count = len(z.namelist())
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(destination / "Raumwerk-Windows.sha256.txt").write_text(digest + "  Raumwerk-Windows.zip\n")
print(f"Windows-Paket erstellt: {count} Dateien, {archive.stat().st_size} Bytes. Prüfsumme gespeichert.")
