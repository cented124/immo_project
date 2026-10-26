import io, json, threading, uuid
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from PIL import Image
from aiosmtpd.controller import Controller
from sqlalchemy import select
from fastapi.testclient import TestClient
from app.main import app
from app.db import Session, Setting, Inquiry, Delivery, now
from app.delivery import process_once, purge

PDF = b"%PDF-1.4\n% Synthetic test fixture, not a disclosure template.\n%%EOF\n"


def config(client):
    return client.get("/api/admin/config").json()["draft"]


def publish(client, c):
    r = client.put("/api/admin/config", json=c)
    assert r.status_code == 200, r.text
    r = client.post("/api/admin/config/publish")
    assert r.status_code == 200, r.text


def upload(client, purpose="image"):
    if purpose in ["image", "brand"]:
        stream = io.BytesIO()
        Image.new("RGB", (100, 100), "#73947b").save(stream, "PNG")
        content = stream.getvalue()
        mime = "image/png"
        name = "test.png"
    else:
        content = PDF
        mime = "application/pdf"
        name = "test.pdf"
    r = client.post(
        "/api/admin/files",
        data={"purpose": purpose},
        files={"file": (name, content, mime)},
    )
    assert r.status_code == 200, r.text
    return r.json()


def prop(client, status="draft"):
    f = upload(client)
    data = {
        "title": "TESTOBJEKT – nicht real",
        "slug": "testobjekt-" + uuid.uuid4().hex[:8],
        "status": status,
        "city": "Hamburg",
        "postcode": "20095",
        "area": 90,
        "rooms": 3,
        "price": 450000,
        "description": "Ein rein synthetisches Testobjekt.",
        "certificate": "exempt",
        "exemption_reason": "Synthetischer Testfall, keine rechtliche Aussage",
        "images": [{"id": f["id"], "alt": "Testbild"}],
    }
    r = client.post("/api/admin/properties", json=data)
    assert r.status_code == 200, r.text
    return r.json()


def inquiry(client, **kw):
    data = {
        "first_name": "Test",
        "last_name": "Person",
        "email": "person@example.com",
        "message": "Eine synthetische Testanfrage.",
        "consent": True,
        **kw,
    }
    return client.post(
        "/api/public/inquiries",
        json=data,
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )


def test_login_roles_csrf_logout(client):
    assert client.get("/api/admin/me").status_code == 401
    assert (
        client.post(
            "/api/admin/login",
            json={"email": "staff@example.com", "password": "test-password-1234"},
        ).status_code
        == 403
    )
    client.headers["X-Requested-With"] = "Raumwerk"
    assert (
        client.post(
            "/api/admin/login", json={"email": "staff@example.com", "password": "wrong"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/admin/login",
            json={"email": "staff@example.com", "password": "test-password-1234"},
        ).status_code
        == 200
    )
    assert client.get("/api/admin/me").json()["role"] == "staff"
    assert client.put("/api/admin/config", json=config(client)).status_code == 403
    assert client.get("/api/admin/integrations/email").status_code == 403
    assert (
        client.post(
            "/api/admin/logout", headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert client.post("/api/admin/logout").status_code == 200
    assert client.get("/api/admin/me").status_code == 401


def test_neutral_identity_draft_publish_and_restart(admin):
    c = config(admin)
    before = admin.get("/api/public/config").json()["company"]
    c["company"] = "Andere Firma GmbH"
    assert admin.put("/api/admin/config", json=c).status_code == 200
    assert admin.get("/api/public/config").json()["company"] == before
    assert admin.post("/api/admin/config/publish").status_code == 200
    with TestClient(app) as restarted:
        assert (
            restarted.get("/api/public/config").json()["company"] == "Andere Firma GmbH"
        )
    assert "Aurevia" not in json.dumps(c)


def test_module_disabling_blocks_api_and_files(admin):
    p = prop(admin, "published")
    image = p["images"][0]["id"]
    assert admin.get("/api/public/files/" + image).status_code == 200
    c = config(admin)
    c["modules"]["properties"] = False
    c["modules"]["contact"] = False
    publish(admin, c)
    assert admin.get("/api/public/properties").status_code == 404
    assert admin.get("/api/public/properties/" + p["slug"]).status_code == 404
    assert admin.get("/api/public/files/" + image).status_code == 404
    assert inquiry(admin).status_code == 404


def test_property_draft_publication_application_and_withdrawal(admin):
    p = prop(admin)
    image = p["images"][0]["id"]
    assert admin.get("/api/public/properties").json()["total"] == 0
    assert admin.get("/api/public/files/" + image).status_code == 404
    p["street"] = "Geheime Straße"
    p["house_number"] = "13"
    p["status"] = "published"
    assert admin.put("/api/admin/properties/" + str(p["id"]), json=p).status_code == 200
    public = admin.get("/api/public/properties/" + p["slug"]).json()
    assert "street" not in public and "house_number" not in public
    assert (
        admin.get("/api/public/properties?q=Hamburg&min_area=80&rooms=3").json()[
            "total"
        ]
        == 1
    )
    assert admin.get("/api/public/properties?max_price=10").json()["total"] == 0
    response = inquiry(admin, property_id=p["id"])
    assert response.status_code == 202
    rows = admin.get("/api/admin/inquiries?property_id=" + str(p["id"])).json()
    assert rows[0]["property_id"] == p["id"] and rows[0]["kind"] == "application"
    assert inquiry(admin, property_id=999999).status_code == 404
    p["status"] = "archived"
    assert admin.put("/api/admin/properties/" + str(p["id"]), json=p).status_code == 200
    assert admin.get("/api/public/properties/" + p["slug"]).status_code == 404
    assert admin.get("/api/public/files/" + image).status_code == 404


def test_publication_validation_and_rent_calculation(admin):
    data = {"title": "Unvollständig", "slug": "unvollstaendig", "status": "published"}
    assert admin.post("/api/admin/properties", json=data).status_code == 422
    p = prop(admin)
    p.update(
        offer="rent",
        price=1000,
        service_charge=200,
        heating_cost=100,
        heating_included=True,
    )
    r = admin.put("/api/admin/properties/" + str(p["id"]), json=p)
    assert r.json()["total_rent"] == 1200
    p["heating_included"] = False
    assert (
        admin.put("/api/admin/properties/" + str(p["id"]), json=p).json()["total_rent"]
        == 1300
    )
    copy = admin.post("/api/admin/properties/" + str(p["id"]) + "/duplicate").json()
    assert copy["status"] == "draft" and len(copy["images"]) == 1
    assert copy["images"][0]["id"] != p["images"][0]["id"]
    assert (
        next(
            x
            for x in admin.get("/api/admin/properties").json()
            if x["id"] == copy["id"]
        )["images"]
        == copy["images"]
    )
    assert admin.get("/api/public/files/" + copy["images"][0]["id"]).status_code == 404


def test_form_idempotency_validation_and_rate_limits(admin):
    body = {
        "first_name": "T",
        "last_name": "P",
        "email": "person@example.com",
        "message": "Eine Testanfrage",
        "consent": True,
    }
    key = str(uuid.uuid4())
    headers = {"Idempotency-Key": key}
    a = admin.post("/api/public/inquiries", json=body, headers=headers)
    b = admin.post("/api/public/inquiries", json=body, headers=headers)
    assert (
        a.status_code == b.status_code == 202
        and a.json()["reference"] == b.json()["reference"]
    )
    assert len(admin.get("/api/admin/inquiries").json()) == 1
    assert (
        admin.post(
            "/api/public/inquiries",
            json={**body, "message": "Andere Nachricht"},
            headers=headers,
        ).status_code
        == 409
    )
    assert inquiry(admin, consent=False).status_code == 422
    assert inquiry(admin, website="spam").status_code == 422
    assert inquiry(admin, email="invalid").status_code == 422
    for _ in range(9):
        assert inquiry(admin).status_code == 202
    assert inquiry(admin).status_code == 429


def test_inquiry_status_notes_export_and_delete(admin):
    r = inquiry(admin, first_name='=HYPERLINK("bad")')
    iid = r.json()["reference"]
    assert (
        admin.patch(
            f"/api/admin/inquiries/{iid}",
            json={"status": "processing", "notes": "Rückruf abstimmen"},
        ).status_code
        == 200
    )
    filtered = admin.get("/api/admin/inquiries?status=processing&q=example.com").json()
    assert len(filtered) == 1
    assert filtered[0]["notes"] == "Rückruf abstimmen"
    export = admin.get("/api/admin/export")
    assert export.status_code == 200 and "'=HYPERLINK" in export.text
    assert admin.delete(f"/api/admin/inquiries/{iid}").status_code == 200
    assert admin.get("/api/admin/inquiries").json() == []


def test_pdf_replacement_private_return_and_anonymous_access(admin):
    f = upload(admin, "template")
    assert admin.get("/api/public/files/" + f["id"]).status_code == 404
    c = config(admin)
    c.update(disclosure_pdf=f["id"], disclosure_returns=True)
    c["modules"]["disclosure"] = True
    publish(admin, c)
    assert admin.get("/api/public/files/" + f["id"]).content == PDF
    second = upload(admin, "template")
    c["disclosure_pdf"] = second["id"]
    publish(admin, c)
    assert admin.get("/api/public/files/" + f["id"]).status_code == 404
    accepted = inquiry(admin).json()
    iid = accepted["reference"]
    r = admin.post(
        "/api/public/disclosure-return",
        data={
            "reference": iid,
            "email": "person@example.com",
            "return_code": "wrong",
            "consent": "true",
        },
        files={"file": ("filled.pdf", PDF, "application/pdf")},
    )
    assert r.status_code == 422
    r = admin.post(
        "/api/public/disclosure-return",
        data={
            "reference": iid,
            "email": "person@example.com",
            "return_code": accepted["document_token"],
            "consent": "true",
        },
        files={"file": ("filled.pdf", PDF, "application/pdf")},
    )
    assert r.status_code == 202, r.text
    private = next(
        x for x in admin.get("/api/admin/files").json() if x["purpose"] == "return"
    )
    with TestClient(app) as anonymous:
        assert anonymous.get("/api/public/files/" + private["id"]).status_code == 404
        assert anonymous.get("/api/admin/files/" + private["id"]).status_code == 401
        assert anonymous.get("/api/admin/inquiries").status_code == 401
    assert admin.get("/api/admin/files/" + private["id"]).content == PDF
    c["modules"]["disclosure"] = False
    publish(admin, c)
    assert admin.get("/api/public/files/" + second["id"]).status_code == 404


def test_upload_and_manifest_validation(admin):
    assert (
        admin.post(
            "/api/admin/files",
            data={"purpose": "image"},
            files={"file": ("bad.svg", b'<svg onload="alert(1)"/>', "image/svg+xml")},
        ).status_code
        == 422
    )
    assert (
        admin.post(
            "/api/admin/files",
            data={"purpose": "template"},
            files={"file": ("bad.pdf", b"not PDF", "application/pdf")},
        ).status_code
        == 422
    )
    assert (
        admin.post(
            "/api/admin/templates/validate",
            json={"id": "../../escape", "adapter": "javascript"},
        ).status_code
        == 422
    )
    manifest = {
        "id": "test-design",
        "name": "Test",
        "version": 1,
        "adapter": "editorial",
        "pages": ["home", "properties", "property", "contact", "disclosure", "content"],
        "actions": ["search", "inquiry", "download", "return"],
    }
    assert admin.post("/api/admin/templates/validate", json=manifest).json()["valid"]
    assert len(admin.get("/api/admin/templates").json()) == 2


def test_analytics_actual_events_and_disabled_state(admin):
    assert admin.get("/api/admin/dashboard").json()["events"] is None
    assert (
        admin.post(
            "/api/public/events", json={"kind": "pageview", "path": "/"}
        ).status_code
        == 404
    )
    c = config(admin)
    c["modules"]["analytics"] = True
    publish(admin, c)
    for kind in ["pageview", "property_view", "inquiry_click"]:
        assert (
            admin.post(
                "/api/public/events", json={"kind": kind, "path": "/immobilien/test"}
            ).status_code
            == 202
        )
    assert inquiry(admin).status_code == 202
    d = admin.get("/api/admin/dashboard").json()
    assert d["events"] == {
        "pageview": 1,
        "property_view": 1,
        "inquiry_click": 1,
        "submission": 1,
    }
    assert d["new_inquiries"] == 1 and d["daily"][0]["count"] == 1


def smtp_settings():
    return {
        "host": "127.0.0.1",
        "port": 18025,
        "tls": "none",
        "sender": "firma@example.com",
        "sender_name": "Testfirma",
        "recipients": ["team@example.com"],
        "confirmation": False,
    }


def test_smtp_real_test_service_and_outbox(admin):
    messages = []

    class Sink:
        async def handle_DATA(self, server, session, envelope):
            messages.append(envelope)
            return "250 accepted"

    controller = Controller(Sink(), hostname="127.0.0.1", port=18025)
    controller.start()
    try:
        assert (
            admin.put(
                "/api/admin/integrations/email",
                json={**smtp_settings(), "password": "supersecret"},
            ).status_code
            == 200
        )
        assert admin.get("/api/admin/integrations/email").json()["password"] == ""
        with Session() as db:
            assert "supersecret" not in json.dumps(
                db.get(Setting, "integration_email").value
            )
        # No username -> anonymous local SMTP test, as expected.
        assert admin.post("/api/admin/integrations/email/test").status_code == 200
        c = config(admin)
        c["modules"]["email"] = True
        c["forms"]["contact"]["email"] = True
        publish(admin, c)
        assert inquiry(admin).status_code == 202
        assert process_once()
        row = admin.get("/api/admin/deliveries").json()[0]
        assert row["status"] == "sent"
        assert messages[-1].mail_from == "firma@example.com"
        assert b"Reply-To: person@example.com" in messages[-1].content
    finally:
        controller.stop()


def test_telegram_real_http_test_service(admin, monkeypatch):
    received = []

    class Sink(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(
                json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Sink)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv(
        "TELEGRAM_API_BASE", "http://127.0.0.1:" + str(server.server_port)
    )
    try:
        assert (
            admin.put(
                "/api/admin/integrations/telegram",
                json={"token": "testtoken", "chat_id": "123", "include_details": False},
            ).status_code
            == 200
        )
        assert admin.get("/api/admin/integrations/telegram").json()["token"] == ""
        assert admin.post("/api/admin/integrations/telegram/test").status_code == 200
        c = config(admin)
        c["modules"]["telegram"] = True
        c["forms"]["contact"]["telegram"] = True
        publish(admin, c)
        inquiry(admin)
        process_once()
        assert admin.get("/api/admin/deliveries").json()[0]["status"] == "sent"
        assert (
            "person@example.com" not in received[-1]["text"]
            and received[-1]["chat_id"] == "123"
        )
    finally:
        server.shutdown()
        server.server_close()


def test_failed_delivery_retry_and_technical_retention(admin):
    s = smtp_settings()
    s["port"] = 18999
    assert admin.put("/api/admin/integrations/email", json=s).status_code == 200
    c = config(admin)
    c["modules"]["email"] = True
    c["forms"]["contact"].update(store=False, email=True)
    publish(admin, c)
    assert inquiry(admin).status_code == 202
    assert admin.get("/api/admin/inquiries").json() == []
    for i in range(4):
        with Session() as db:
            d = db.scalar(select(Delivery))
            d.next_attempt = now() - timedelta(seconds=1)
            db.commit()
        process_once()
    row = admin.get("/api/admin/deliveries").json()[0]
    assert row["status"] == "failed" and row["attempts"] == 4
    assert (
        admin.post("/api/admin/deliveries/" + str(row["id"]) + "/retry").status_code
        == 200
    )
    assert admin.get("/api/admin/deliveries").json()[0]["status"] == "pending"
    with Session() as db:
        r = db.scalar(select(Inquiry))
        r.created = now() - timedelta(hours=25)
        db.commit()
    purge()
    with Session() as db:
        assert (
            db.scalar(select(Inquiry)) is None and db.scalar(select(Delivery)) is None
        )


def test_phone_requirement_and_invalid_config(admin):
    c = config(admin)
    c["forms"]["contact"]["phone_required"] = True
    publish(admin, c)
    assert inquiry(admin).status_code == 422
    assert inquiry(admin, phone="+49123456").status_code == 202
    c["primary"] = "javascript:alert(1)"
    assert admin.put("/api/admin/config", json=c).status_code == 422
    c = config(admin)
    c["modules"]["disclosure"] = True
    assert admin.put("/api/admin/config", json=c).status_code == 200
    assert admin.post("/api/admin/config/publish").status_code == 422
