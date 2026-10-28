"""Stopped SQLite installation backups with checksums and staged restoration."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import sqlite3
import stat
import zipfile
from datetime import datetime, timezone

MAX_BYTES = 2 * 1024**3
MAX_FILES = 20000
MANIFEST = "raumwerk-backup.json"


def digest_file(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024**2), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    if not name or "\\" in name or path.is_absolute() or any(p in {"", ".", ".."} for p in name.split("/")):
        raise RuntimeError("Ungueltiger Dateipfad in der Sicherung.")
    if path.parts[0] != "DATEN" or len(path.parts) < 2:
        raise RuntimeError("Die Sicherung darf nur DATEN enthalten.")
    for part in path.parts:
        if any(ord(c) < 32 or c in ':<>"|?*' for c in part) or part.endswith((".", " ")) or re.match(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", part, re.I):
            raise RuntimeError("Ungueltiger Windows-Dateiname in der Sicherung.")
    return path


def validate_database(data):
    """Read-only checks before any existing installation is replaced."""
    database = data / "app.db"
    if not database.is_file():
        raise RuntimeError("Die Sicherung enthaelt keine lokale Datenbank.")
    from cryptography.fernet import Fernet
    try:
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
            if db.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                raise ValueError("integrity")
            # Reject unknown future schemas; older known schemas can migrate on start.
            if db.execute("SELECT version_num FROM alembic_version").fetchone()[0] not in {"0001", "0002", "0003"}:
                raise ValueError("schema")
            settings = {key: json.loads(value) for key, value in db.execute("SELECT key,value FROM settings")}
            if not all(isinstance(settings.get(key), dict) for key in ["draft", "published"]):
                raise ValueError("config")
            encrypted = [v["encrypted"] for k, v in settings.items() if k.startswith("integration_") and v.get("encrypted")]
            if encrypted or (data / "encryption.key").exists():
                cipher = Fernet((data / "encryption.key").read_bytes())
                for value in encrypted:
                    json.loads(cipher.decrypt(value.encode()))
            for (identity,) in db.execute("SELECT id FROM files"):
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", identity) or not (data / "files" / identity).is_file():
                    raise ValueError("media")
            for key, value in settings.items():
                if key.startswith("design_"):
                    identity = key.removeprefix("design_")
                    if not re.fullmatch(r"[a-z][a-z0-9-]{1,40}", identity):
                        raise ValueError("design")
                    for name, info in value.items():
                        rel = safe_name("DATEN/designs/" + identity + "/" + name)
                        path = data.joinpath(*rel.parts[1:])
                        if path.stat().st_size != info["size"] or digest_file(path) != info["sha256"]:
                            raise ValueError("design")
    except Exception as error:
        raise RuntimeError("Datenbank, Medien oder Verschluesselungsschluessel sind unvollstaendig oder inkompatibel. Bestehende Daten bleiben erhalten.") from error


def create_backup(data, folder, version, validate=True):
    if validate:
        validate_database(data)
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc)
    target = folder / (stamp.strftime("Raumwerk-%Y%m%d-%H%M%S-") + secrets.token_hex(3) + ".zip")
    temporary = target.with_suffix(".partial")
    files = {}
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(data.rglob("*")):
                if path.is_symlink():
                    raise RuntimeError("Verknuepfungen im Datenordner werden nicht gesichert.")
                if path.is_file():
                    name = "DATEN/" + path.relative_to(data).as_posix()
                    safe_name(name)
                    files[name] = {"size": path.stat().st_size, "sha256": digest_file(path)}
                    archive.write(path, name)
            archive.writestr(MANIFEST, json.dumps({"format": 1, "version": version, "database_checked": validate, "created": stamp.isoformat(), "files": files}, indent=2))
        os.replace(temporary, target)
        return target
    finally:
        temporary.unlink(missing_ok=True)


def stage_backup(archive_path, stage):
    """Bounded extraction, never ZipFile.extractall; supports old DATEN-only ZIPs."""
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_FILES or sum(i.file_size for i in entries) > MAX_BYTES:
                raise RuntimeError("Sicherung zu gross (maximal 2 GB / 20000 Dateien).")
            names = set()
            manifest = None
            for entry in entries:
                name = entry.filename.rstrip("/") if entry.is_dir() else entry.filename
                if name == MANIFEST:
                    if manifest is not None or entry.file_size > 8 * 1024**2:
                        raise RuntimeError("Ungueltiges Sicherungsmanifest.")
                    manifest = json.loads(archive.read(entry))
                    if not isinstance(manifest, dict) or manifest.get("format") != 1 or not isinstance(manifest.get("files"), dict):
                        raise RuntimeError("Unbekanntes Sicherungsformat.")
                    continue
                if name == "DATEN" and entry.is_dir():
                    continue
                safe_name(name)
                if name.casefold() in names or stat.S_IFMT(entry.external_attr >> 16) == stat.S_IFLNK or entry.flag_bits & 1:
                    raise RuntimeError("Doppelte, verschluesselte oder verknuepfte Datei in der Sicherung.")
                names.add(name.casefold())
            if shutil.disk_usage(stage.parent).free < sum(i.file_size for i in entries) + 128 * 1024**2:
                raise RuntimeError("Zu wenig freier Speicher fuer die Wiederherstellung.")
            expected = manifest["files"] if manifest else None
            actual = {}
            for entry in entries:
                if entry.is_dir() or entry.filename == MANIFEST:
                    continue
                rel = safe_name(entry.filename)
                target = stage.joinpath(*rel.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                h = hashlib.sha256()
                size = 0
                with archive.open(entry) as source, target.open("xb") as out:
                    while chunk := source.read(1024**2):
                        size += len(chunk)
                        if size > entry.file_size:
                            raise RuntimeError("Dateigroesse stimmt nicht.")
                        h.update(chunk)
                        out.write(chunk)
                actual[entry.filename] = {"size": size, "sha256": h.hexdigest()}
            if expected is not None and expected != actual:
                raise RuntimeError("Pruefsummen stimmen nicht. Sicherung wurde nicht uebernommen.")
        validate_database(stage / "DATEN")
        return manifest or {"format": 0, "version": "aeltere Version"}
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        raise RuntimeError("Sicherung konnte nicht vollstaendig geprueft werden. Bestehende Daten bleiben erhalten.") from error


def prepare_restored_database(data):
    # Restoring must not revive old sessions or automatically resend jobs from a snapshot.
    with sqlite3.connect(data / "app.db") as db:
        db.execute("DELETE FROM sessions")
        if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deliveries'").fetchone():
            db.execute("UPDATE deliveries SET status='failed', error='Nach Wiederherstellung pausiert. Zustellung vor manueller Wiederaufnahme pruefen.' WHERE status IN ('pending','retry')")
        db.commit()


def replace_data(data, staged):
    previous = staged.parent / ("previous-DATEN-" + secrets.token_hex(8))
    moved = False
    try:
        if data.exists():
            data.rename(previous)
            moved = True
        staged.rename(data)
    except OSError:
        if moved:
            previous.rename(data)
        raise RuntimeError("Wiederherstellung blockiert. Der bisherige Datenordner wurde zurueckgesetzt.")
    if moved:
        shutil.rmtree(previous, ignore_errors=True)
