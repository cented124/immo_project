"""Complete browser bundles: actual files, draft isolation, export and hostile ZIPs."""

import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import pytest
from app.db import DATA, Session, Setting
from app.frontend_packages import parse_package, preview_token, valid_preview
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]


def bundle(identity="custom-package", **changes):
    manifest = {
        "id": identity,
        "name": "Eigenes vollständiges Frontend",
        "version": 3,
        "adapter": "atelier",
        "entry": "index.html",
        "pages": ["home", "properties", "property", "contact", "disclosure", "content"],
        "actions": ["search", "inquiry", "download", "return"],
        **changes,
    }
    return manifest, {
        "index.html": b'<!doctype html><html><head></head><body><h1>Frei gestaltet</h1><script src="app.js"></script></body></html>',
        "app.js": b"window.Raumwerk.ready().then(console.log)",
        "app.css": b"body {color:navy}",
    }


def archive(manifest, files, prefix=""):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(prefix + "manifest.json", json.dumps(manifest))
        for name, raw in files.items():
            z.writestr(prefix + name, raw)
    return out.getvalue()


def upload(admin, data, action="import"):
    return admin.post(
        "/api/admin/builder/design/" + action,
        files={"file": ("frontend.zip", data, "application/zip")},
    )


def test_complete_site_is_private_until_published_and_preview_is_capability_scoped(
    admin,
):
    manifest, files = bundle()
    data = archive(manifest, files)
    before = admin.get("/api/public/config").json()
    report = upload(admin, data, "validate")
    assert report.status_code == 200 and report.json()["files"] == 3
    assert not (DATA / "designs/custom-package").exists()
    result = upload(admin, data)
    assert result.status_code == 201, result.text
    draft = result.json()["config"]
    assert draft["company"] == before["company"]
    assert admin.get("/api/public/config").json() == before
    assert (
        admin.get("/api/public/frontend/custom-package/index.html").status_code == 404
    )
    entry = draft["frontend_package"]["entry"]
    response = admin.get(entry)
    assert response.status_code == 200 and "frontend-sdk.js" in response.text
    csp = response.headers["content-security-policy"]
    assert (
        "sandbox allow-scripts" in csp
        and "allow-same-origin" not in csp
        and "connect-src 'none'" in csp
    )
    assert (
        admin.get(entry.replace("custom-package", "other-package")).status_code == 404
    )
    assert (
        admin.get(entry.replace("frontend-preview/", "frontend-preview/0-")).status_code
        == 404
    )
    assert (
        admin.get(draft["frontend_package"]["base"] + "app.js").content
        == files["app.js"]
    )
    assert (
        admin.get(draft["frontend_package"]["base"] + "missing.js").status_code == 404
    )
    assert admin.post("/api/admin/config/publish").status_code == 200
    assert (
        admin.get("/api/public/frontend/custom-package/app.js").content
        == files["app.js"]
    )
    assert upload(admin, data).status_code == 409
    # A classic manifest endpoint cannot register a broken complete frontend.
    assert (
        admin.post(
            "/api/admin/templates/import", json={**manifest, "id": "broken-custom"}
        ).status_code
        == 422
    )


def test_actual_ready_example_contains_images_fonts_and_loads_as_complete_package(
    admin,
):
    data = admin.get("/api/admin/builder/example").content
    parsed = parse_package(data, "example.zip")
    assert parsed.manifest.version == 3
    assert any(p.endswith(".woff2") for p in parsed.files)
    assert parsed.manifest.assets["hero_image"] in parsed.files
    result = upload(admin, data)
    assert result.status_code == 201, result.text
    c = result.json()["config"]
    assert c["hero_image"].startswith("/api/public/frontend/")
    assert admin.get("/api/admin/builder/check").json()["valid"]
    assert admin.put("/api/admin/config", json=c).status_code == 200
    assert admin.post("/api/admin/config/publish").status_code == 200
    assert (
        admin.get(c["hero_image"]).content
        == parsed.files[parsed.manifest.assets["hero_image"]]
    )


def test_supported_wrapped_zip_and_rejection_of_sources_paths_duplicates_and_missing_assets():
    m, files = bundle()
    assert (
        parse_package(archive(m, files, "my-design/"), "a.zip").manifest.id == m["id"]
    )
    for changes in [
        {"../escape.js": b"bad"},
        {"A.js": b"1", "a.js": b"2"},
        {"CON.js": b"1"},
        {"source.tsx": b"code"},
        {"bad.js": b"\xff"},
        {"dir.js": b"1", "dir.js/x.js": b"1"},
    ]:
        with pytest.raises(HTTPException) as e:
            parse_package(archive(m, {**files, **changes}), "a.zip")
        assert e.value.status_code == 422
    with pytest.raises(HTTPException):
        parse_package(json.dumps(m).encode(), "manifest.json")
    with pytest.raises(HTTPException):
        parse_package(archive({**m, "assets": {"logo": "missing.png"}}, files), "a.zip")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("manifest.json", json.dumps(m))
        info = zipfile.ZipInfo("index.html")
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        z.writestr(info, "/etc/passwd")
    with pytest.raises(HTTPException):
        parse_package(out.getvalue(), "a.zip")


def test_failed_database_transaction_does_not_leave_installed_files(admin, monkeypatch):
    import app.main as main

    m, files = bundle("failed-package")

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(main, "add_revision", fail)
    with pytest.raises(RuntimeError):
        upload(admin, archive(m, files))
    assert not (DATA / "designs/failed-package").exists()
    with Session() as db:
        assert db.get(Setting, "design_failed-package") is None
        assert db.get(Setting, "template_failed-package") is None


def test_preview_expiry_and_identity_do_not_accept_modified_capabilities(monkeypatch):
    import app.frontend_packages as package

    monkeypatch.setattr(package.time, "time", lambda: 1000000)
    token = preview_token("my-frontend")
    assert valid_preview("my-frontend", token)
    assert not valid_preview("another-frontend", token)
    monkeypatch.setattr(package.time, "time", lambda: 1001000)
    assert not valid_preview("my-frontend", token)


def test_custom_bundle_survives_project_export_and_fresh_seed_import(admin, tmp_path):
    m, files = bundle("exported-package")
    assert upload(admin, archive(m, files)).status_code == 201
    assert admin.post("/api/admin/config/publish").status_code == 200
    exported = admin.post("/api/admin/builder/project", json={"domain": ""})
    assert exported.status_code == 200, exported.text
    with zipfile.ZipFile(io.BytesIO(exported.content)) as z:
        seed = json.loads(z.read("Raumwerk/project/project.json"))
        assert (
            seed["designs"][m["id"]]["app.js"]["sha256"]
            == hashlib.sha256(files["app.js"]).hexdigest()
        )
        assert (
            z.read("Raumwerk/project/designs/" + m["id"] + "/app.js") == files["app.js"]
        )
        z.extractall(tmp_path)
    script = """
import os,sys
from pathlib import Path
root=Path(sys.argv[1]); folder=Path(sys.argv[2]); data=folder/'db'
os.environ.update(DATA_DIR=str(data),DATABASE_URL='sqlite:///'+str(data/'app.db'),DELIVERY_WORKER='0')
sys.path.insert(0,str(root/'backend'))
from alembic import command
from alembic.config import Config
command.upgrade(Config(str(root/'backend/alembic.ini')),'head')
from app.project import import_project
from app.db import Session,Setting,engine
assert import_project(folder/'Raumwerk/project/project.json')
with Session() as db:
 assert db.get(Setting,'design_exported-package').value['app.js']['size']>0
assert (data/'designs/exported-package/app.js').is_file()
assert not import_project(folder/'Raumwerk/project/project.json')
engine.dispose()
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(ROOT), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_changed_package_file_blocks_publication_and_is_reported(admin):
    m, files = bundle("tampered-package")
    assert upload(admin, archive(m, files)).status_code == 201
    (DATA / "designs/tampered-package/app.js").write_bytes(b"changed")
    report = admin.get("/api/admin/builder/check").json()
    assert not report["valid"]
    assert any(x["id"] == "package" and not x["ok"] for x in report["checks"])
    assert admin.post("/api/admin/config/publish").status_code == 422


def test_missing_scripts_and_css_assets_are_rejected_before_installation():
    m, files = bundle()
    for broken in [
        {**files, "index.html": b'<script src="missing.js"></script>'},
        {**files, "index.html": b'<script src="https://example.com/cdn.js"></script>'},
        {**files, "app.css": b"body {background:url(missing.png)}"},
    ]:
        with pytest.raises(HTTPException) as error:
            parse_package(archive(m, broken), "frontend.zip")
        assert error.value.status_code == 422
