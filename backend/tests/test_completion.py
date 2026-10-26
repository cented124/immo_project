import json
from app.db import Session, Delivery, File
from sqlalchemy import select
from fastapi.testclient import TestClient
from app.main import app
from test_workflows import config, publish, upload, inquiry, prop, PDF


def test_template_import_is_persistent_and_code_cannot_be_imported(admin):
    assert "Template-Schnittstelle" in admin.get("/api/admin/help/templates").text
    manifest = {
        "id": "eigene-firma",
        "name": "Eigenes Design",
        "version": 1,
        "adapter": "editorial",
        "pages": ["home", "properties", "property", "contact", "disclosure", "content"],
        "actions": ["search", "inquiry", "download", "return"],
    }
    assert (
        admin.post(
            "/api/admin/templates/import", json={**manifest, "script": "alert(1)"}
        ).status_code
        == 422
    )
    assert admin.post("/api/admin/templates/import", json=manifest).status_code == 201
    assert admin.post("/api/admin/templates/import", json=manifest).status_code == 409
    c = config(admin)
    c["template"] = manifest["id"]
    publish(admin, c)
    assert admin.get("/api/public/config").json()["template_adapter"] == "editorial"
    assert any(
        t["id"] == manifest["id"] for t in admin.get("/api/admin/templates").json()
    )


def test_per_page_forms_and_form_statistics(admin):
    c = config(admin)
    c["forms"]["bewertung"] = {**c["forms"]["contact"], "phone_required": True}
    publish(admin, c)
    assert inquiry(admin, page="bewertung").status_code == 422
    assert inquiry(admin, page="bewertung", phone="0123456").status_code == 202
    assert inquiry(admin).status_code == 202
    byform = admin.get("/api/admin/dashboard").json()["by_form"]
    assert {x["kind"] for x in byform} == {"bewertung", "contact"}
    c["pages"] = [
        {**p, "enabled": False} if p["slug"] == "bewertung" else p for p in c["pages"]
    ]
    publish(admin, c)
    assert inquiry(admin, page="bewertung", phone="0123456").status_code == 404


def test_account_revocation_and_last_admin_protection(admin):
    rows = admin.get("/api/admin/users").json()
    owner = next(x for x in rows if x["role"] == "admin")
    staff = next(x for x in rows if x["role"] == "staff")
    assert (
        admin.patch(
            "/api/admin/users/" + str(owner["id"]), json={"active": False}
        ).status_code
        == 409
    )
    with TestClient(app) as employee:
        employee.headers["X-Requested-With"] = "Raumwerk"
        assert (
            employee.post(
                "/api/admin/login",
                json={"email": "staff@example.com", "password": "test-password-1234"},
            ).status_code
            == 200
        )
        assert (
            admin.patch(
                "/api/admin/users/" + str(staff["id"]), json={"active": False}
            ).status_code
            == 200
        )
        assert employee.get("/api/admin/me").status_code == 401
        assert (
            employee.post(
                "/api/admin/login",
                json={"email": "staff@example.com", "password": "test-password-1234"},
            ).status_code
            == 401
        )
    assert admin.delete("/api/admin/users/" + str(staff["id"])).status_code == 200


def test_self_password_change_revokes_all_sessions(admin):
    assert (
        admin.post(
            "/api/admin/account/password",
            json={"current_password": "wrong", "password": "a-new-password-123"},
        ).status_code
        == 400
    )
    assert (
        admin.post(
            "/api/admin/account/password",
            json={
                "current_password": "test-password-1234",
                "password": "a-new-password-123",
            },
        ).status_code
        == 200
    )
    assert admin.get("/api/admin/me").status_code == 401
    assert (
        admin.post(
            "/api/admin/login",
            json={"email": "admin@example.com", "password": "a-new-password-123"},
        ).status_code
        == 200
    )


def test_document_return_is_atomic_deduplicated_and_has_own_notifications(admin):
    f = upload(admin, "template")
    c = config(admin)
    c.update(disclosure_pdf=f["id"], disclosure_returns=True)
    c["modules"]["disclosure"] = True
    c["modules"]["telegram"] = True
    assert (
        admin.put(
            "/api/admin/integrations/telegram",
            json={"token": "local-test-token", "chat_id": "local-test-chat"},
        ).status_code
        == 200
    )
    c["forms"]["disclosure"] = {**c["forms"]["contact"], "telegram": True}
    publish(admin, c)
    accepted = inquiry(admin).json()
    data = {
        "reference": accepted["reference"],
        "email": "person@example.com",
        "return_code": accepted["document_token"],
        "consent": "true",
    }
    for _ in range(2):
        r = admin.post(
            "/api/public/disclosure-return",
            data=data,
            files={"file": ("filled.pdf", PDF, "application/pdf")},
        )
        assert r.status_code == 202, r.text
    with Session() as db:
        files = db.scalars(select(File).where(File.purpose == "return")).all()
        jobs = db.scalars(select(Delivery)).all()
        assert len(files) == len(jobs) == 1
        assert (
            jobs[0].payload["kind"] == "disclosure_return"
            and jobs[0].payload["file_id"] == files[0].id
        )
        assert "PDF-1.4" not in json.dumps(jobs[0].payload)


def test_preview_of_disabled_module_is_private(admin):
    p = prop(admin)
    c = config(admin)
    c["modules"]["properties"] = False
    publish(admin, c)
    c["modules"]["properties"] = True
    assert admin.put("/api/admin/config", json=c).status_code == 200
    assert admin.get("/api/public/properties").status_code == 404
    assert any(
        r["id"] == p["id"] for r in admin.get("/api/admin/preview/properties").json()
    )
    with TestClient(app) as anonymous:
        assert anonymous.get("/api/admin/preview/properties").status_code == 401


def test_chunked_upload_limit_without_content_length(admin):
    def stream():
        for _ in range(13):
            yield b"x" * 1024 * 1024

    r = admin.post(
        "/api/admin/files",
        content=stream(),
        headers={"Content-Type": "application/octet-stream"},
    )
    assert r.status_code == 413


def test_unicode_notes_search_and_filtered_export(admin):
    accepted = inquiry(admin, first_name="Jörg").json()
    inquiry(admin, first_name="Andere Person")
    assert len(admin.get("/api/admin/inquiries?q=Jörg").json()) == 1
    admin.patch(
        "/api/admin/inquiries/" + str(accepted["reference"]),
        json={"status": "processing", "notes": "Rückruf München"},
    )
    assert len(admin.get("/api/admin/inquiries?q=München").json()) == 1
    exported = admin.get("/api/admin/export?q=München&status=processing").text
    assert "Jörg" in exported and "Andere Person" not in exported


def test_temporary_telegram_and_permanent_smtp_errors(admin, monkeypatch):
    import httpx, smtplib
    from app import delivery

    c = config(admin)
    c["modules"]["email"] = True
    c["forms"]["contact"]["email"] = True
    admin.put(
        "/api/admin/integrations/email",
        json={
            "host": "127.0.0.1",
            "port": 18025,
            "tls": "none",
            "sender": "firma@example.com",
            "recipients": ["team@example.com"],
        },
    )
    publish(admin, c)

    def authentication_error(*args, **kwargs):
        raise smtplib.SMTPAuthenticationError(535, b"provider detail must stay private")

    monkeypatch.setattr(delivery, "send_email", authentication_error)
    inquiry(admin)
    delivery.process_once()
    row = admin.get("/api/admin/deliveries").json()[0]
    assert (
        row["status"] == "failed"
        and row["attempts"] == 1
        and "provider detail" not in row["error"]
    )
    c["forms"]["contact"]["email"] = False
    c["modules"]["email"] = False
    c["modules"]["telegram"] = True
    c["forms"]["contact"]["telegram"] = True
    admin.put(
        "/api/admin/integrations/telegram",
        json={"token": "local-test", "chat_id": "local-test"},
    )
    publish(admin, c)
    monkeypatch.setattr(
        delivery.httpx,
        "post",
        lambda *args, **kwargs: httpx.Response(429, json={"ok": False}),
    )
    inquiry(admin)
    delivery.process_once()
    row = admin.get("/api/admin/deliveries").json()[0]
    assert row["status"] == "retry" and row["attempts"] == 1
