"""Immutable browser bundles: data on disk, scripts only in an opaque iframe."""

import hashlib
import hmac
import io
import json
import mimetypes
import re
import shutil
import time
import zipfile
import posixpath
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from dataclasses import dataclass
from pathlib import PurePosixPath
from fastapi import HTTPException
from PIL import Image
from .db import DATA, Setting
from .security import key_material
from .templates import Manifest

MAX_UNPACKED = 32 * 1024 * 1024
EXTENSIONS = {
    ".html",
    ".css",
    ".js",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".txt",
    ".map",
}
MIMES = {
    ".svg": "image/svg+xml",
    ".js": "text/javascript",
    ".css": "text/css",
    ".html": "text/html",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
}


def safe_path(value):
    p = PurePosixPath(value)
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 180
        or not re.fullmatch(r"[A-Za-z0-9_./@+-]+", value)
        or p.is_absolute()
        or any(
            part in {"", ".", ".."}
            or part.startswith(".")
            or part.endswith(".")
            or part.split(".")[0].upper()
            in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10)),
            }
            for part in value.split("/")
        )
    ):
        raise ValueError(
            "Dateipfade müssen relativ sein und dürfen keine versteckten Dateien enthalten"
        )
    return p


@dataclass
class DesignPackage:
    manifest: Manifest
    files: dict


def check_references(files):
    def check(source, value):
        parts = urlsplit(value)
        if parts.scheme == "data":
            return
        if parts.scheme or parts.netloc or value.startswith("/"):
            raise ValueError(
                "Frontend-Ressourcen müssen relative lokale Pfade verwenden: "
                + value[:100]
            )
        target = posixpath.normpath(
            posixpath.join(posixpath.dirname(source), unquote(parts.path))
        )
        if target not in files:
            raise ValueError("Im ZIP fehlt eine verknüpfte Datei: " + target[:140])

    class References(HTMLParser):
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "script" and attrs.get("src"):
                check(self.source, attrs["src"])
            if (
                tag == "link"
                and attrs.get("href")
                and attrs.get("rel", "").lower()
                in {"stylesheet", "modulepreload", "preload", "icon"}
            ):
                check(self.source, attrs["href"])
            if tag == "base":
                raise ValueError(
                    "Kein base-Tag im Browserpaket verwenden; relative lokale Dateipfade benutzen"
                )

    for name, raw in files.items():
        if name.lower().endswith(".html"):
            parser = References()
            parser.source = name
            parser.feed(raw.decode("utf-8"))
        if name.lower().endswith(".css"):
            for value in re.findall(
                r"url\(\s*[\'\"]?([^\)\'\"]+)[\'\"]?\s*\)", raw.decode("utf-8"), re.I
            ):
                if not value.startswith(("data:", "#")):
                    check(name, value.strip())


def parse_package(content, filename):
    try:
        files = {}
        if filename.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                infos = archive.infolist()
                if len(infos) > 400 or sum(i.file_size for i in infos) > MAX_UNPACKED:
                    raise ValueError("ZIP maximal 32 MB entpackt und 400 Dateien")
                names = [i.filename.rstrip("/") for i in infos]
                if len(names) != len(set(n.casefold() for n in names)):
                    raise ValueError("Doppelte Dateinamen im ZIP")
                for info in infos:
                    candidate = PurePosixPath(info.filename)
                    if (
                        candidate.is_absolute()
                        or ".." in candidate.parts
                        or "\\" in info.filename
                        or "\x00" in info.filename
                    ):
                        raise ValueError("Unzulässiger Archivpfad")
                    if (
                        info.flag_bits & 1
                        or (info.external_attr >> 16) & 0o170000 == 0o120000
                    ):
                        raise ValueError(
                            "Verschlüsselte Dateien und Verknüpfungen sind nicht erlaubt"
                        )
                # ZIP from a hosting service may wrap the package in one folder.
                roots = [
                    i.filename
                    for i in infos
                    if i.filename.endswith("/manifest.json")
                    or i.filename == "manifest.json"
                ]
                if "manifest.json" in roots:
                    prefix = ""
                elif len(roots) == 1 and roots[0].count("/") == 1:
                    prefix = roots[0][: -len("manifest.json")]
                else:
                    raise ValueError(
                        "manifest.json fehlt auf der obersten Ebene des Frontend-Pakets"
                    )
                for info in infos:
                    if info.is_dir():
                        continue
                    if not info.filename.startswith(prefix):
                        raise ValueError("Dateien außerhalb des Paketordners")
                    name = info.filename[len(prefix) :]
                    if info.file_size > 10 * 1024 * 1024:
                        raise ValueError("Eine Datei überschreitet 10 MB")
                    files[name] = archive.read(info)
                content = files.pop("manifest.json")
        if len(content) > 128 * 1024:
            raise ValueError("Manifest maximal 128 KB")
        manifest = Manifest.model_validate(json.loads(content))
        if manifest.version != 3:
            for name in files:
                if name not in {
                    "README.md",
                    "PROMPT.md",
                    "CONTRACT.md",
                    "CHECKLIST.md",
                    "company.json",
                } and not name.startswith(("reference/", "schemas/")):
                    raise ValueError(
                        "Das ZIP enthält Frontend-Quellcode. Bitte das fertig gebaute Raumwerk-Frontend.zip verwenden"
                    )
            return DesignPackage(manifest, {})
        if not files or manifest.entry not in files:
            raise ValueError(
                "Das vollständige ZIP mit der HTML-Einstiegsdatei auswählen, nicht nur manifest.json"
            )
        for name, raw in files.items():
            suffix = safe_path(name).suffix.lower()
            if any(
                str(parent) in files
                for parent in PurePosixPath(name).parents
                if str(parent) != "."
            ):
                raise ValueError("Datei und Ordner besitzen denselben Namen")
            if suffix not in EXTENSIONS and name != "README.md":
                raise ValueError(
                    "Nicht unterstützte Datei: "
                    + name
                    + ". Nur fertige Browserdateien, keine TSX-, Server- oder Paketquellen"
                )
            if suffix in {".html", ".css", ".js", ".json", ".txt", ".map", ".svg"}:
                raw.decode("utf-8")
            if suffix == ".svg" and (
                not re.search(rb"<svg(?:\s|>)", raw, re.I)
                or re.search(rb"<!DOCTYPE|<!ENTITY", raw, re.I)
            ):
                raise ValueError(
                    "SVG muss eine lokale Grafik ohne externe Entitäten sein"
                )
            if suffix in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico"}:
                with Image.open(io.BytesIO(raw)) as image:
                    if image.width * image.height > 24_000_000:
                        raise ValueError("Bild zu groß")
                    image.verify()
        for slot, name in manifest.assets.items():
            if name not in files or safe_path(name).suffix.lower() not in {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".ico",
                ".svg",
            }:
                raise ValueError(
                    "Bild für " + slot + " fehlt oder hat ein ungeeignetes Format"
                )
        check_references(files)
        return DesignPackage(manifest, files)
    except (
        ValueError,
        KeyError,
        zipfile.BadZipFile,
        RuntimeError,
        NotImplementedError,
        OSError,
        Image.DecompressionBombError,
    ) as error:
        detail = (
            str(error)
            if type(error) is ValueError
            else "ZIP oder Manifest ist beschädigt bzw. entspricht nicht dem Raumwerk-Vertrag"
        )
        raise HTTPException(422, detail[:400])


def metadata(files):
    return {
        name: {"sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw)}
        for name, raw in files.items()
    }


def store_package(db, package):
    identity = package.manifest.id
    target = DATA / "designs" / identity
    if target.exists():
        raise HTTPException(
            409, "Diese Paket-ID besitzt bereits Dateien. Bitte eine neue ID verwenden"
        )
    try:
        target.mkdir(parents=True, mode=0o700)
        for name, raw in package.files.items():
            destination = target.joinpath(*safe_path(name).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        db.add(Setting(key="design_" + identity, value=metadata(package.files)))
    except BaseException:
        shutil.rmtree(target, ignore_errors=True)
        raise
    return target


def preview_token(identity):
    expires = str(int(time.time()) + 900)
    payload = identity + ":" + expires
    signature = hmac.new(
        key_material(), ("frontend-preview:" + payload).encode(), hashlib.sha256
    ).hexdigest()
    return expires + "-" + signature


def valid_preview(identity, token):
    try:
        expires, signature = token.split("-", 1)
        timestamp = int(expires)
        if not int(time.time()) <= timestamp <= int(time.time()) + 901:
            return False
        payload = identity + ":" + expires
        expected = hmac.new(
            key_material(), ("frontend-preview:" + payload).encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)
    except (ValueError, TypeError):
        return False


def package_view(manifest, preview=False):
    identity = manifest["id"]
    base = "/api/public/frontend/" + identity + "/"
    if preview:
        base = (
            "/api/public/frontend-preview/"
            + preview_token(identity)
            + "/"
            + identity
            + "/"
        )
    return {
        "id": identity,
        "name": manifest["name"],
        "base": base,
        "entry": base + manifest["entry"],
        "preview": preview,
    }


def package_file(db, identity, name):
    try:
        safe_path(name)
    except ValueError:
        raise HTTPException(404)
    row = db.get(Setting, "design_" + identity)
    if not row or name not in row.value:
        raise HTTPException(404)
    root = DATA / "designs" / identity
    path = root.joinpath(*PurePosixPath(name).parts)
    if (
        not path.is_file()
        or path.is_symlink()
        or not path.resolve().is_relative_to(root.resolve())
    ):
        raise HTTPException(404, "Paketdatei fehlt")
    return path, MIMES.get(
        path.suffix.lower(),
        mimetypes.guess_type(path.name)[0] or "application/octet-stream",
    )


# Applied to HTML, JS, CSS and images, including when a file is opened directly.
# No same-origin privilege, forms, outgoing connections, plugins or parent access.
PACKAGE_CSP = "sandbox allow-scripts allow-forms allow-downloads; default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'none'; form-action 'none'; base-uri 'none'; object-src 'none'; frame-src 'none'; frame-ancestors 'self'"


def package_intact(db, identity):
    row = db.get(Setting, "design_" + identity)
    if not row or not row.value:
        return False
    try:
        return all(
            hashlib.sha256(package_file(db, identity, name)[0].read_bytes()).hexdigest()
            == info["sha256"]
            for name, info in row.value.items()
        )
    except (HTTPException, OSError, KeyError, ValueError):
        return False
