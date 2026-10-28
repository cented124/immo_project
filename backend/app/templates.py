import json
from pathlib import Path
from fastapi import HTTPException
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Literal
from sqlalchemy import select
from .db import Setting
from .config import Theme


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{1,40}$")
    name: str = Field(min_length=1, max_length=100)
    version: Literal[1, 2, 3]
    adapter: Literal["atelier", "editorial"]
    theme: Theme | None = None
    entry: str | None = None
    assets: dict[Literal["hero_image", "approach_image", "logo", "favicon"], str] = {}
    pages: list[
        Literal["home", "properties", "property", "contact", "disclosure", "content"]
    ]
    actions: list[Literal["search", "inquiry", "download", "return"]]

    @model_validator(mode="after")
    def contract(self):
        if (self.version == 2 and self.theme is None) or (
            self.version == 1 and self.theme is not None
        ):
            raise ValueError(
                "Version 2 benötigt ein Theme; Version 1 verwendet den registrierten Adapter"
            )
        if self.version == 3:
            if not self.entry or not self.entry.endswith(".html"):
                raise ValueError("Version 3 benötigt eine HTML-Einstiegsdatei")
        elif self.entry or self.assets:
            raise ValueError("Dateien benötigen ein vollständiges Version-3-ZIP")
        if (
            len(self.pages) != 6
            or set(self.pages)
            != {"home", "properties", "property", "contact", "disclosure", "content"}
            or set(self.actions) != {"search", "inquiry", "download", "return"}
            or len(self.actions) != 4
        ):
            raise ValueError(
                "Vollständige Seiten- und Aktionsschnittstelle erforderlich"
            )
        return self


def library(db):
    folder = Path(__file__).resolve().parents[2] / "templates"
    builtins = [
        Manifest.model_validate(json.loads(p.read_text())).model_dump()
        for p in folder.glob("*.json")
    ]
    return builtins + [
        r.value
        for r in db.scalars(select(Setting).where(Setting.key.like("template_%")))
    ]


def resolve(db, identity):
    manifest = next((m for m in library(db) if m["id"] == identity), None)
    if not manifest:
        raise HTTPException(
            422, "Dieses Template wurde noch nicht importiert oder ist nicht kompatibel"
        )
    return manifest


def presentation(db, config, preview=False):
    manifest = resolve(db, config["template"])
    result = {**config, "template_adapter": manifest["adapter"]}
    if manifest["version"] == 3:
        from .frontend_packages import package_view

        result["frontend_package"] = package_view(manifest, preview)
    return result
