"""Release operations across authentication, indexing and recoverable local data."""

import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import zipfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db import Session, Setting, DATA, engine
from app.cli import reset_admin_password
from app.security import key_material
from test_workflows import config, publish, prop, inquiry

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from desktop_backup import create_backup, stage_backup, replace_data


def test_operating_checks_are_private_and_do_not_expose_secrets(admin, monkeypatch):
    monkeypatch.setenv("PUBLIC_ORIGIN", "https://firma.example")
    monkeypatch.delenv("RAUMWERK_DESKTOP", raising=False)
    admin.put("/api/admin/integrations/telegram", json={"token": "secret-release-token", "chat_id": "secret-group"})
    result = admin.get("/api/admin/system")
    assert result.status_code == 200
    data = result.json()
    assert data["mode"] == "server" and data["version"] == "1.0.0"
    assert not data["ready"]  # tests intentionally have no running delivery worker
    assert "secret-release-token" not in result.text and str(DATA) not in result.text
    with TestClient(app) as visitor:
        assert visitor.get("/api/admin/system").status_code == 401
        visitor.headers["X-Requested-With"] = "Raumwerk"
        visitor.post("/api/admin/login", json={"email": "staff@example.com", "password": "test-password-1234"})
        assert visitor.get("/api/admin/system").status_code == 403


def test_live_index_follows_publication_withdrawal_and_modules(admin, monkeypatch):
    monkeypatch.setenv("PUBLIC_ORIGIN", "https://firma.example")
    monkeypatch.delenv("RAUMWERK_DESKTOP", raising=False)
    row = prop(admin, "published")
    path = "/immobilien/" + row["slug"]
    index = admin.get("/api/public/search-index").json()
    assert not index["local"] and path in index["paths"] and "/admin" not in index["paths"]
    row["status"] = "archived"
    assert admin.put("/api/admin/properties/" + str(row["id"]), json=row).status_code == 200
    assert path not in admin.get("/api/public/search-index").json()["paths"]
    c = config(admin)
    c["modules"]["properties"] = False
    c["pages"][0]["enabled"] = False
    publish(admin, c)
    index = admin.get("/api/public/search-index").json()
    assert "/immobilien" not in index["paths"] and "/" + c["pages"][0]["slug"] not in index["paths"]
    monkeypatch.setenv("PUBLIC_ORIGIN", "http://127.0.0.1:3456")
    assert admin.get("/api/public/search-index").json()["local"]


def test_logout_others_and_shell_recovery_revoke_sessions(admin):
    with TestClient(app) as second:
        second.headers["X-Requested-With"] = "Raumwerk"
        second.post("/api/admin/login", json={"email": "admin@example.com", "password": "test-password-1234"})
        assert admin.post("/api/admin/account/logout-others").json()["revoked"] == 1
        assert second.get("/api/admin/me").status_code == 401
    assert admin.get("/api/admin/me").status_code == 200
    with pytest.raises(ValueError):
        reset_admin_password("staff@example.com", "new-safe-password-123")
    reset_admin_password("admin@example.com", "new-safe-password-123")
    assert admin.get("/api/admin/me").status_code == 401
    assert admin.post("/api/admin/login", json={"email": "admin@example.com", "password": "test-password-1234"}).status_code == 401
    assert admin.post("/api/admin/login", json={"email": "admin@example.com", "password": "new-safe-password-123"}).status_code == 200
    assert admin.get("/api/docs").status_code == 404


def snapshot(target):
    target.mkdir()
    # SQLite online backup is used only to prepare an isolated fixture, not production restore.
    with sqlite3.connect(str(DATA / "test.db")) as source, sqlite3.connect(str(target / "app.db")) as dest:
        source.backup(dest)
    key_material()
    shutil.copyfile(DATA / "encryption.key", target / "encryption.key")
    if (DATA / "files").is_dir():
        shutil.copytree(DATA / "files", target / "files")
    if (DATA / "designs").is_dir():
        shutil.copytree(DATA / "designs", target / "designs")


def test_backup_restore_retains_company_property_inquiries_and_encryption(admin, tmp_path):
    if engine.dialect.name != "sqlite":
        pytest.skip("Native backups intentionally use SQLite")
    from app.delivery import integration
    from test_frontend_packages import bundle, archive, upload
    manifest, files = bundle("backup-release-design")
    assert upload(admin, archive(manifest, files)).status_code == 201
    prop(admin)
    inquiry(admin)
    admin.put("/api/admin/integrations/telegram", json={"token": "backup-only-secret", "chat_id": "synthetic"})
    data = tmp_path / "DATEN"
    snapshot(data)
    target = create_backup(data, tmp_path / "backups", "1.0.0")
    stage = tmp_path / "staging"
    stage.mkdir()
    assert stage_backup(target, stage)["version"] == "1.0.0"
    with sqlite3.connect(data / "app.db") as db:
        db.execute("DELETE FROM inquiries")
        db.commit()
    replace_data(data, stage / "DATEN")
    assert (data / "designs/backup-release-design/app.js").read_bytes() == files["app.js"]
    with sqlite3.connect(data / "app.db") as db:
        assert db.execute("SELECT count(*) FROM inquiries").fetchone()[0] == 1
        assert db.execute("SELECT count(*) FROM properties").fetchone()[0] == 1
        value = json.loads(db.execute("SELECT value FROM settings WHERE key='integration_telegram'").fetchone()[0])
    from cryptography.fernet import Fernet
    assert json.loads(Fernet((data / "encryption.key").read_bytes()).decrypt(value["encrypted"].encode()))["token"] == "backup-only-secret"


def test_backup_rejects_tampering_and_does_not_touch_current_data(admin, tmp_path):
    if engine.dialect.name != "sqlite":
        pytest.skip("Native backups intentionally use SQLite")
    prop(admin)
    data = tmp_path / "DATEN"
    snapshot(data)
    target = create_backup(data, tmp_path / "backups", "1.0.0")
    with zipfile.ZipFile(target) as original:
        entries = {i.filename: original.read(i) for i in original.infolist()}
    with zipfile.ZipFile(tmp_path / "tampered.zip", "w") as archive:
        for name, raw in entries.items():
            archive.writestr(name, raw + b"modified" if name.endswith("encryption.key") else raw)
    stage = tmp_path / "staging"
    stage.mkdir()
    before = (data / "app.db").read_bytes()
    with pytest.raises(RuntimeError):
        stage_backup(tmp_path / "tampered.zip", stage)
    assert (data / "app.db").read_bytes() == before
    # Legacy DATEN-only archives remain importable after full database/media checks.
    with zipfile.ZipFile(tmp_path / "legacy.zip", "w") as archive:
        for name, raw in entries.items():
            if name != "raumwerk-backup.json":
                archive.writestr(name, raw)
    stage2 = tmp_path / "legacy-stage"
    stage2.mkdir()
    assert stage_backup(tmp_path / "legacy.zip", stage2)["format"] == 0


@pytest.mark.parametrize("names", [["DATEN/../../outside"], ["DATEN/CON.txt"], ["DATEN/a", "DATEN/A"], ["DATEN\\a"], ["other/app.db"]])
def test_hostile_backup_paths_fail_without_extraction(tmp_path, names):
    archive = tmp_path / "hostile.zip"
    with zipfile.ZipFile(archive, "w") as out:
        for name in names:
            out.writestr(name, "fake")
    stage = tmp_path / "stage"
    stage.mkdir()
    with pytest.raises(RuntimeError):
        stage_backup(archive, stage)
    assert list(stage.iterdir()) == []
