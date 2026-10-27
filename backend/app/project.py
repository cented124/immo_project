"""Export an assembled installation and seed a fresh destination exactly once."""

import copy
import hashlib
import os
import secrets
import tempfile
import zipfile
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, func
from .db import Session, Setting, Property, File, User, DATA
from .config import Config, PropertyData
from .templates import Manifest, library
from .builder import add_sources, json_bytes, check_config


class SeedFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-f0-9]{32}$")
    name: str = Field(min_length=1, max_length=255)
    mime: Literal["image/webp", "application/pdf"]
    purpose: Literal["brand", "image", "template", "document"]
    property_id: int | None = None
    size: int = Field(ge=1, le=10 * 1024 * 1024)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class SeedProperty(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int = Field(gt=0)
    data: PropertyData


class ProjectSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1]
    export_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    draft: Config
    published: Config
    templates: list[Manifest]
    properties: list[SeedProperty]
    files: list[SeedFile]

    @model_validator(mode="after")
    def references(self):
        for rows, key in [
            (self.files, "id"),
            (self.properties, "id"),
            (self.templates, "id"),
        ]:
            if len({getattr(x, key) for x in rows}) != len(rows):
                raise ValueError("Doppelte IDs im Projekt")
        if len({p.data.slug for p in self.properties}) != len(self.properties):
            raise ValueError("Doppelte Immobilienpfade")
        files = {f.id: f for f in self.files}
        props = {p.id for p in self.properties}
        for f in self.files:
            if f.property_id is not None and f.property_id not in props:
                raise ValueError("Datei verweist auf unbekannte Immobilie")
            if (f.purpose in {"brand", "template"}) != (f.property_id is None):
                raise ValueError("Dateizuordnung ungültig")
            if f.mime != (
                "image/webp" if f.purpose in {"brand", "image"} else "application/pdf"
            ):
                raise ValueError("Dateityp und Zweck passen nicht zusammen")
        for c in [self.draft, self.published]:
            if c.template not in {m.id for m in self.templates}:
                raise ValueError("Frontend-Manifest fehlt")
            for key in ["logo", "favicon", "hero_image", "approach_image"]:
                v = getattr(c, key)
                if v.startswith("/api/"):
                    f = files.get(v.rsplit("/", 1)[-1])
                    if not f or f.purpose != "brand":
                        raise ValueError("Unternehmensdatei fehlt")
            if c.disclosure_pdf and (
                c.disclosure_pdf not in files
                or files[c.disclosure_pdf].purpose != "template"
            ):
                raise ValueError("PDF-Vorlage fehlt")
            if c.modules.disclosure and not c.disclosure_pdf:
                raise ValueError("Aktives PDF-Modul benötigt eine Vorlage")
            if (
                c.modules.email
                or c.modules.telegram
                or any(f.email or f.telegram for f in c.forms.values())
            ):
                raise ValueError("Zustellwege müssen am Ziel neu eingerichtet werden")
        for p in self.properties:
            for fid in [i["id"] for i in p.data.images] + p.data.documents:
                f = files.get(fid)
                purpose = "document" if fid in p.data.documents else "image"
                if not f or f.purpose != purpose or f.property_id != p.id:
                    raise ValueError("Immobilienmedien fehlen oder falsch zugeordnet")
        return self


def without_integrations(config):
    c = copy.deepcopy(config)
    c.pop("template_adapter", None)
    c["modules"]["email"] = c["modules"]["telegram"] = False
    for f in c["forms"].values():
        f.update(store=True, email=False, telegram=False)
    return c


def export_project(db, domain=""):
    configs = {
        key: without_integrations(db.get(Setting, key).value)
        for key in ["draft", "published"]
    }
    checks = check_config(db, configs["published"])
    if not checks["valid"]:
        raise ValueError(
            "Veröffentlichter Stand enthält fehlende Medien oder ein unvollständiges PDF-Modul"
        )
    properties = [
        dict(id=p.id, data=p.data)
        for p in db.scalars(select(Property).order_by(Property.id))
    ]
    fids = set()
    for c in configs.values():
        for key in ["logo", "favicon", "hero_image", "approach_image"]:
            if c[key].startswith("/api/"):
                fids.add(c[key].rsplit("/", 1)[-1])
        if c["disclosure_pdf"]:
            fids.add(c["disclosure_pdf"])
    for p in properties:
        fids.update(i["id"] for i in p["data"].get("images", []))
        fids.update(p["data"].get("documents", []))
    media = []
    for fid in sorted(fids):
        f = db.get(File, fid)
        if not f or f.purpose == "return" or not (DATA / "files" / f.id).is_file():
            raise ValueError(
                "Eine verknüpfte Mediendatei fehlt. Bitte Zuordnungen prüfen."
            )
        path = DATA / "files" / f.id
        media.append(
            dict(
                id=f.id,
                name=f.name,
                mime=f.mime,
                purpose=f.purpose,
                property_id=f.property_id,
                size=path.stat().st_size,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    seed = ProjectSeed(
        version=1,
        export_id=secrets.token_hex(16),
        **configs,
        properties=properties,
        files=media,
        templates=library(db),
    )
    fd, filename = tempfile.mkstemp(prefix="raumwerk-projekt-", suffix=".zip")
    os.close(fd)
    try:
        with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as z:
            add_sources(z, "Raumwerk/")
            z.writestr("Raumwerk/project/project.json", json_bytes(seed.model_dump()))
            z.writestr("Raumwerk/deployment.json", json_bytes({"domain": domain}))
            for f in media:
                z.write(DATA / "files" / f["id"], "Raumwerk/project/files/" + f["id"])
            z.writestr(
                "Raumwerk/EXPORT-LESEN.md",
                "# Dein fertig konfiguriertes Projekt\n\nWebsite und Admin sind enthalten. Windows: STARTEN.cmd. VPS: siehe docs/DEPLOYMENT.md, dann bash LIVE-STARTEN.sh. Veröffentlichten Stand und Entwurf sowie alle Immobilien inklusive Entwürfen und zugeordneten Medien enthalten. Auch interne Objekt-PDFs sind enthalten; Paket vertraulich aufbewahren. Keine Benutzer, Anfragen, ausgefüllten Selbstauskünfte, Zustelljobs, Statistik oder Zugangsdaten enthalten. Neue Administratoren und Integrationen am Ziel einrichten. Kontakte landen bis dahin im Adminbereich. Der Datenimport erfolgt nur einmal in einer frischen Instanz; erneuter Start überschreibt nichts.\n",
            )
        return filename
    except Exception:
        Path(filename).unlink(missing_ok=True)
        raise


def import_project(path):
    path = Path(path)
    if not path.is_file():
        return False
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError("Projektdatei zu groß")
    seed = ProjectSeed.model_validate_json(path.read_bytes())
    with Session() as db:
        marker = db.get(Setting, "project_seed")
        if marker:
            if marker.value["export_id"] != seed.export_id:
                raise ValueError(
                    "Diese Instanz hat bereits ein anderes Projekt importiert. Keine Daten wurden überschrieben."
                )
            return False
        if any(
            db.scalar(select(func.count()).select_from(model))
            for model in [Property, File, User]
        ):
            raise ValueError(
                "Projektimport ist ausschließlich in eine frische Instanz ohne Benutzer und Inhalte möglich."
            )
        default = Config().model_dump()
        if any(
            row.value != default
            for row in db.scalars(
                select(Setting).where(Setting.key.in_(["draft", "published"]))
            )
        ):
            raise ValueError(
                "Vorhandene Konfiguration bleibt erhalten; für Import eine frische Instanz verwenden."
            )
        # Verify all bytes before touching destination database or filesystem.
        sources = []
        for f in seed.files:
            source = path.parent / "files" / f.id
            if (
                source.is_symlink()
                or not source.is_file()
                or source.stat().st_size != f.size
            ):
                raise ValueError("Mediendatei fehlt oder hat eine falsche Größe")
            raw = source.read_bytes()
            if hashlib.sha256(raw).hexdigest() != f.sha256:
                raise ValueError("Prüfsumme einer Mediendatei stimmt nicht")
            if f.mime == "application/pdf":
                if not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-2048:]:
                    raise ValueError("Ungültige PDF-Datei")
            else:
                from PIL import Image

                with Image.open(source) as img:
                    if img.format != "WEBP" or max(img.size) > 2400:
                        raise ValueError("Ungültige Bilddatei")
                    img.verify()
            sources.append((f, raw))
        target = DATA / "files"
        target.mkdir(mode=0o700, exist_ok=True)
        created = []
        try:
            for p in seed.properties:
                db.add(
                    Property(
                        id=p.id,
                        slug=p.data.slug,
                        status=p.data.status,
                        data=p.data.model_dump(),
                    )
                )
            db.flush()
            for f, raw in sources:
                destination = target / f.id
                fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                created.append(destination)
                with os.fdopen(fd, "wb") as handle:
                    handle.write(raw)
                db.add(File(**f.model_dump(exclude={"sha256"})))
            for key, c in [("draft", seed.draft), ("published", seed.published)]:
                db.merge(Setting(key=key, value=c.model_dump()))
            for m in seed.templates:
                if m.id not in {"atelier", "editorial"}:
                    db.merge(Setting(key="template_" + m.id, value=m.model_dump()))
            db.add(Setting(key="project_seed", value={"export_id": seed.export_id}))
            # Explicit IDs require resetting PostgreSQL's next generated identity.
            if db.bind.dialect.name == "postgresql" and seed.properties:
                from sqlalchemy import text

                db.execute(
                    text(
                        "SELECT setval(pg_get_serial_sequence('properties','id'), (SELECT MAX(id) FROM properties))"
                    )
                )
            db.commit()
        except Exception:
            db.rollback()
            for p in created:
                p.unlink(missing_ok=True)
            raise
    return True
