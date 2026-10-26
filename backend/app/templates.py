import json
from pathlib import Path
from fastapi import HTTPException
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Literal
from sqlalchemy import select
from .db import Setting


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{1,40}$")
    name: str = Field(min_length=1, max_length=100)
    version: Literal[1]
    adapter: Literal["atelier", "editorial"]
    pages: list[
        Literal["home", "properties", "property", "contact", "disclosure", "content"]
    ]
    actions: list[Literal["search", "inquiry", "download", "return"]]

    @model_validator(mode="after")
    def contract(self):
        if (
            len(self.pages) != 6
            or set(self.pages)
            != {"home", "properties", "property", "contact", "disclosure", "content"}
            or set(self.actions) != {"search", "inquiry", "download", "return"}
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


def presentation(db, config):
    return {**config, "template_adapter": resolve(db, config["template"])["adapter"]}
