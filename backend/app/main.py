import csv, hashlib, io, json, os, re, secrets, threading, time, warnings, ipaddress
from contextlib import asynccontextmanager
from datetime import timedelta, timezone
from typing import Literal
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Response, Depends, UploadFile, Form
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from PIL import Image
from .db import (
    Session,
    Setting,
    User,
    LoginSession,
    Property,
    Inquiry,
    Submission,
    Delivery,
    File,
    Event,
    Audit,
    Revision,
    DATA,
    now,
)
from .config import Config, PropertyData
from .security import hasher, digest, encrypt, document_token
from .delivery import integration, send_email, send_telegram, safe_error, worker
from .templates import Manifest, library, resolve, presentation
from .uploads import BodySizeLimit
from .builder import (
    add_revision,
    check_config,
    prompt,
    reference_zip,
    imprint,
    parse_design,
    domain_name,
)
from .project import export_project

SESSION_COOKIE = os.getenv("SESSION_COOKIE_NAME", "raumwerk_session")


def initialize():
    with Session() as db:
        for key in ["draft", "published"]:
            if not db.get(Setting, key):
                db.add(Setting(key=key, value=Config().model_dump()))
            else:
                db.get(Setting, key).value = Config.model_validate(
                    db.get(Setting, key).value
                ).model_dump()
        db.commit()


@asynccontextmanager
async def lifespan(app):
    initialize()
    stop = threading.Event()
    thread = None
    if os.getenv("DELIVERY_WORKER", "1") == "1":
        thread = threading.Thread(target=worker, args=(stop,), daemon=True)
        thread.start()
    yield
    stop.set()
    if thread:
        thread.join(timeout=20)


app = FastAPI(title="Raumwerk · Immobilien-Baukasten", lifespan=lifespan)
app.add_middleware(BodySizeLimit)


def db_session():
    with Session() as db:
        yield db


def cfg(db):
    return db.get(Setting, "published").value


def module(db, name):
    if not cfg(db)["modules"].get(name):
        raise HTTPException(404, "Dieses Modul ist nicht verfügbar")


def audit(db, user, action):
    db.add(Audit(actor=user.email, action=action))


_limits = {}
_limit_lock = threading.Lock()


def client_ip(request):
    # Only the production Caddy topology enables this. Caddy overwrites X-Real-IP;
    # API and Next are not publicly exposed. Ordinary development ignores it.
    if os.getenv("TRUST_PROXY_HEADERS", "0") == "1":
        try:
            return str(ipaddress.ip_address(request.headers.get("x-real-ip", "")))
        except ValueError:
            pass
    return request.client.host if request.client else "local"


def limit(request, bucket, maximum=12, seconds=600):
    key = (client_ip(request), bucket)
    with _limit_lock:
        if len(_limits) > 10000:
            for k in list(_limits):
                if all(t < time.monotonic() - 3600 for t in _limits[k]):
                    _limits.pop(k, None)
        values = [t for t in _limits.get(key, []) if t > time.monotonic() - seconds]
        if len(values) >= maximum:
            raise HTTPException(
                429, "Zu viele Versuche. Bitte später erneut versuchen."
            )
        _limits[key] = values + [time.monotonic()]


@app.middleware("http")
async def safety(request, call_next):
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        origin = request.headers.get("origin")
        allowed = os.getenv("PUBLIC_ORIGIN", "http://localhost:3000").split(",")
        if origin and origin.rstrip("/") not in allowed:
            return Response("Unzulässiger Ursprung", status_code=403)
        if (
            request.url.path.startswith("/api/admin")
            and request.headers.get("x-requested-with") != "Raumwerk"
        ):
            return Response("CSRF-Schutz: Request-Header fehlt", status_code=403)
        size = request.headers.get("content-length")
        if size:
            try:
                length = int(size)
            except ValueError:
                return Response("Ungültige Größenangabe", status_code=400)
            if length < 0:
                return Response("Ungültige Größenangabe", status_code=400)
            if length > 12 * 1024 * 1024:
                return Response("Datei zu groß", status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    return response


def current(request: Request, db=Depends(db_session)):
    token = request.cookies.get(SESSION_COOKIE, "")
    session = db.get(LoginSession, digest(token)) if token else None
    expires = session.expires.replace(tzinfo=timezone.utc) if session else None
    if not session or expires < now():
        raise HTTPException(401, "Bitte anmelden")
    user = db.get(User, session.user_id)
    if not user or not user.active:
        raise HTTPException(401, "Sitzung ungültig")
    return user


def admin(user=Depends(current)):
    if user.role != "admin":
        raise HTTPException(403, "Nur Administratoren dürfen diese Einstellung ändern")
    return user


class Login(BaseModel):
    email: EmailStr
    password: str = Field(max_length=512)


@app.post("/api/admin/login")
def login(data: Login, request: Request, response: Response, db=Depends(db_session)):
    limit(request, "login-ip", 60)
    bucket = "login:" + data.email.lower()
    limit(request, bucket, 8)
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    try:
        if not user:
            hasher.verify(hasher.hash("unused-dummy-password"), data.password)
        else:
            hasher.verify(user.password, data.password)
    except Exception:
        raise HTTPException(401, "E-Mail oder Passwort ist nicht korrekt")
    if not user or not user.active:
        raise HTTPException(401, "E-Mail oder Passwort ist nicht korrekt")
    with _limit_lock:
        _limits.pop((client_ip(request), bucket), None)
    token = secrets.token_urlsafe(48)
    db.add(
        LoginSession(
            token=digest(token), user_id=user.id, expires=now() + timedelta(hours=12)
        )
    )
    audit(db, user, "Anmeldung")
    db.commit()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="strict",
        secure=os.getenv("COOKIE_SECURE", "0") == "1",
        max_age=43200,
        path="/",
    )
    return {"email": user.email, "role": user.role}


@app.get("/api/admin/me")
def me(user=Depends(current)):
    return {"email": user.email, "role": user.role}


@app.post("/api/admin/logout")
def logout(
    request: Request, response: Response, user=Depends(current), db=Depends(db_session)
):
    db.execute(
        delete(LoginSession).where(
            LoginSession.token == digest(request.cookies.get(SESSION_COOKIE, ""))
        )
    )
    db.commit()
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


class UserInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=200)
    role: Literal["admin", "staff"] = "staff"


@app.get("/api/admin/users")
def users(user=Depends(admin), db=Depends(db_session)):
    return [
        {"id": u.id, "email": u.email, "role": u.role, "active": u.active}
        for u in db.scalars(select(User))
    ]


@app.post("/api/admin/users")
def add_user(data: UserInput, user=Depends(admin), db=Depends(db_session)):
    row = User(
        email=data.email.lower(), password=hasher.hash(data.password), role=data.role
    )
    db.add(row)
    audit(db, user, "Benutzer angelegt")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "E-Mail existiert bereits")
    return {"id": row.id, "email": row.email, "role": row.role}


class AccountPassword(BaseModel):
    current_password: str = Field(max_length=512)
    password: str = Field(min_length=12, max_length=200)


@app.post("/api/admin/account/password")
def change_password(
    data: AccountPassword,
    request: Request,
    user=Depends(current),
    db=Depends(db_session),
):
    limit(request, "password-change", 5)
    try:
        hasher.verify(user.password, data.current_password)
    except Exception:
        raise HTTPException(400, "Das aktuelle Passwort ist nicht korrekt")
    row = db.get(User, user.id)
    row.password = hasher.hash(data.password)
    db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    audit(db, user, "Eigenes Passwort geändert; Sitzungen beendet")
    db.commit()
    return {"ok": True, "message": "Passwort geändert. Bitte neu anmelden."}


class UserUpdate(BaseModel):
    role: Literal["admin", "staff"] | None = None
    active: bool | None = None
    password: str | None = Field(None, min_length=12, max_length=200)


@app.patch("/api/admin/users/{uid}")
def update_user(
    uid: int, data: UserUpdate, user=Depends(admin), db=Depends(db_session)
):
    row = db.get(User, uid)
    if not row:
        raise HTTPException(404, "Benutzer nicht gefunden")
    role = data.role or row.role
    active = row.active if data.active is None else data.active
    if row.role == "admin" and row.active and (role != "admin" or not active):
        count = db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == "admin", User.active == True, User.id != uid)
        )
        if not count:
            raise HTTPException(
                409, "Mindestens ein aktiver Administrator muss erhalten bleiben"
            )
    row.role = role
    row.active = active
    if data.password:
        row.password = hasher.hash(data.password)
    db.execute(delete(LoginSession).where(LoginSession.user_id == uid))
    audit(
        db,
        user,
        f"Benutzer {uid}: Rolle/Status oder Passwort aktualisiert; Sitzungen beendet",
    )
    db.commit()
    return {"id": row.id, "email": row.email, "role": row.role, "active": row.active}


@app.delete("/api/admin/users/{uid}")
def delete_user(uid: int, user=Depends(admin), db=Depends(db_session)):
    if uid == user.id:
        raise HTTPException(
            409, "Das eigene angemeldete Konto kann hier nicht gelöscht werden"
        )
    row = db.get(User, uid)
    if not row:
        raise HTTPException(404, "Benutzer nicht gefunden")
    db.execute(delete(LoginSession).where(LoginSession.user_id == uid))
    db.delete(row)
    audit(db, user, f"Benutzer {uid} gelöscht")
    db.commit()
    return {"ok": True}


@app.get("/api/health")
def health(db=Depends(db_session)):
    db.execute(select(1))
    return {"status": "ok"}


@app.get("/api/admin/help/templates")
def template_help(user=Depends(current)):
    path = Path(__file__).resolve().parents[2] / "docs" / "TEMPLATES.md"
    return Response(path.read_text(), media_type="text/plain; charset=utf-8")


@app.get("/api/public/config")
def public_config(db=Depends(db_session)):
    data = presentation(db, cfg(db))
    data.pop("frontend_brief", None)
    return data


@app.get("/api/admin/config")
def get_config(user=Depends(current), db=Depends(db_session)):
    return {
        "draft": presentation(db, db.get(Setting, "draft").value),
        "published": presentation(db, cfg(db)),
    }


@app.put("/api/admin/config")
def save_config(data: Config, user=Depends(admin), db=Depends(db_session)):
    resolve(db, data.template)
    if not db.scalar(select(Revision.id).limit(1)):
        add_revision(db, user, cfg(db), "published", "Ausgangsstand")
    db.get(Setting, "draft").value = data.model_dump()
    add_revision(db, user, data.model_dump())
    audit(db, user, "Konfigurationsentwurf gespeichert")
    db.commit()
    return presentation(db, data.model_dump())


@app.post("/api/admin/config/publish")
def publish_config(user=Depends(admin), db=Depends(db_session)):
    config = Config.model_validate(db.get(Setting, "draft").value)
    resolve(db, config.template)
    if config.modules.disclosure and not config.disclosure_pdf:
        raise HTTPException(422, "Zuerst eigenes PDF hochladen")
    for field in ["logo", "favicon", "hero_image", "approach_image"]:
        value = getattr(config, field)
        if value.startswith("/api/"):
            file = db.get(File, value.rsplit("/", 1)[-1])
            if not file or file.purpose != "brand":
                raise HTTPException(422, "Ungültige Unternehmensdatei")
    for form in config.forms.values():
        if form.email and not integration(db, "email").get("host"):
            raise HTTPException(422, "SMTP zuerst einrichten")
        if form.telegram and not integration(db, "telegram").get("token"):
            raise HTTPException(422, "Telegram zuerst einrichten")
    if config.disclosure_pdf:
        file = db.get(File, config.disclosure_pdf)
        if not file or file.purpose != "template":
            raise HTTPException(422, "PDF nicht gefunden")
    db.get(Setting, "published").value = config.model_dump()
    add_revision(db, user, config.model_dump(), "published", "Veröffentlicht")
    audit(db, user, "Website-Konfiguration veröffentlicht")
    db.commit()
    return {"ok": True}


def serialize_property(row, public=False):
    data = {
        **row.data,
        "id": row.id,
        "status": row.status,
        "slug": row.slug,
        "created": row.created.isoformat(),
    }
    if public:
        data.pop("number", None)
        data.pop("documents", None)
        if not data.get("show_address"):
            data.pop("street", None)
            data.pop("house_number", None)
    if data["offer"] == "rent":
        data["total_rent"] = round(
            data["price"]
            + data["service_charge"]
            + (0 if data["heating_included"] else data["heating_cost"]),
            2,
        )
    return data


@app.get("/api/public/properties")
def property_list(
    q: str = "",
    offer: str = "",
    type: str = "",
    min_price: float = 0,
    max_price: float = 1e12,
    min_area: float = 0,
    rooms: float = 0,
    sort: str = "newest",
    page: int = 1,
    db=Depends(db_session),
):
    module(db, "properties")
    rows = [
        serialize_property(p, True)
        for p in db.scalars(
            select(Property)
            .where(Property.status.in_(["published", "reserved"]))
            .order_by(Property.id.desc())
        )
    ]
    rows = [
        p
        for p in rows
        if (
            not q
            or q.lower() in (p["city"] + " " + p["postcode"] + " " + p["title"]).lower()
        )
        and (not offer or p["offer"] == offer)
        and (not type or p["type"] == type)
        and min_price <= p["price"] <= max_price
        and p["area"] >= min_area
        and p["rooms"] >= rooms
    ]
    if sort == "price_asc":
        rows.sort(key=lambda p: p["price"])
    if sort == "price_desc":
        rows.sort(key=lambda p: -p["price"])
    page = max(1, page)
    return {
        "items": rows[(page - 1) * 9 : page * 9],
        "total": len(rows),
        "page": page,
        "pages": (len(rows) + 8) // 9,
    }


@app.get("/api/public/properties/{slug}")
def property_detail(slug: str, db=Depends(db_session)):
    module(db, "properties")
    row = db.scalar(
        select(Property).where(
            Property.slug == slug, Property.status.in_(["published", "reserved"])
        )
    )
    if not row:
        raise HTTPException(404, "Diese Immobilie ist nicht mehr verfügbar")
    return serialize_property(row, True)


@app.get("/api/admin/preview/properties")
def preview_properties(user=Depends(current), db=Depends(db_session)):
    if not db.get(Setting, "draft").value["modules"]["properties"]:
        raise HTTPException(404, "Modul im Entwurf deaktiviert")
    return [
        serialize_property(p)
        for p in db.scalars(select(Property).order_by(Property.id.desc()))
    ]


@app.get("/api/admin/properties")
def admin_properties(user=Depends(current), db=Depends(db_session)):
    module(db, "properties")
    return [
        serialize_property(p)
        for p in db.scalars(select(Property).order_by(Property.id.desc()))
    ]


def check_media(data, db, property_id=None):
    for image in data.images:
        file = db.get(File, image.get("id", ""))
        if (
            not file
            or file.purpose != "image"
            or (file.property_id is not None and file.property_id != property_id)
        ):
            raise HTTPException(422, "Ungültiges oder fremdes Immobilienbild")
    for file_id in data.documents:
        file = db.get(File, file_id)
        if (
            not file
            or file.purpose != "document"
            or (file.property_id is not None and file.property_id != property_id)
        ):
            raise HTTPException(422, "Ungültiges Dokument")


def bind_media(data, db, property_id):
    for fid in [i["id"] for i in data.images] + data.documents:
        db.get(File, fid).property_id = property_id


@app.post("/api/admin/properties")
def create_property(data: PropertyData, user=Depends(current), db=Depends(db_session)):
    module(db, "properties")
    check_media(data, db)
    row = Property(slug=data.slug, status=data.status, data=data.model_dump())
    db.add(row)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Dieser URL-Slug wird bereits verwendet")
    bind_media(data, db, row.id)
    audit(db, user, f"Immobilie {row.id} erstellt: {row.status}")
    db.commit()
    return serialize_property(row)


@app.put("/api/admin/properties/{pid}")
def update_property(
    pid: int, data: PropertyData, user=Depends(current), db=Depends(db_session)
):
    module(db, "properties")
    row = db.get(Property, pid)
    if not row:
        raise HTTPException(404, "Immobilie nicht gefunden")
    check_media(data, db, pid)
    row.slug = data.slug
    row.status = data.status
    row.data = data.model_dump()
    bind_media(data, db, pid)
    audit(db, user, f"Immobilie {pid} gespeichert: {row.status}")
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Dieser URL-Slug wird bereits verwendet")
    return serialize_property(row)


@app.post("/api/admin/properties/{pid}/duplicate")
def duplicate(pid: int, user=Depends(current), db=Depends(db_session)):
    module(db, "properties")
    row = db.get(Property, pid)
    if not row:
        raise HTTPException(404, "Immobilie nicht gefunden")
    data = {
        **row.data,
        "title": row.data["title"] + " (Kopie)",
        "slug": row.slug + "-" + secrets.token_hex(3),
        "status": "draft",
        "images": [],
        "documents": [],
    }
    copy = Property(
        slug=data["slug"], status="draft", data={**data, "images": [], "documents": []}
    )
    db.add(copy)
    db.flush()
    copied = []
    try:
        for original in row.data.get("images", []) + [
            {"id": fid} for fid in row.data.get("documents", [])
        ]:
            source = db.get(File, original["id"])
            if not source:
                continue
            fid = secrets.token_hex(16)
            path = DATA / "files" / fid
            path.write_bytes((DATA / "files" / source.id).read_bytes())
            path.chmod(0o600)
            copied.append(path)
            db.add(
                File(
                    id=fid,
                    name=source.name,
                    mime=source.mime,
                    purpose=source.purpose,
                    property_id=copy.id,
                    size=source.size,
                )
            )
            if source.purpose == "image":
                data["images"].append({**original, "id": fid})
            else:
                data["documents"].append(fid)
        copy.data = dict(data)
        audit(
            db,
            user,
            f"Immobilie {pid} einschließlich Medien als privaten Entwurf dupliziert",
        )
        db.commit()
    except Exception:
        db.rollback()
        for path in copied:
            path.unlink(missing_ok=True)
        raise
    return serialize_property(copy)


class InquiryInput(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field("", max_length=50)
    subject: str = Field("Kontakt", max_length=150)
    message: str = Field(min_length=5, max_length=10000)
    consent: bool
    property_id: int | None = Field(None, gt=0)
    website: str = Field("", max_length=200)
    page: str = Field("", max_length=61)


@app.post("/api/public/inquiries", status_code=202)
def submit(data: InquiryInput, request: Request, db=Depends(db_session)):
    kind = "application" if data.property_id else "contact"
    module(db, "applications" if kind == "application" else "contact")
    if data.website:
        raise HTTPException(422, "Anfrage konnte nicht angenommen werden")
    if not data.consent:
        raise HTTPException(422, "Bitte den Datenschutzhinweis bestätigen")
    config = cfg(db)
    form_id = data.page if data.page and kind == "contact" else kind
    targets = config["forms"].get(form_id, config["forms"][kind])
    if targets["phone_required"] and not data.phone.strip():
        raise HTTPException(422, "Telefonnummer erforderlich")
    if data.page:
        page = next(
            (
                p
                for p in config["pages"]
                if p["slug"] == data.page and p["enabled"] and p["form"]
            ),
            None,
        )
        if not page:
            raise HTTPException(404, "Formular nicht verfügbar")
    if data.property_id:
        module(db, "properties")
        prop = db.get(Property, data.property_id)
        if not prop or prop.status not in ["published", "reserved"]:
            raise HTTPException(404, "Immobilie nicht verfügbar")
    key = request.headers.get("idempotency-key", "")
    if not re.fullmatch(r"[a-zA-Z0-9-]{16,128}", key):
        raise HTTPException(422, "Gültige Anfragekennung erforderlich")
    fingerprint = hashlib.sha256(data.model_dump_json().encode()).hexdigest()
    previous = db.get(Submission, key)
    if previous:
        if previous.fingerprint != fingerprint:
            raise HTTPException(409, "Anfragekennung bereits verwendet")
        return {
            "accepted": True,
            "reference": previous.inquiry_id,
            "document_token": document_token(key),
            "message": "Anfrage bereits angenommen",
        }
    limit(request, "form", 10)
    payload = data.model_dump(exclude={"website", "property_id", "consent"})
    payload["consent_at"] = now().isoformat()
    payload["privacy_notice"] = config["privacy_text"]
    payload["destinations"] = [k for k in ["store", "email", "telegram"] if targets[k]]
    payload["return_token_hash"] = digest(document_token(key))
    payload["form_id"] = form_id
    row = Inquiry(
        kind=kind, property_id=data.property_id, data=payload, retained=targets["store"]
    )
    db.add(row)
    db.flush()
    db.add(Submission(key=key, fingerprint=fingerprint, inquiry_id=row.id))
    for channel in ["email", "telegram"]:
        if targets[channel]:
            module(db, channel)
            settings = integration(db, channel)
            if channel == "telegram" and kind not in settings.get(
                "types", ["contact", "application"]
            ):
                continue
            db.add(Delivery(inquiry_id=row.id, channel=channel))
            if channel == "email" and settings.get("confirmation"):
                db.add(Delivery(inquiry_id=row.id, channel="confirmation"))
    if config["modules"]["analytics"]:
        db.add(
            Event(
                kind="submission",
                path="/immobilien" if data.property_id else "/kontakt",
            )
        )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        previous = db.get(Submission, key)
        if previous and previous.fingerprint == fingerprint:
            return {
                "accepted": True,
                "reference": previous.inquiry_id,
                "document_token": document_token(key),
            }
        raise HTTPException(409, "Anfragekennung bereits verwendet")
    return {
        "accepted": True,
        "reference": row.id,
        "document_token": document_token(key),
        "message": "Ihre Anfrage wurde angenommen. Externe Zustellungen werden separat verarbeitet.",
    }


def inquiry_dict(row):
    return {
        "id": row.id,
        "property_id": row.property_id,
        "kind": row.kind,
        "status": row.status,
        "data": row.data,
        "notes": row.notes,
        "created": row.created.isoformat(),
    }


@app.get("/api/admin/inquiries")
def inquiries(
    q: str = "",
    status: str = "",
    kind: str = "",
    property_id: int = 0,
    date_from: str = "",
    date_to: str = "",
    user=Depends(current),
    db=Depends(db_session),
):
    rows = db.scalars(
        select(Inquiry).where(Inquiry.retained == True).order_by(Inquiry.id.desc())
    ).all()
    return [
        inquiry_dict(r)
        for r in rows
        if (
            not q
            or q.lower() in json.dumps(r.data, ensure_ascii=False).lower()
            or q.lower() in r.notes.lower()
        )
        and (not status or r.status == status)
        and (not kind or r.kind == kind)
        and (not property_id or r.property_id == property_id)
        and (not date_from or r.created.isoformat()[:10] >= date_from)
        and (not date_to or r.created.isoformat()[:10] <= date_to)
    ]


class InquiryUpdate(BaseModel):
    status: Literal["new", "processing", "answered", "closed"]
    notes: str = Field("", max_length=20000)


@app.patch("/api/admin/inquiries/{iid}")
def edit_inquiry(
    iid: int, data: InquiryUpdate, user=Depends(current), db=Depends(db_session)
):
    row = db.get(Inquiry, iid)
    if not row or not row.retained:
        raise HTTPException(404, "Anfrage nicht gefunden")
    row.status = data.status
    row.notes = data.notes
    audit(db, user, f"Anfrage {iid}: {data.status}")
    db.commit()
    return inquiry_dict(row)


@app.delete("/api/admin/inquiries/{iid}")
def remove_inquiry(iid: int, user=Depends(admin), db=Depends(db_session)):
    row = db.get(Inquiry, iid)
    if not row:
        raise HTTPException(404, "Anfrage nicht gefunden")
    for file in db.scalars(select(File).where(File.inquiry_id == iid)).all():
        (DATA / "files" / file.id).unlink(missing_ok=True)
        db.delete(file)
    db.execute(delete(Delivery).where(Delivery.inquiry_id == iid))
    db.delete(row)
    audit(db, user, f"Anfrage {iid} gelöscht")
    db.commit()
    return {"ok": True}


@app.get("/api/admin/export")
def export(
    q: str = "",
    status: str = "",
    kind: str = "",
    property_id: int = 0,
    date_from: str = "",
    date_to: str = "",
    user=Depends(current),
    db=Depends(db_session),
):
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter=";")
    writer.writerow(
        [
            "ID",
            "Datum",
            "Typ",
            "Objekt",
            "Status",
            "Vorname",
            "Nachname",
            "E-Mail",
            "Telefon",
            "Nachricht",
        ]
    )

    def safe(v):
        s = str(v or "")
        return "'" + s if s.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else s

    for r in inquiries(
        q=q,
        status=status,
        kind=kind,
        property_id=property_id,
        date_from=date_from,
        date_to=date_to,
        user=user,
        db=db,
    ):
        writer.writerow(
            [
                safe(v)
                for v in [
                    r["id"],
                    r["created"],
                    r["kind"],
                    r["property_id"],
                    r["status"],
                    *[
                        r["data"].get(k, "")
                        for k in [
                            "first_name",
                            "last_name",
                            "email",
                            "phone",
                            "message",
                        ]
                    ],
                ]
            ]
        )
    return Response(
        "\ufeff" + stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="anfragen.csv"'},
    )


class SMTPConfig(BaseModel):
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(587, ge=1, le=65535)
    tls: Literal["starttls", "ssl", "none"] = "starttls"
    username: str = Field("", max_length=254)
    password: str = Field("", max_length=500)
    sender_name: str = Field("", max_length=100, pattern=r"^[^\r\n]*$")
    sender: EmailStr
    recipients: list[EmailStr] = Field(min_length=1, max_length=10)
    confirmation: bool = False

    @model_validator(mode="after")
    def tls_validation(self):
        if self.tls == "none" and os.getenv("ALLOW_INSECURE_SMTP", "0") != "1":
            raise ValueError(
                "Unverschlüsseltes SMTP nur für lokale Testdienste zulässig"
            )
        return self


class TelegramConfig(BaseModel):
    token: str = Field("", max_length=300, pattern=r"^[^\s/]*$")
    chat_id: str = Field(min_length=1, max_length=100)
    include_details: bool = False
    types: list[Literal["contact", "application"]] = ["contact", "application"]


@app.get("/api/admin/integrations/{channel}")
def get_integration(
    channel: Literal["email", "telegram"], user=Depends(admin), db=Depends(db_session)
):
    settings = integration(db, channel)
    secret = "password" if channel == "email" else "token"
    return {
        **{k: v for k, v in settings.items() if k != secret},
        secret: "",
        "secret_configured": bool(settings.get(secret)),
    }


@app.put("/api/admin/integrations/{channel}")
def save_integration(
    channel: Literal["email", "telegram"],
    data: dict,
    user=Depends(admin),
    db=Depends(db_session),
):
    try:
        value = (
            (SMTPConfig if channel == "email" else TelegramConfig)
            .model_validate(data)
            .model_dump(mode="json")
        )
    except Exception:
        raise HTTPException(
            422,
            "Ungültige Einstellungen. Empfänger, Port, TLS und Pflichtfelder prüfen.",
        )
    secret = "password" if channel == "email" else "token"
    old = integration(db, channel)
    if not value[secret]:
        value[secret] = old.get(secret, "")
    row = db.get(Setting, "integration_" + channel)
    encrypted = {"encrypted": encrypt(json.dumps(value))}
    if row:
        row.value = encrypted
    else:
        db.add(Setting(key="integration_" + channel, value=encrypted))
    audit(db, user, f"{channel}: Einstellungen gespeichert")
    db.commit()
    return {"ok": True}


@app.post("/api/admin/integrations/{channel}/test")
def test_integration(
    channel: Literal["email", "telegram"],
    request: Request,
    user=Depends(admin),
    db=Depends(db_session),
):
    limit(request, "integration-test", 5, 60)
    settings = integration(db, channel)
    try:
        if channel == "email":
            send_email(settings, {}, True)
        else:
            send_telegram(settings, {}, True)
    except Exception as e:
        raise HTTPException(502, safe_error(e))
    audit(db, user, f"{channel}: Test vom Zielserver bestätigt")
    db.commit()
    return {"ok": True, "message": "Die Testnachricht wurde vom Zielserver angenommen."}


@app.get("/api/admin/deliveries")
def deliveries(user=Depends(current), db=Depends(db_session)):
    return [
        {
            "id": r.id,
            "inquiry_id": r.inquiry_id,
            "channel": r.channel,
            "status": r.status,
            "attempts": r.attempts,
            "error": r.error,
        }
        for r in db.scalars(select(Delivery).order_by(Delivery.id.desc()).limit(200))
    ]


@app.post("/api/admin/deliveries/{did}/retry")
def retry(did: int, user=Depends(current), db=Depends(db_session)):
    row = db.get(Delivery, did)
    if not row:
        raise HTTPException(404, "Zustellung nicht gefunden")
    if row.status == "sent":
        raise HTTPException(409, "Bereits versendet")
    row.status = "pending"
    row.attempts = 0
    row.next_attempt = now()
    row.error = ""
    audit(db, user, f"Zustellung {did}: erneuter Versuch")
    db.commit()
    return {"ok": True}


async def store_file(
    upload, purpose, db, property_id=None, inquiry_id=None, commit=True
):
    content = await upload.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Maximal 10 MB pro Datei")
    name = Path(upload.filename or "Datei").name[:200]
    mime = "application/pdf"
    if purpose in ["image", "brand"]:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                image = Image.open(io.BytesIO(content))
                image.load()
            if image.format not in ["JPEG", "PNG", "WEBP"]:
                raise ValueError()
            image.thumbnail((2400, 1600))
            out = io.BytesIO()
            image.convert("RGB").save(out, "WEBP", quality=85)
            content = out.getvalue()
            mime = "image/webp"
            name = Path(name).stem + ".webp"
        except Exception:
            raise HTTPException(
                422, "Bitte ein gültiges JPEG-, PNG- oder WebP-Bild hochladen"
            )
    elif not content.startswith(b"%PDF-") or b"%%EOF" not in content[-2048:]:
        raise HTTPException(422, "Bitte eine gültige PDF-Datei hochladen")
    fid = secrets.token_hex(16)
    folder = DATA / "files"
    folder.mkdir(mode=0o700, exist_ok=True)
    path = folder / fid
    path.write_bytes(content)
    path.chmod(0o600)
    row = File(
        id=fid,
        name=name,
        mime=mime,
        purpose=purpose,
        property_id=property_id,
        inquiry_id=inquiry_id,
        size=len(content),
    )
    db.add(row)
    if commit:
        db.commit()
    else:
        db.flush()
    return {
        "id": fid,
        "name": name,
        "size": len(content),
        "purpose": purpose,
        "url": "/api/public/files/" + fid,
    }


@app.post("/api/admin/files")
async def upload_file(
    file: UploadFile,
    purpose: Literal["image", "brand", "template", "document"] = Form(...),
    user=Depends(current),
    db=Depends(db_session),
):
    if purpose in ["brand", "template"] and user.role != "admin":
        raise HTTPException(403, "Nur Administratoren")
    return await store_file(file, purpose, db)


@app.get("/api/admin/files")
def files(user=Depends(current), db=Depends(db_session)):
    return [
        {
            "id": f.id,
            "name": f.name,
            "purpose": f.purpose,
            "size": f.size,
            "property_id": f.property_id,
            "inquiry_id": f.inquiry_id,
        }
        for f in db.scalars(select(File).order_by(File.created.desc()))
    ]


@app.get("/api/admin/files/{fid}")
def private_file(fid: str, user=Depends(current), db=Depends(db_session)):
    file = db.get(File, fid)
    if not file:
        raise HTTPException(404, "Datei nicht gefunden")
    return FileResponse(
        DATA / "files" / file.id,
        media_type=file.mime,
        filename=file.name,
        content_disposition_type="inline"
        if file.mime.startswith("image/")
        else "attachment",
        headers={"Content-Security-Policy": "sandbox; default-src 'none'"},
    )


@app.get("/api/public/files/{fid}")
def public_file(fid: str, db=Depends(db_session)):
    file = db.get(File, fid)
    config = cfg(db)
    allowed = False
    if file:
        if file.purpose == "template":
            allowed = (
                config["modules"]["disclosure"] and config["disclosure_pdf"] == fid
            )
        elif file.purpose == "brand":
            allowed = any(
                config.get(k, "").endswith(fid)
                for k in ["logo", "favicon", "hero_image", "approach_image"]
            )
        elif (
            file.purpose == "image"
            and file.property_id
            and config["modules"]["properties"]
        ):
            prop = db.get(Property, file.property_id)
            allowed = (
                prop
                and prop.status in ["published", "reserved"]
                and any(i.get("id") == fid for i in prop.data["images"])
            )
    if not allowed:
        raise HTTPException(404, "Datei nicht verfügbar")
    return FileResponse(
        DATA / "files" / fid,
        media_type=file.mime,
        filename=file.name,
        content_disposition_type="inline"
        if file.mime.startswith("image/")
        else "attachment",
        headers={"Content-Security-Policy": "sandbox; default-src 'none'"},
    )


@app.post("/api/public/disclosure-return", status_code=202)
async def disclosure_return(
    request: Request,
    file: UploadFile,
    reference: int = Form(...),
    email: str = Form(...),
    return_code: str = Form(...),
    consent: bool = Form(...),
    db=Depends(db_session),
):
    module(db, "disclosure")
    config = cfg(db)
    if not config["disclosure_returns"]:
        raise HTTPException(404, "Rückgabe deaktiviert")
    inquiry = db.get(Inquiry, reference)
    if (
        not consent
        or not inquiry
        or not secrets.compare_digest(inquiry.data["email"].lower(), email.lower())
        or not secrets.compare_digest(
            inquiry.data.get("return_token_hash", ""), digest(return_code)
        )
    ):
        raise HTTPException(
            422,
            "Zuordnung nicht möglich. Anfragekennung, E-Mail und Rückgabecode prüfen.",
        )
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Maximal 10 MB pro Datei")
    await file.seek(0)
    fingerprint = hashlib.sha256(content).hexdigest()
    key = "pdf:" + digest(str(reference) + return_code + fingerprint)
    if db.get(Submission, key):
        return {
            "accepted": True,
            "message": "Dieses Dokument wurde bereits privat angenommen.",
        }
    limit(request, "documents", 3, 3600)
    db.add(Submission(key=key, fingerprint=fingerprint, inquiry_id=inquiry.id))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return {
            "accepted": True,
            "message": "Dieses Dokument wurde bereits privat angenommen.",
        }
    stored = await store_file(
        file, "return", db, inquiry.property_id, inquiry.id, commit=False
    )
    audit_row = Audit(
        actor="Öffentliche Rückgabe",
        action=f"Dokument zu Anfrage {reference} eingegangen",
    )
    db.add(audit_row)
    targets = config["forms"].get("disclosure", config["forms"][inquiry.kind])
    notification = {
        "kind": "disclosure_return",
        "file_id": stored["id"],
        "inquiry_id": inquiry.id,
        "property_id": inquiry.property_id,
        "message": "Neue private Unterlage eingegangen. Bitte im geschützten Adminbereich prüfen.",
        "email": inquiry.data["email"],
    }
    for channel in ["email", "telegram"]:
        if config["modules"][channel] and targets[channel]:
            db.add(
                Delivery(inquiry_id=inquiry.id, channel=channel, payload=notification)
            )
            if channel == "email" and integration(db, "email").get("confirmation"):
                db.add(
                    Delivery(
                        inquiry_id=inquiry.id,
                        channel="confirmation",
                        payload=notification,
                    )
                )
    try:
        db.commit()
    except Exception:
        db.rollback()
        (DATA / "files" / stored["id"]).unlink(missing_ok=True)
        raise HTTPException(
            503, "Dokument konnte noch nicht angenommen werden. Bitte erneut versuchen."
        )
    return {
        "accepted": True,
        "message": "Dokument privat gespeichert. Benachrichtigungen werden verarbeitet.",
    }


class EventInput(BaseModel):
    kind: Literal["pageview", "property_view", "inquiry_click"]
    path: str = Field(max_length=200, pattern=r"^/[a-zA-Z0-9/_-]*$")


@app.post("/api/public/events", status_code=202)
def event(data: EventInput, request: Request, db=Depends(db_session)):
    module(db, "analytics")
    limit(request, "events", 120, 60)
    db.add(Event(**data.model_dump()))
    db.commit()
    return {"accepted": True}


@app.get("/api/admin/dashboard")
def dashboard(user=Depends(current), db=Depends(db_session)):
    count = (
        lambda model, *where: db.scalar(
            select(func.count()).select_from(model).where(*where)
        )
        or 0
    )
    stats = {
        "new_inquiries": count(
            Inquiry, Inquiry.retained == True, Inquiry.status == "new"
        ),
        "inquiries": count(Inquiry, Inquiry.retained == True),
        "published": count(Property, Property.status.in_(["published", "reserved"])),
        "delivery_errors": count(Delivery, Delivery.status == "failed"),
    }
    stats["events"] = (
        {
            kind: count(Event, Event.kind == kind)
            for kind in ["pageview", "property_view", "inquiry_click", "submission"]
        }
        if cfg(db)["modules"]["analytics"]
        else None
    )
    stats["by_property"] = [
        {"property_id": pid, "count": n}
        for pid, n in db.execute(
            select(Inquiry.property_id, func.count())
            .where(Inquiry.retained == True)
            .group_by(Inquiry.property_id)
        )
    ]
    form_expression = func.coalesce(Inquiry.data["form_id"].as_string(), Inquiry.kind)
    stats["by_form"] = [
        {"kind": kind, "count": n}
        for kind, n in db.execute(
            select(form_expression, func.count())
            .where(Inquiry.retained == True)
            .group_by(form_expression)
        )
    ]
    stats["daily"] = [
        {"date": str(d), "count": n}
        for d, n in db.execute(
            select(func.date(Inquiry.created), func.count())
            .where(
                Inquiry.retained == True, Inquiry.created >= now() - timedelta(days=30)
            )
            .group_by(func.date(Inquiry.created))
            .order_by(func.date(Inquiry.created))
        )
    ]
    stats["recent"] = [
        inquiry_dict(r)
        for r in db.scalars(
            select(Inquiry)
            .where(Inquiry.retained == True)
            .order_by(Inquiry.id.desc())
            .limit(5)
        )
    ]
    return stats


@app.get("/api/admin/audit")
def audit_log(user=Depends(admin), db=Depends(db_session)):
    return [
        {"actor": r.actor, "action": r.action, "created": r.created.isoformat()}
        for r in db.scalars(select(Audit).order_by(Audit.id.desc()).limit(100))
    ]


@app.get("/api/admin/templates")
def templates(user=Depends(current), db=Depends(db_session)):
    return library(db)


@app.post("/api/admin/templates/validate")
def validate_manifest(data: Manifest, user=Depends(admin)):
    return {
        "valid": True,
        "manifest": data,
        "message": "Manifest kompatibel. Es wird ausschließlich der registrierte Adapter verwendet.",
    }


@app.post("/api/admin/templates/import", status_code=201)
def import_template(data: Manifest, user=Depends(admin), db=Depends(db_session)):
    if any(m["id"] == data.id for m in library(db)):
        raise HTTPException(409, "Diese Template-ID ist bereits vorhanden")
    db.add(Setting(key="template_" + data.id, value=data.model_dump()))
    audit(db, user, "Template-Manifest importiert: " + data.id)
    db.commit()
    return {
        "imported": True,
        "manifest": data,
        "message": "Template importiert und im Baukasten auswählbar. Fremder Code wurde nicht ausgeführt.",
    }


@app.get("/api/admin/builder/prompt")
def frontend_prompt(user=Depends(admin), db=Depends(db_session)):
    return {"prompt": prompt(db.get(Setting, "draft").value)}


@app.get("/api/admin/builder/reference")
def frontend_reference(user=Depends(admin), db=Depends(db_session)):
    return Response(
        reference_zip(db.get(Setting, "draft").value, app.openapi()),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="Raumwerk-KI-Frontend.zip"'
        },
    )


@app.get("/api/admin/builder/imprint")
def frontend_imprint(user=Depends(admin), db=Depends(db_session)):
    return {"text": imprint(db.get(Setting, "draft").value)}


@app.get("/api/admin/builder/check")
def frontend_check(user=Depends(admin), db=Depends(db_session)):
    return check_config(db, db.get(Setting, "draft").value)


async def design_upload(file):
    data = await file.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "Designpaket maximal 10 MB")
    return parse_design(data, file.filename or "manifest.json")


@app.post("/api/admin/builder/design/validate")
async def check_design(file: UploadFile, user=Depends(admin), db=Depends(db_session)):
    m = await design_upload(file)
    available = not any(x["id"] == m.id for x in library(db))
    return {
        "valid": True,
        "available": available,
        "manifest": m,
        "message": "Seiten, Aktionen und Theme geprüft. Quellcode im Referenzordner wird nicht ausgeführt."
        if available
        else "Diese ID ist bereits vorhanden. Die KI muss eine neue ID vergeben.",
    }


@app.post("/api/admin/builder/design/import", status_code=201)
async def install_design(file: UploadFile, user=Depends(admin), db=Depends(db_session)):
    m = await design_upload(file)
    if any(x["id"] == m.id for x in library(db)):
        raise HTTPException(409, "Diese Frontend-ID ist bereits vorhanden")
    c = Config.model_validate(db.get(Setting, "draft").value)
    c.template = m.id
    if m.theme:
        c.primary, c.accent, c.font = m.theme.primary, m.theme.accent, m.theme.font
        c.frontend_theme = type(c.frontend_theme).model_validate(
            m.theme.model_dump(exclude={"primary", "accent", "font"})
        )
    db.add(Setting(key="template_" + m.id, value=m.model_dump()))
    db.get(Setting, "draft").value = c.model_dump()
    add_revision(db, user, c.model_dump(), "import", "Frontend importiert: " + m.name)
    audit(db, user, "Frontend-Datenpaket importiert: " + m.id)
    db.commit()
    return {
        "config": presentation(db, c.model_dump()),
        "message": "Frontend als Entwurf importiert. Vorschau prüfen, danach veröffentlichen.",
    }


class DeploymentPlan(BaseModel):
    domain: str = ""


def validate_domain(value):
    try:
        return domain_name(value) if value else ""
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/api/admin/builder/deployment")
def deployment_plan(data: DeploymentPlan, user=Depends(admin)):
    domain = validate_domain(data.domain)
    if not domain:
        raise HTTPException(422, "Bitte deine Domain eintragen")
    return {
        "domain": domain,
        "url": "https://" + domain,
        "admin_url": "https://" + domain + "/admin",
        "steps": [
            "VPS mit Ubuntu 24.04 LTS, mindestens 2 CPU, 4 GB RAM und Docker Compose bereitstellen.",
            f"A-Eintrag für {domain} auf die öffentliche IPv4 des VPS setzen. AAAA nur bei funktionierendem IPv6.",
            "TCP 80 und 443 freigeben. SSH-Zugang absichern. Keine Datenbankports öffnen.",
            "Projektpaket herunterladen, auf den VPS kopieren und entpacken.",
            "Im Ordner Raumwerk: bash LIVE-STARTEN.sh. Domain bestätigen, Administrator anlegen.",
            "Caddy richtet HTTPS automatisch ein, sobald DNS und Ports stimmen. Website und /admin prüfen.",
            "Integrationen neu einrichten, Formrouting veröffentlichen und einen bewussten Test durchführen. Backups einrichten.",
        ],
        "command": "bash LIVE-STARTEN.sh",
        "note": "Dein VPS ist das Hosting. Domain und VPS müssen vorhanden sein; dieses Formular bestellt keinen Server und ändert kein DNS.",
    }


@app.post("/api/admin/builder/project")
def project_export(data: DeploymentPlan, user=Depends(admin), db=Depends(db_session)):
    domain = validate_domain(data.domain)
    try:
        path = export_project(db, domain)
    except ValueError:
        raise HTTPException(
            422,
            "Projekt nicht exportierbar. Verknüpfte Medien, PDF-Modul und gespeicherten Entwurf prüfen.",
        )
    audit(db, user, "Projektpaket exportiert (ohne Zugänge und Anfragen)")
    db.commit()
    return FileResponse(
        path,
        media_type="application/zip",
        filename="Raumwerk-Projekt.zip",
        background=BackgroundTask(Path(path).unlink, missing_ok=True),
    )


@app.get("/api/admin/builder/versions")
def config_versions(user=Depends(admin), db=Depends(db_session)):
    current_config = Config.model_validate(db.get(Setting, "draft").value).model_dump()
    return [
        {
            "id": r.id,
            "label": r.label,
            "kind": r.kind,
            "actor": r.actor,
            "created": r.created,
            "changed_fields": [
                k for k in current_config if current_config[k] != r.config.get(k)
            ],
        }
        for r in db.scalars(select(Revision).order_by(Revision.id.desc()).limit(100))
    ]


@app.get("/api/admin/builder/versions/{rid}")
def config_version(rid: int, user=Depends(admin), db=Depends(db_session)):
    r = db.get(Revision, rid)
    if not r:
        raise HTTPException(404, "Version nicht gefunden")
    c = Config.model_validate(db.get(Setting, "draft").value).model_dump()
    saved = Config.model_validate(r.config).model_dump()
    return {
        "id": r.id,
        "label": r.label,
        "changes": [
            {"field": k, "current": c[k], "saved": saved[k]}
            for k in c
            if c[k] != saved[k]
        ],
    }


@app.post("/api/admin/builder/versions/{rid}/restore")
def restore_config_version(rid: int, user=Depends(admin), db=Depends(db_session)):
    r = db.get(Revision, rid)
    if not r:
        raise HTTPException(404, "Version nicht gefunden")
    config = Config.model_validate(r.config).model_dump()
    check_config(db, config)
    # Preserve both sides: rollback restores a draft, never silently publishes.
    add_revision(
        db, user, db.get(Setting, "draft").value, "checkpoint", "Vor Wiederherstellung"
    )
    db.get(Setting, "draft").value = config
    add_revision(db, user, config, "restore", "Wiederhergestellt: Version " + str(rid))
    audit(db, user, "Konfiguration als Entwurf wiederhergestellt: " + str(rid))
    db.commit()
    return presentation(db, config)
