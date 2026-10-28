"""Read-only operating checks. Never returns credentials or private file names."""

import os
import shutil
from urllib.parse import urlsplit
from sqlalchemy import select, func
from .db import DATA, Setting, Delivery, File, Property
from .config import Config
from .builder import check_config
from .delivery import integration, worker_status
from .version import VERSION


def public_origin():
    # Only server configuration is trusted, never incoming Host / proxy headers.
    value = os.getenv("PUBLIC_ORIGIN", "http://localhost:3000").split(",")[0].rstrip("/")
    try:
        url = urlsplit(value)
        if url.scheme in {"http", "https"} and url.hostname and not url.username and not url.password and not url.query and not url.fragment and url.path in {"", "/"}:
            return value
    except ValueError:
        pass
    return "http://localhost:3000"


def local_installation():
    hostname = urlsplit(public_origin()).hostname
    return os.getenv("RAUMWERK_DESKTOP") == "1" or hostname in {"localhost", "127.0.0.1", "::1"}


def operating_status(db):
    config = Config.model_validate(db.get(Setting, "published").value)
    checks = check_config(db, config.model_dump())["checks"]

    def add(identity, title, ok, detail, level="error", link="settings"):
        checks.append(dict(id=identity, title=title, ok=bool(ok), detail=detail, level=level, link=link))

    for check in checks:
        check["link"] = "company" if check["id"] in {"legal", "company"} else "studio"
    # The builder's export-specific routing advice is replaced with actual live routing.
    checks[:] = [c for c in checks if c["id"] != "contact"]
    local = local_installation()
    worker = worker_status()
    add("worker", "Zustellung und automatische Bereinigung", worker["healthy"],
        "Der Hintergrunddienst ist aktiv." if worker["healthy"] else "Hintergrunddienst ist deaktiviert oder meldet Fehler. Anfragen bleiben gespeichert; externe Zustellungen und Bereinigung prüfen.", link="integrations")
    for channel, label in [("email", "E-Mail"), ("telegram", "Telegram")]:
        selected = config.modules.model_dump().get(channel) and any(getattr(f, channel) for f in config.forms.values())
        if selected:
            try:
                data = integration(db, channel)
                complete = all(data.get(k) for k in (["host", "sender", "recipients"] if channel == "email" else ["token", "chat_id"]))
            except Exception:
                complete = False
            add(channel, label + " eingerichtet", complete, "Verbindungsdaten vorhanden. Ein erfolgreicher Testversand muss am Ziel geprüft werden.", link="integrations")
    missing = sum(not (DATA / "files" / f.id).is_file() for f in db.scalars(select(File)))
    add("files", "Gespeicherte Medien vollständig", not missing, f"{missing} fehlende Datei(en). Bei Fehlern eine vollständige Sicherung wiederherstellen.")
    free = shutil.disk_usage(DATA).free
    add("storage", "Freier Datenspeicher", free >= 512 * 1024**2, f"{free // 1024**2} MB frei; mindestens 512 MB empfohlen.", "warning")
    add("https", "HTTPS für öffentliche Website", local or public_origin().startswith("https://"), "Für eine öffentliche Website Domain und HTTPS einrichten.", link="deployment")
    failed = db.scalar(select(func.count()).select_from(Delivery).where(Delivery.status == "failed"))
    pending = db.scalar(select(func.count()).select_from(Delivery).where(Delivery.status.in_(["pending", "retry"])))
    add("outbox", "Keine fehlgeschlagenen Zustellungen", not failed, f"{pending} wartend, {failed} fehlgeschlagen. Fehlgeschlagene Aufträge unter Integrationen bearbeiten.", link="integrations")
    return dict(version=VERSION, mode="local" if local else "server", origin=public_origin(), worker=worker,
                published_properties=db.scalar(select(func.count()).select_from(Property).where(Property.status.in_(["published", "reserved"]))),
                checks=checks, ready=all(c["ok"] for c in checks if c["level"] == "error"), pending=pending, failed=failed)


def search_index(db):
    """Public routes only, independent of pagination and imported site designs."""
    c = Config.model_validate(db.get(Setting, "published").value)
    paths = {"/", "/impressum", "/datenschutz"}
    for slug, enabled in [("immobilien", c.modules.properties), ("kontakt", c.modules.contact), ("selbstauskunft", c.modules.disclosure)]:
        if enabled:
            paths.add("/" + slug)
    paths.update("/" + p.slug for p in c.pages if p.enabled)
    if c.modules.properties:
        paths.update("/immobilien/" + slug for slug in db.scalars(select(Property.slug).where(Property.status.in_(["published", "reserved"]))))
    return dict(origin=public_origin(), local=local_installation(), paths=sorted(paths))
