import io
import json
import os
import subprocess
import sys
import zipfile
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.db import DATA
from app.builder import example_manifest
from test_workflows import config, publish, prop, upload, inquiry


def design(client, manifest, endpoint="validate"):
    return client.post(
        "/api/admin/builder/design/" + endpoint,
        files={"file": ("manifest.json", json.dumps(manifest), "application/json")},
    )


def test_company_profile_prompt_and_complete_reference_do_not_export_operational_secrets(
    admin,
):
    c = config(admin)
    c.update(
        company="Beispielverwaltung GmbH",
        address="Musterweg 12",
        email="info@example.com",
    )
    c["legal"].update(
        legal_form="GmbH",
        representative="Testperson",
        postcode="20095",
        register_court="Amtsgericht Musterstadt",
        register_number="HRB TEST123",
        vat_id="DE123456789",
    )
    c["frontend_brief"]["wishes"] = "Helle Oberflächen und geteiltes Titelbild"
    assert admin.put("/api/admin/config", json=c).status_code == 200
    secret = "test-secret-" + uuid.uuid4().hex
    assert (
        admin.put(
            "/api/admin/integrations/telegram",
            json={"token": secret, "chat_id": "private-destination"},
        ).status_code
        == 200
    )
    text = admin.get("/api/admin/builder/prompt").json()["prompt"]
    assert all(
        v in text
        for v in [
            "Beispielverwaltung",
            "HRB TEST123",
            "DE123456789",
            "Idempotency-Key",
            "return_code",
            "Helle Oberflächen",
        ]
    )
    assert secret not in text
    imprint = admin.get("/api/admin/builder/imprint").json()["text"]
    assert "HRB TEST123" in imprint and "Vertreten durch: Testperson" in imprint
    with zipfile.ZipFile(
        io.BytesIO(admin.get("/api/admin/builder/reference").content)
    ) as z:
        names = z.namelist()
        assert all(
            n in names
            for n in [
                "PROMPT.md",
                "CONTRACT.md",
                "schemas/manifest.schema.json",
                "schemas/openapi.json",
                "reference/frontend/components/Website.tsx",
                "reference/frontend/package-lock.json",
                "reference/backend/app/main.py",
                "reference/compose.production.yaml",
            ]
        )
        assert not any(
            ".env" in n
            and not n.endswith(".env.example")
            or "/node_modules/" in n
            or "/.local/" in n
            for n in names
        )
        assert all(secret.encode() not in z.read(n) for n in names)
        manifest = json.loads(z.read("manifest.json"))
        assert manifest["version"] == 2 and manifest["theme"]["hero_layout"] == "cover"


def test_design_roundtrip_preview_publish_and_malicious_packages(admin):
    c = config(admin)
    m = example_manifest(c)
    m["theme"].update(hero_layout="split", radius=14, primary="#226655")
    assert design(admin, {**m, "script": "alert(1)"}).status_code == 422
    invalid = {**m, "theme": {**m["theme"], "background": "url(https://example.com)"}}
    assert design(admin, invalid).status_code == 422
    assert design(admin, {**m, "pages": ["home"]}).status_code == 422
    assert design(admin, m).json()["available"] is True
    before = admin.get("/api/public/config").json()
    r = design(admin, m, "import")
    assert r.status_code == 201, r.text
    assert r.json()["config"]["frontend_theme"]["radius"] == 14
    assert config(admin)["primary"] == "#226655"
    assert admin.get("/api/public/config").json() == before
    assert design(admin, m, "import").status_code == 409
    assert design(admin, m).json()["available"] is False
    assert admin.post("/api/admin/config/publish").status_code == 200
    assert (
        admin.get("/api/public/config").json()["frontend_theme"]["hero_layout"]
        == "split"
    )
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("manifest.json", json.dumps({**m, "id": "other-design"}))
        z.writestr("../escape", "bad")
    assert (
        admin.post(
            "/api/admin/builder/design/validate",
            files={"file": ("unsafe.zip", stream.getvalue())},
        ).status_code
        == 422
    )
    assert (
        admin.post(
            "/api/admin/builder/design/validate",
            files={"file": ("bad.zip", b"not-a-zip")},
        ).status_code
        == 422
    )
    # The exact downloaded AI reference package is accepted without running its source.
    kit = admin.get("/api/admin/builder/reference").content
    assert (
        admin.post(
            "/api/admin/builder/design/validate", files={"file": ("reference.zip", kit)}
        ).status_code
        == 200
    )


def test_checks_detect_missing_assets_and_low_contrast(admin):
    c = config(admin)
    c["hero_image"] = "/api/public/files/" + "a" * 32
    c["frontend_theme"].update(background="#ffffff", foreground="#ffffff")
    assert admin.put("/api/admin/config", json=c).status_code == 200
    report = admin.get("/api/admin/builder/check").json()
    assert report["valid"] is False
    assert any(x["id"] == "hero_image" and not x["ok"] for x in report["checks"])
    assert any(x["id"] == "contrast" and not x["ok"] for x in report["checks"])
    assert admin.post("/api/admin/config/publish").status_code == 422


def test_history_compares_and_restores_draft_without_changing_public_site(admin):
    c = config(admin)
    c["company"] = "Erste Firma"
    publish(admin, c)
    rows = admin.get("/api/admin/builder/versions").json()
    old = next(
        x for x in rows if x["kind"] == "published" and x["label"] == "Veröffentlicht"
    )
    c["company"] = "Zweite Firma"
    publish(admin, c)
    diff = admin.get(f"/api/admin/builder/versions/{old['id']}").json()
    assert {
        "field": "company",
        "current": "Zweite Firma",
        "saved": "Erste Firma",
    } in diff["changes"]
    r = admin.post(f"/api/admin/builder/versions/{old['id']}/restore")
    assert r.status_code == 200 and r.json()["company"] == "Erste Firma"
    assert admin.get("/api/public/config").json()["company"] == "Zweite Firma"
    assert any(
        x["label"] == "Vor Wiederherstellung"
        for x in admin.get("/api/admin/builder/versions").json()
    )
    assert admin.post("/api/admin/config/publish").status_code == 200
    assert admin.get("/api/public/config").json()["company"] == "Erste Firma"


def test_all_builder_routes_require_admin_and_domain_injection_is_rejected(admin):
    with TestClient(app) as staff:
        staff.headers["X-Requested-With"] = "Raumwerk"
        assert (
            staff.post(
                "/api/admin/login",
                json={"email": "staff@example.com", "password": "test-password-1234"},
            ).status_code
            == 200
        )
        for route in ["prompt", "reference", "imprint", "check", "versions"]:
            assert staff.get("/api/admin/builder/" + route).status_code == 403
        for route in ["project", "deployment"]:
            assert (
                staff.post(
                    "/api/admin/builder/" + route, json={"domain": "example.com"}
                ).status_code
                == 403
            )
        assert (
            design(staff, example_manifest(config(admin)), "import").status_code == 403
        )
    for value in [
        "https://example.com/path",
        "example.com\nCOOKIE_SECURE=0",
        "localhost",
        "127.0.0.1",
        "x.com:80",
        "$(whoami).com",
    ]:
        assert (
            admin.post(
                "/api/admin/builder/deployment", json={"domain": value}
            ).status_code
            == 422
        )
    plan = admin.post(
        "/api/admin/builder/deployment", json={"domain": "münchen.example.com"}
    ).json()
    assert plan["admin_url"] == "https://xn--mnchen-3ya.example.com/admin"


def test_successful_logins_do_not_exhaust_failure_limit_and_proxy_identity_is_explicit(
    client, monkeypatch
):
    from app.main import _limits, client_ip
    from starlette.requests import Request

    client.headers["X-Requested-With"] = "Raumwerk"
    for _ in range(10):
        assert (
            client.post(
                "/api/admin/login",
                json={"email": "admin@example.com", "password": "test-password-1234"},
            ).status_code
            == 200
        )
    _limits.clear()
    for _ in range(8):
        assert (
            client.post(
                "/api/admin/login",
                json={"email": "admin@example.com", "password": "wrong"},
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/admin/login", json={"email": "admin@example.com", "password": "wrong"}
        ).status_code
        == 429
    )
    req = Request(
        {
            "type": "http",
            "client": ("127.0.0.1", 1),
            "headers": [(b"x-real-ip", b"198.51.100.12")],
        }
    )
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "0")
    assert client_ip(req) == "127.0.0.1"
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
    assert client_ip(req) == "198.51.100.12"
    req = Request(
        {
            "type": "http",
            "client": ("127.0.0.1", 1),
            "headers": [(b"x-real-ip", b"bad-value")],
        }
    )
    assert client_ip(req) == "127.0.0.1"


def test_project_export_bootstraps_fresh_installation_without_users_leads_or_secrets(
    admin, tmp_path
):
    p = prop(admin, "published")
    template = upload(admin, "template")
    document = upload(admin, "document")
    p["documents"] = [document["id"]]
    assert admin.put("/api/admin/properties/" + str(p["id"]), json=p).status_code == 200
    c = config(admin)
    c.update(company="Exportierte Firma", disclosure_pdf=template["id"])
    c["modules"].update(disclosure=True, telegram=True)
    c["forms"]["contact"]["telegram"] = True
    secret = "test-secret-" + uuid.uuid4().hex
    lead = "private-lead-" + uuid.uuid4().hex
    assert (
        admin.put(
            "/api/admin/integrations/telegram",
            json={"token": secret, "chat_id": "private-destination"},
        ).status_code
        == 200
    )
    publish(admin, c)
    assert inquiry(admin, message=lead).status_code == 202
    response = admin.post("/api/admin/builder/project", json={"domain": "example.com"})
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        names = z.namelist()
        assert "Raumwerk/LIVE-STARTEN.sh" in names
        assert "Raumwerk/compose.production.yaml" in names
        assert not any(
            "/.local/" in n or n.endswith("/.env") or "/downloads/" in n for n in names
        )
        for name in names:
            assert secret.encode() not in z.read(name)
            assert lead.encode() not in z.read(name)
        seed = json.loads(z.read("Raumwerk/project/project.json"))
        assert seed["published"]["forms"]["contact"] == {
            "store": True,
            "email": False,
            "telegram": False,
            "phone_required": False,
        }
        assert len(seed["files"]) == 3
        assert (
            z.read("Raumwerk/project/files/" + template["id"])
            == (DATA / "files" / template["id"]).read_bytes()
        )
        # This archive was generated by the application, not supplied by an attacker.
        z.extractall(tmp_path / "unpacked")
    target = tmp_path / "destination"
    target.mkdir()
    environment = {
        **os.environ,
        "DATA_DIR": str(target),
        "DATABASE_URL": "sqlite:///" + str(target / "app.db"),
        "PYTHONPATH": "backend",
        "DELIVERY_WORKER": "0",
    }
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "backend/alembic.ini",
            "upgrade",
            "head",
        ],
        env=environment,
        check=True,
        capture_output=True,
    )
    seedpath = tmp_path / "unpacked/Raumwerk/project/project.json"
    code = """
import sys, json
from pathlib import Path
from sqlalchemy import select, func
from fastapi.testclient import TestClient
from app.project import import_project
from app.db import Session, Setting, User, Inquiry, Delivery, Property, File
from app.main import app
p = Path(sys.argv[1])
assert import_project(p) is True
with Session() as db:
    assert db.scalar(select(func.count()).select_from(User)) == 0
    assert db.scalar(select(func.count()).select_from(Inquiry)) == 0
    assert db.scalar(select(func.count()).select_from(Delivery)) == 0
    assert db.scalar(select(func.count()).select_from(Property)) == 1
    assert db.scalar(select(func.count()).select_from(File)) == 3
    assert not db.get(Setting, 'integration_telegram')
with TestClient(app) as client:
    c = client.get('/api/public/config').json()
    assert c['company'] == 'Exportierte Firma' and not c['modules']['telegram']
    rows = client.get('/api/public/properties').json()['items']
    assert len(rows) == 1
    assert client.get('/api/public/files/' + rows[0]['images'][0]['id']).status_code == 200
    assert not rows[0].get('documents')
    doc = next(f for f in json.loads(p.read_text())['files'] if f['purpose'] == 'document')
    assert client.get('/api/public/files/' + doc['id']).status_code == 404
with Session() as db:
    row = db.get(Setting, 'draft'); row.value = {**row.value, 'company': 'Changed after import'}; db.commit()
assert import_project(p) is False
with Session() as db:
    assert db.get(Setting, 'draft').value['company'] == 'Changed after import'
seed = json.loads(p.read_text()); seed['export_id'] = 'a' * 32; p.write_text(json.dumps(seed))
try: import_project(p)
except ValueError: pass
else: raise AssertionError('Different project must not overwrite existing installation')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(seedpath)],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_tampered_project_media_fails_before_writing_any_destination(admin, tmp_path):
    prop(admin, "published")
    response = admin.post("/api/admin/builder/project", json={})
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(tmp_path / "unpacked")
    seedpath = tmp_path / "unpacked/Raumwerk/project/project.json"
    seed = json.loads(seedpath.read_text())
    file = seedpath.parent / "files" / seed["files"][0]["id"]
    file.write_bytes(b"x" * file.stat().st_size)
    environment = {
        **os.environ,
        "DATA_DIR": str(tmp_path / "target"),
        "DATABASE_URL": "sqlite:///" + str(tmp_path / "target/app.db"),
        "PYTHONPATH": "backend",
    }
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "backend/alembic.ini",
            "upgrade",
            "head",
        ],
        env=environment,
        check=True,
        capture_output=True,
    )
    code = """
import sys
from app.project import import_project
from app.db import Session, Property, File
from sqlalchemy import select, func
try: import_project(sys.argv[1])
except ValueError: pass
else: raise AssertionError('Tampered media accepted')
with Session() as db:
    assert db.scalar(select(func.count()).select_from(Property)) == 0
    assert db.scalar(select(func.count()).select_from(File)) == 0
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(seedpath)],
        env=environment,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
