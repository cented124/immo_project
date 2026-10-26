"""Durable outbox. Exactly one worker claims rows using FOR UPDATE SKIP LOCKED.
SMTP/Telegram cannot promise exactly-once delivery after ambiguous network failures.
"""

import json, os, smtplib, ssl
from email.message import EmailMessage
from datetime import timedelta
import httpx
from sqlalchemy import select, delete
from .db import (
    Session,
    Setting,
    Inquiry,
    Delivery,
    File,
    Event,
    Submission,
    LoginSession,
    now,
    DATA,
)
from .security import decrypt


class TemporaryDeliveryError(RuntimeError):
    pass


def integration(db, channel):
    row = db.get(Setting, "integration_" + channel)
    return json.loads(decrypt(row.value["encrypted"])) if row else {}


def send_email(settings, data, test=False, confirmation=False):
    required = ["host", "port", "sender", "recipients", "tls"]
    if any(not settings.get(k) for k in required):
        raise ValueError("SMTP-Konfiguration unvollständig")
    msg = EmailMessage()
    msg["From"] = f"{settings.get('sender_name', 'Immobilien')} <{settings['sender']}>"
    msg["To"] = data["email"] if confirmation else ", ".join(settings["recipients"])
    msg["Subject"] = (
        "Ihre Anfrage ist eingegangen"
        if confirmation
        else (
            "Verbindungstest" if test else f"Neue {data.get('kind', 'Kontaktanfrage')}"
        )
    )
    if data.get("email") and not confirmation:
        msg["Reply-To"] = data["email"]
    if confirmation:
        msg.set_content(
            "Ihre Unterlage wurde privat gespeichert. Wir prüfen diese persönlich."
            if data.get("kind") == "disclosure_return"
            else "Vielen Dank. Ihre Anfrage wurde angenommen und wird persönlich bearbeitet."
        )
    else:
        msg.set_content(
            "Testnachricht: SMTP funktioniert."
            if test
            else "\n".join(
                f"{k}: {data[k]}"
                for k in [
                    "kind",
                    "first_name",
                    "last_name",
                    "email",
                    "phone",
                    "subject",
                    "message",
                    "property_id",
                    "consent_at",
                ]
                if data.get(k)
            )
        )
    context = ssl.create_default_context()
    client_type = smtplib.SMTP_SSL if settings["tls"] == "ssl" else smtplib.SMTP
    kwargs = {"context": context} if settings["tls"] == "ssl" else {}
    with client_type(
        settings["host"], int(settings["port"]), timeout=15, **kwargs
    ) as smtp:
        if settings["tls"] == "starttls":
            smtp.starttls(context=context)
        if settings.get("username"):
            smtp.login(settings["username"], settings.get("password", ""))
        refused = smtp.send_message(msg)
        if refused:
            raise ValueError(
                "Mindestens eine Empfängeradresse wurde abgelehnt. Empfänger und Zustellprotokoll prüfen."
            )


def send_telegram(settings, data, test=False):
    if not settings.get("token") or not settings.get("chat_id"):
        raise ValueError("Bot-Token und Chat-ID fehlen")
    fields = ["kind", "property_id"] + (
        ["first_name", "last_name", "email", "phone", "message"]
        if settings.get("include_details", False)
        else []
    )
    text = (
        "Testnachricht: Telegram funktioniert."
        if test
        else (
            "Private Unterlage im Adminbereich eingegangen\n"
            if data.get("kind") == "disclosure_return"
            else "Neue Anfrage im Adminbereich\n"
        )
        + "\n".join(f"{k}: {str(data[k])[:1500]}" for k in fields if data.get(k))
    )
    base = os.getenv("TELEGRAM_API_BASE", "https://api.telegram.org")
    response = httpx.post(
        f"{base}/bot{settings['token']}/sendMessage",
        json={"chat_id": settings["chat_id"], "text": text[:4000]},
        timeout=15,
    )
    if response.status_code == 429 or response.status_code >= 500:
        raise TemporaryDeliveryError(
            "Telegram ist vorübergehend nicht erreichbar oder begrenzt Anfragen."
        )
    if response.status_code != 200 or not response.json().get("ok"):
        raise ValueError(
            "Telegram hat die Nachricht abgelehnt. Bot-Start und Chat-ID prüfen."
        )


def safe_error(error):
    if isinstance(error, TemporaryDeliveryError):
        return str(error)
    if isinstance(error, smtplib.SMTPAuthenticationError):
        return "SMTP-Anmeldung abgelehnt"
    if isinstance(error, ValueError):
        return str(error)[:150]
    if isinstance(error, ssl.SSLError):
        return "TLS-Zertifikat konnte nicht verifiziert werden"
    if isinstance(error, ConnectionRefusedError):
        return "Der Mailserver lehnt die Netzwerkverbindung ab. Host, Port und ausgehenden Netzwerkzugriff prüfen."
    if isinstance(error, TimeoutError):
        return "Zeitüberschreitung beim Verbindungsaufbau zum Zielserver."
    return "Zustellung fehlgeschlagen. Verbindung und Einstellungen prüfen."


def process_once():
    with Session() as db:
        row = db.scalar(
            select(Delivery)
            .where(
                Delivery.status.in_(["pending", "retry"]),
                Delivery.next_attempt <= now(),
            )
            .order_by(Delivery.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if not row:
            return False
        inquiry = db.get(Inquiry, row.inquiry_id)
        config = db.get(Setting, "published").value
        # Disabling a module also blocks queued jobs until explicitly enabled again.
        channel = "email" if row.channel == "confirmation" else row.channel
        if not config["modules"].get(channel):
            row.status = "failed"
            row.error = "Zustellmodul deaktiviert"
            db.commit()
            return True
        row.attempts += 1
        try:
            settings = integration(db, channel)
            data = {
                **inquiry.data,
                "kind": inquiry.kind,
                "property_id": inquiry.property_id,
            }
            if channel == "email":
                send_email(
                    settings,
                    row.payload or data,
                    confirmation=row.channel == "confirmation",
                )
            else:
                send_telegram(settings, row.payload or data)
            row.status = "sent"
            row.error = ""
        except Exception as e:
            row.error = safe_error(e)
            permanent = isinstance(e, ValueError) or (
                isinstance(e, smtplib.SMTPResponseException) and e.smtp_code >= 500
            )
            if isinstance(e, smtplib.SMTPRecipientsRefused):
                permanent = any(code >= 500 for code, _ in e.recipients.values())
            row.status = "failed" if row.attempts >= 4 or permanent else "retry"
            row.next_attempt = now() + timedelta(seconds=30 * 2**row.attempts)
        db.commit()
    return True


def purge():
    with Session() as db:
        days = db.get(Setting, "published").value["retention_days"]
        rows = db.scalars(
            select(Inquiry).where(
                (
                    (Inquiry.retained == False)
                    & (Inquiry.created < now() - timedelta(hours=24))
                )
                | (Inquiry.created < now() - timedelta(days=days))
            )
        ).all()
        for row in rows:
            for file in db.scalars(select(File).where(File.inquiry_id == row.id)).all():
                (DATA / "files" / file.id).unlink(missing_ok=True)
                db.delete(file)
            db.execute(delete(Delivery).where(Delivery.inquiry_id == row.id))
            db.delete(row)
        db.execute(
            delete(Submission).where(Submission.created < now() - timedelta(hours=24))
        )
        db.execute(delete(Event).where(Event.created < now() - timedelta(days=days)))
        db.execute(delete(LoginSession).where(LoginSession.expires < now()))
        db.commit()


def worker(stop):
    ticks = 0
    while not stop.wait(2):
        try:
            process_once()
            ticks += 1
            if ticks % 30 == 0:
                purge()
        except Exception:
            # No request contents, credentials or provider URLs in logs.
            import logging

            logging.getLogger(__name__).warning(
                "Outbox: Datenbank vorübergehend nicht erreichbar"
            )
