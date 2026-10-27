"""Build a Windows-ready ZIP from a tested Windows installation, without any data."""
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.builder import add_sources

if os.name != "nt":
    raise SystemExit("A Windows runtime must be built and tested on Windows.")
runtime = ROOT / ".runtime"
if (runtime / "control/state.json").exists():
    raise SystemExit("Stop the desktop application before packaging.")
webs = [p for p in runtime.glob("web-*") if (p / "desktop-ready.json").is_file()]
if not webs:
    raise SystemExit("No tested frontend build found.")
web = max(webs, key=lambda p: p.stat().st_mtime)
for directory in [runtime / "python", runtime / "node", web]:
    if not directory.is_dir():
        raise SystemExit("Runtime incomplete")
target = ROOT / "dist/Raumwerk-Windows-ohne-Docker.zip"
target.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    add_sources(archive, "Raumwerk/")
    for directory in [runtime / "python", runtime / "node", web]:
        for path in directory.rglob("*"):
            if not path.is_file() or path.is_symlink() or "__pycache__" in path.parts:
                continue
            archive.write(path, "Raumwerk/" + path.relative_to(ROOT).as_posix())
    names = archive.namelist()
    assert not any(n.startswith(("Raumwerk/DATEN/", "Raumwerk/.runtime/control/", "Raumwerk/.runtime/logs/")) or n.endswith("/.env") for n in names)
digest = hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix(".sha256.txt").write_text(digest + "  " + target.name + "\n", encoding="utf-8")
print(json.dumps({"file": target.name, "bytes": target.stat().st_size, "sha256": digest}))
