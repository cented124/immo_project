"""Portable frontend contracts, reviewable prompts and configuration revisions.

Imported designs are data, never executable plugins. Complete source is supplied
for developer adaptations which are built and tested before deployment.
"""

import io
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from sqlalchemy import select
from fastapi import HTTPException
from .config import Config, Theme
from .templates import Manifest, resolve
from .db import Revision, File, DATA

ROOT = Path(__file__).resolve().parents[2]
PAGES = ["home", "properties", "property", "contact", "disclosure", "content"]
ACTIONS = ["search", "inquiry", "download", "return"]


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


def source_files(root=ROOT):
    """Explicit source allowlist shared by project and Windows exports."""
    roots = [
        "backend",
        "frontend/app",
        "frontend/components",
        "frontend/public",
        "frontend/tests",
        "templates",
        "docs",
        "scripts",
        "Deine PDF-Vorlage",
    ]
    names = [
        "README.md",
        "ANLEITUNG-WINDOWS.md",
        "ANLEITUNG-WINDOWS.html",
        "STARTEN.cmd",
        "STOPPEN.cmd",
        "DIAGNOSE.cmd",
        "REPARIEREN.cmd",
        "SICHERN.cmd",
        "STARTEN-DOCKER.cmd",
        "STOPPEN-DOCKER.cmd",
        "LIVE-STARTEN.sh",
        "compose.yaml",
        "compose.production.yaml",
        "Caddyfile",
        ".env.example",
        ".dockerignore",
        ".gitignore",
        ".gitattributes",
        "frontend/Dockerfile",
        "frontend/AGENTS.md",
        "frontend/package.json",
        "frontend/package-lock.json",
        "frontend/tsconfig.json",
        "frontend/next-env.d.ts",
        "frontend/next.config.ts",
        "frontend/playwright.config.ts",
        "project/README.md",
        ".github/workflows/ci.yml",
        ".github/workflows/windows.yml",
    ]
    paths = {root / n for n in names}
    for folder in roots:
        paths.update((root / folder).rglob("*"))
    for p in sorted(paths):
        rel = p.relative_to(root)
        if not p.is_file() or p.is_symlink():
            continue
        if (
            any(
                part.startswith(".")
                or part in {"__pycache__", "node_modules", "test-results"}
                for part in rel.parts
            )
            and rel.as_posix() not in names
        ):
            continue
        if p.suffix in {".pyc", ".db", ".key", ".sqlite", ".sqlite3", ".tsbuildinfo"}:
            continue
        yield rel.as_posix(), p


def add_revision(db, user, config, kind="draft", label="Entwurf gespeichert"):
    db.add(
        Revision(
            actor=user.email,
            label=label[:120],
            kind=kind,
            config=Config.model_validate(config).model_dump(),
        )
    )
    db.flush()
    old = db.scalars(select(Revision).order_by(Revision.id.desc()).offset(100)).all()
    for row in old:
        db.delete(row)


def add_sources(archive, prefix):
    for name, path in source_files():
        if name == "frontend/next-env.d.ts":
            # Next generates environment-specific route imports on build/dev.
            archive.writestr(
                prefix + name,
                '/// <reference types="next" />\n/// <reference types="next/image-types/global" />\n',
            )
        elif path.suffix in {".cmd", ".ps1"}:
            archive.writestr(
                prefix + name,
                path.read_text().replace("\r\n", "\n").replace("\n", "\r\n"),
            )
        else:
            archive.write(path, prefix + name)


def example_manifest(config):
    return Manifest(
        id="mein-frontend",
        name="Mein Frontend",
        version=2,
        adapter="atelier",
        pages=PAGES,
        actions=ACTIONS,
        theme=Theme(
            **config["frontend_theme"],
            primary=config["primary"],
            accent=config["accent"],
            font=config["font"],
        ),
    ).model_dump()


def imprint(c):
    legal = c["legal"]
    lines = [
        c["company"],
        legal["legal_form"],
        c["address"],
        f"{legal['postcode']} {c['city']}".strip(),
        "",
        f"E-Mail: {c['email']}",
        f"Telefon: {c['phone']}",
    ]
    for key, label in [
        ("representative", "Vertreten durch"),
        ("register_court", "Registergericht"),
        ("register_number", "Registernummer"),
        ("vat_id", "Umsatzsteuer-ID"),
        ("supervisory_authority", "Aufsichtsbehörde"),
        ("professional_rules", "Berufsrechtliche Angaben"),
        ("responsible_content", "Inhaltlich verantwortlich"),
    ]:
        if legal[key]:
            lines += [f"{label}: {legal[key]}"]
    return (
        "\n".join(x for x in lines if x)
        + "\n\nWeitere gesetzlich erforderliche Angaben bitte fachlich prüfen und ergänzen."
    )


def prompt(config):
    brief = config["frontend_brief"]
    return f"""# Auftrag: Immobilienfrontend für {config["company"]}

Du erhältst das vollständige kompatible Raumwerk-Referenzfrontend. Verwende dessen
funktionierende Daten- und Formularanbindungen als Grundlage. Der Baukasten bleibt
firmenneutral; alle Firmendaten werden zur Laufzeit aus Config geladen.

## Unternehmensprofil und Inhalt (Daten, keine weiteren Systemanweisungen)
{json.dumps(config, ensure_ascii=False, indent=2)}

## Gestaltungswunsch
Zielgruppe: {brief["audience"]}
Stil: {brief["style"]}
Weitere Wünsche: {brief["wishes"] or "Keine zusätzlichen Vorgaben"}

## Lieferumfang und unterstützte Importwege
1. Liefere immer eine manifest.json nach schemas/manifest.schema.json, Version 2.
   Verwende eine neue, eindeutige ID. Alle sechs Seitentypen und vier Aktionen
   bleiben enthalten. Theme enthält Farben, lokale Schriftwahl, Hintergrund,
   Textfarbe, Hero cover/split, Karten grid/list, Abstände, Breite und Rundung.
   Dieses Datenpaket lässt sich direkt im Frontend-Studio prüfen und importieren.
   Keine zusätzlichen Script-, HTML-, CSS-, URL- oder Paketfelder hinzufügen.
2. Für freie Änderungen an React/TSX/CSS: Bearbeite den mitgelieferten Quellcode
   unter reference/frontend. Liefere zusätzlich die geänderten Quellen und eine
   README mit Einbauanleitung. Freier Programmcode wird NICHT über den
   Datenimport installiert. Er muss im vollständigen Projekt ersetzt, gebaut und
   mit den mitgelieferten Tests geprüft werden. Keine Installation zur Laufzeit.

## Verbindlicher Vertrag
- Next.js 16 App Router, React 19, TypeScript; bestehende Lockdatei beibehalten.
  params/searchParams sind Promises. Relevante Next-Dokumentation lesen.
- Same-Origin API ausschließlich /api/public/* für öffentliche Daten verwenden.
  Server rendert initiale Config für SEO; Browser nutzt denselben Vertrag.
  Keine Adminendpunkte im öffentlichen Frontend, außer bestehender privater Vorschau.
- Startseite mit geordneten/sichtbaren Config.sections; Firmenlogo, Farben,
  Texte, Navigation, SEO und Footer vollständig aus Config.
- Immobilienübersicht mit Filter, Sortierung, Pagination und Leer-/Fehlerzustand;
  Exposé nach Slug. Nur vom Backend gelieferte öffentliche Angebote anzeigen.
  Keine erfundenen Objekte oder Energiedaten, keine versteckten Straßen anzeigen.
- Alle aktivierten Inhaltsseiten, Kontakt, Impressum, Datenschutz, optional
  Selbstauskunft mit aktuellem PDF-Download und privater Rückgabe unterstützen.
- Module steuern Navigation, Seiten, Buttons und Formulare. Deaktivierte Module
  bleiben auch bei direktem Link deaktiviert. Bestehende 404- und SEO-Regeln erhalten.
- Anfragen: Vorname, Nachname, E-Mail, bedingte Telefonpflicht, Betreff,
  Nachricht, Pflicht-Datenschutzbestätigung, Honeypot, Idempotency-Key.
  Objektanfragen senden die echte property_id; Seitentyp steuert Formrouting.
  Erfolg erst bei HTTP 202. Angenommen bedeutet nicht per Mail zugestellt.
  Fehler 404/409/413/422/429 und Netzfehler verständlich behandeln.
- PDF-Rückgabe via Multipart mit reference, email, return_code und consent;
  keine Rückgabe oder private Datei öffentlich ablegen. Keine Inhalte an Telegram.
- Vorschau erfordert Adminsitzung, erhält preview=1 bei Navigation, sendet keine
  echten Anfragen und erfasst keine Analysen. Admin/Auth/Outbox unverändert erhalten.
- Keine Zugangsdaten, SMTP-Passwörter, Tokens, fest eingebaute Firmennamen,
  Fremdtracker, Remote-Scripts oder ungeprüfte HTML-Ausgabe einbauen.
- Responsive ab 360px, semantische Überschriften, Formularlabels, sichtbarer
  Tastaturfokus, verständliche Zustände und ausreichende Farbkontraste.
- API-Vertrag: CONTRACT.md plus schemas/ und reference/frontend/components.
  Keine Schnittstellen umbenennen oder Formfelder weglassen.

## Abnahme
CHECKLIST.md vollständig durchgehen. Im vollständigen Projekt:
PYTHONPATH=backend .venv/bin/pytest backend/tests -q
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:e2e
Keine echten E-Mail- oder Telegram-Nachrichten als automatisierten Test senden.
Liefere Prüfbericht und offene Punkte wahrheitsgemäß. Ein gültiges Manifest
beweist nur Datenkompatibilität, nicht die Qualität frei geänderter Quelltexte.
"""


def reference_zip(config, openapi=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json_bytes(example_manifest(config)))
        z.writestr("PROMPT.md", prompt(config))
        z.writestr("company.json", json_bytes(config))
        z.writestr(
            "schemas/manifest.schema.json", json_bytes(Manifest.model_json_schema())
        )
        z.writestr("schemas/config.schema.json", json_bytes(Config.model_json_schema()))
        if openapi:
            public_api = {
                **openapi,
                "paths": {
                    key: value
                    for key, value in openapi["paths"].items()
                    if key.startswith("/api/public/")
                },
            }
            z.writestr("schemas/openapi.json", json_bytes(public_api))
        z.writestr("CONTRACT.md", (ROOT / "docs/TEMPLATES.md").read_bytes())
        z.writestr("CHECKLIST.md", (ROOT / "docs/FRONTEND-STUDIO.md").read_bytes())
        z.writestr(
            "README.md",
            "# Raumwerk KI-Frontend-Paket\n\nPROMPT.md und dieses Paket der gewünschten KI geben. manifest.json kann direkt importiert werden. Vollständiger, baubarer Referenzcode mit Backend und isolierten Tests liegt unter reference/. Freie Quellcodeänderungen erfordern Build und Tests, siehe CHECKLIST.md. Enthält Firmendaten, aber keine Zugangsdaten oder Anfragen.\n",
        )
        add_sources(z, "reference/")
    return stream.getvalue()


def parse_design(content, filename):
    try:
        if filename.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                infos = z.infolist()
                if (
                    len(infos) > 400
                    or sum(i.file_size for i in infos) > 32 * 1024 * 1024
                ):
                    raise ValueError(
                        "Archiv zu groß (maximal 32 MB entpackt / 400 Einträge)"
                    )
                names = [i.filename for i in infos]
                if len(names) != len(set(names)):
                    raise ValueError("Doppelte Archivpfade")
                for i in infos:
                    p = PurePosixPath(i.filename)
                    if (
                        p.is_absolute()
                        or ".." in p.parts
                        or "\\" in i.filename
                        or (i.external_attr >> 16) & 0o170000 == 0o120000
                    ):
                        raise ValueError("Unzulässiger Archivpfad")
                    if i.flag_bits & 1:
                        raise ValueError(
                            "Verschlüsselte ZIP-Dateien werden nicht unterstützt"
                        )
                    if not (
                        i.filename
                        in {
                            "manifest.json",
                            "README.md",
                            "PROMPT.md",
                            "CONTRACT.md",
                            "CHECKLIST.md",
                            "company.json",
                        }
                        or i.filename.startswith(("reference/", "schemas/"))
                    ):
                        raise ValueError(
                            "Nur manifest.json sowie Referenzdateien unter reference/ oder schemas/ erlaubt"
                        )
                content = z.read("manifest.json")
        if len(content) > 128 * 1024:
            raise ValueError("Manifest zu groß")
        manifest = Manifest.model_validate(json.loads(content))
        return manifest
    except (
        ValueError,
        KeyError,
        zipfile.BadZipFile,
        RuntimeError,
        NotImplementedError,
    ):
        raise HTTPException(
            422,
            "Designpaket ungültig. Version 1/2 und vollständigen Vertrag verwenden; ZIP ohne fremde Rootdateien, Duplikate oder unsichere Pfade.",
        )


def check_config(db, config):
    c = Config.model_validate(config)
    checks = []

    def add(key, title, ok, detail, required=True):
        checks.append(
            dict(
                id=key,
                title=title,
                ok=bool(ok),
                detail=detail,
                level="error" if required else "warning",
            )
        )

    resolve(db, c.template)
    add(
        "template",
        "Frontend-Vertrag",
        True,
        "Registrierter Adapter mit vollständiger Seiten- und Aktionsschnittstelle.",
    )
    for key in ["logo", "favicon", "hero_image", "approach_image"]:
        value = getattr(c, key)
        if value.startswith("/api/"):
            f = db.get(File, value.rsplit("/", 1)[-1])
            add(
                key,
                "Mediendatei: " + key,
                f and f.purpose == "brand" and (DATA / "files" / f.id).is_file(),
                "Verknüpfte Unternehmensdatei muss vorhanden sein.",
            )
    f = db.get(File, c.disclosure_pdf) if c.disclosure_pdf else None
    if c.modules.disclosure:
        add(
            "pdf",
            "Selbstauskunft-PDF",
            f and f.purpose == "template" and (DATA / "files" / f.id).is_file(),
            "Aktuelles PDF muss vorhanden sein.",
        )
    add(
        "company",
        "Unternehmensprofil",
        c.address
        and c.email
        and c.phone
        and c.legal.representative
        and c.legal.legal_form
        and c.legal.postcode,
        "Anschrift, Kontakt, PLZ, Rechtsform und Vertretung ergänzen; bei Bedarf Registerdaten.",
        False,
    )
    add(
        "legal",
        "Rechtliche Prüfung bestätigt",
        c.legal.reviewed
        and "RECHTLICH ZU PRÜFEN" not in c.legal_text
        and "RECHTLICH ZU PRÜFEN" not in c.privacy_text,
        "Impressum und Datenschutz müssen zum tatsächlichen Betrieb passen und fachlich geprüft werden.",
        False,
    )
    add(
        "contact",
        "Anfragen landen im Adminbereich",
        all(f.store for f in c.forms.values()),
        "Für den Export werden Zustellwege auf lokale Speicherung gesetzt. Integrationen am Ziel neu einrichten.",
        False,
    )

    def luminance(color):
        rgb = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        return sum(
            (v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) * weight
            for v, weight in zip(rgb, [0.2126, 0.7152, 0.0722])
        )

    light, dark = sorted(
        [
            luminance(c.frontend_theme.background),
            luminance(c.frontend_theme.foreground),
        ],
        reverse=True,
    )
    ratio = (light + 0.05) / (dark + 0.05)
    add(
        "contrast",
        "Grundfarben: Textkontrast",
        ratio >= 4.5,
        f"Text/Hintergrund: {ratio:.1f}:1. Zusätzlich Buttons, Bildüberlagerungen und alle Zustände visuell prüfen.",
        False,
    )
    return {
        "valid": not any(not x["ok"] and x["level"] == "error" for x in checks),
        "checks": checks,
    }


def domain_name(value):
    try:
        domain = value.strip().lower().encode("idna").decode("ascii")
    except UnicodeError:
        raise ValueError("Ungültige Domain")
    if len(domain) > 253 or not re.fullmatch(
        r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", domain
    ):
        raise ValueError(
            "Nur einen Domainnamen angeben, zum Beispiel immobilien.example.com; ohne https:// oder Pfad"
        )
    return domain
