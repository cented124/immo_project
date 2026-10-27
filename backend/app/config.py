from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    EmailStr,
    TypeAdapter,
    model_validator,
    field_validator,
)
from typing import Literal
import re


class Modules(BaseModel):
    contact: bool = True
    properties: bool = True
    applications: bool = True
    disclosure: bool = False
    email: bool = False
    telegram: bool = False
    analytics: bool = False


class Section(BaseModel):
    id: Literal["hero", "services", "properties", "approach", "contact"]
    visible: bool = True


class Service(BaseModel):
    slug: str
    title: str
    text: str
    label: str


class Page(BaseModel):
    slug: str
    title: str
    enabled: bool = True
    text: str = ""
    form: bool = True
    seo_description: str = ""

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, v):
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,60}", v):
            raise ValueError("Ungültiger Seitenpfad")
        if v in [
            "admin",
            "api",
            "immobilien",
            "kontakt",
            "selbstauskunft",
            "impressum",
            "datenschutz",
        ]:
            raise ValueError("Reservierter Seitenpfad")
        return v


class FormTargets(BaseModel):
    store: bool = True
    email: bool = False
    telegram: bool = False
    phone_required: bool = False

    @model_validator(mode="after")
    def destination(self):
        if not any([self.store, self.email, self.telegram]):
            raise ValueError("Mindestens ein Ziel aktivieren")
        return self


class LegalProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", str_max_length=2000)
    legal_form: str = ""
    representative: str = ""
    postcode: str = ""
    register_court: str = ""
    register_number: str = ""
    vat_id: str = ""
    supervisory_authority: str = ""
    professional_rules: str = ""
    responsible_content: str = ""
    reviewed: bool = False


class FrontendBrief(BaseModel):
    model_config = ConfigDict(extra="forbid", str_max_length=6000)
    audience: str = "Eigentümer, Kauf- und Mietinteressenten"
    style: str = "Klar, hochwertig, zugänglich und persönlich"
    wishes: str = ""


class LayoutTheme(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    background: str = Field("#f7f9fa", pattern=r"^#[0-9a-fA-F]{6}$")
    foreground: str = Field("#142736", pattern=r"^#[0-9a-fA-F]{6}$")
    hero_layout: Literal["cover", "split"] = "cover"
    card_layout: Literal["grid", "list"] = "grid"
    radius: int = Field(0, ge=0, le=32)
    content_width: int = Field(1280, ge=960, le=1600)
    spacing: Literal["compact", "normal", "generous"] = "normal"
    heading_scale: float = Field(1, ge=0.8, le=1.3)


class Theme(LayoutTheme):
    primary: str = Field("#173c50", pattern=r"^#[0-9a-fA-F]{6}$")
    accent: str = Field("#b18b63", pattern=r"^#[0-9a-fA-F]{6}$")
    font: Literal["modern", "classic"] = "modern"


class Config(BaseModel):
    company: str = Field("RAUM & WERT", min_length=1, max_length=100)
    tagline: str = "IMMOBILIEN"
    city: str = "Hamburg"
    address: str = ""
    email: str = ""
    phone: str = ""
    legal: LegalProfile = LegalProfile()
    frontend_brief: FrontendBrief = FrontendBrief()
    frontend_theme: LayoutTheme = LayoutTheme()
    logo: str = ""
    favicon: str = ""
    primary: str = "#173c50"
    accent: str = "#b18b63"
    font: Literal["modern", "classic"] = "modern"
    template: str = Field("atelier", pattern=r"^[a-z][a-z0-9-]{1,40}$")
    headline: str = "Räume für heute.\nWerte für morgen."
    introduction: str = "Besondere Immobilien. Persönliche Beratung.\nWir verbinden Ihr Zuhause mit Ihrer nächsten Perspektive."
    hero_image: str = "/architecture.png"
    hero_alt: str = (
        "Architekturillustration einer modernen Villa; kein Immobilienangebot"
    )
    cta_label: str = "Immobilien entdecken"
    cta_target: Literal["immobilien", "kontakt"] = "immobilien"
    seo_title: str = "Immobilien mit Perspektive"
    seo_description: str = (
        "Ihr nächstes Zuhause beginnt mit einer persönlichen Beratung."
    )
    social_links: list[str] = []
    footer_text: str = "Räume mit Charakter. Beratung mit Weitblick."
    services_heading: str = "Ihre Pläne.\nUnsere Perspektive."
    services_intro: str = "Jede Immobilie erzählt eine Geschichte. Wir helfen Ihnen, das nächste Kapitel zu schreiben."
    services: list[Service] = [
        Service(
            slug="verkaufen",
            title="Werte weitergeben.",
            text="Von der ersten Einschätzung bis zur Schlüsselübergabe. Mit einem guten Gefühl verkaufen.",
            label="Immobilie verkaufen",
        ),
        Service(
            slug="vermieten",
            title="Menschen verbinden.",
            text="Das richtige Zuhause für die richtigen Menschen. Wir kümmern uns um die Details.",
            label="Immobilie vermieten",
        ),
        Service(
            slug="bewertung",
            title="Klarheit gewinnen.",
            text="Wissen, was Ihre Immobilie wert ist. Persönlich eingeschätzt, fundiert beraten.",
            label="Wert einschätzen lassen",
        ),
    ]
    approach_heading: str = "Persönlich denken.\nWeitsichtig handeln."
    approach_text: str = "Ein Zuhause ist mehr als eine Adresse. Es ist ein Gefühl. Deshalb nehmen wir uns Zeit für das, was Ihnen wichtig ist – und begleiten Sie mit Erfahrung, Klarheit und einem Blick für das Besondere."
    approach_image: str = "/architecture.png"
    approach_alt: str = "Generierte Architekturillustration; kein Immobilienangebot"
    privacy_text: str = "RECHTLICH ZU PRÜFEN: Ihre Angaben werden zur Bearbeitung Ihrer Anfrage verwendet. Ergänzen Sie Verantwortlichen, Empfänger, Rechtsgrundlagen, Aufbewahrung und Ihre Rechte vor Veröffentlichung."
    legal_text: str = "RECHTLICH ZU PRÜFEN: Bitte hinterlegen Sie hier die vollständigen Anbieterangaben Ihres Unternehmens."
    retention_days: int = Field(90, ge=1, le=730)
    disclosure_text: str = "Laden Sie unsere Selbstauskunft herunter und füllen Sie diese in Ruhe auf Ihrem Gerät aus. Stimmen Sie die Rückgabe persönlich mit uns ab."
    disclosure_pdf: str = ""
    disclosure_returns: bool = False
    modules: Modules = Modules()
    forms: dict[str, FormTargets] = {
        "contact": FormTargets(),
        "application": FormTargets(),
    }
    sections: list[Section] = [
        Section(id=x) for x in ["hero", "services", "properties", "approach", "contact"]
    ]
    pages: list[Page] = [
        Page(
            slug="verkaufen",
            title="Verkaufen",
            text="Ihre Immobilie verdient die richtige Perspektive. Wir begleiten Sie vom ersten Gespräch bis zur Übergabe.",
        ),
        Page(
            slug="vermieten",
            title="Vermieten",
            text="Passende Menschen für Ihre Immobilie. Persönlich, sorgfältig und vorausschauend.",
        ),
        Page(
            slug="bewertung",
            title="Bewertung",
            text="Eine fundierte Einschätzung als Grundlage für Ihre nächste Entscheidung. Wir prüfen Ihre Angaben persönlich; es wird kein automatischer Immobilienwert berechnet.",
        ),
        Page(
            slug="beratung",
            title="Beratung",
            text="Gute Entscheidungen beginnen mit einem offenen Gespräch.",
        ),
        Page(
            slug="ueber-uns",
            title="Über uns",
            text="Immobilien sind für uns mehr als Quadratmeter. Sie sind der Anfang einer neuen Geschichte.",
            form=False,
        ),
    ]

    @field_validator("primary", "accent")
    @classmethod
    def color(cls, v):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            raise ValueError("Farbe als #RRGGBB angeben")
        return v

    @field_validator("email")
    @classmethod
    def valid_email(cls, v):
        return str(TypeAdapter(EmailStr).validate_python(v)) if v else ""

    @field_validator("logo", "favicon", "hero_image", "approach_image")
    @classmethod
    def local_media(cls, v):
        if v and not (
            v == "/architecture.png"
            or re.fullmatch(r"/api/public/files/[a-f0-9]{32}", v)
        ):
            raise ValueError("Bitte eine Datei aus der Medienverwaltung auswählen")
        return v

    @field_validator("social_links")
    @classmethod
    def links(cls, v):
        if any(not x.startswith("https://") for x in v):
            raise ValueError("Social Links müssen HTTPS verwenden")
        return v

    @model_validator(mode="after")
    def valid(self):
        if not {"contact", "application"}.issubset(self.forms):
            raise ValueError("Kontakt- und Bewerbungsformular erforderlich")
        if set(self.forms) - (
            {"contact", "application", "disclosure"} | {p.slug for p in self.pages}
        ):
            raise ValueError("Formulareinstellungen enthalten eine unbekannte Seite")
        if len({p.slug for p in self.pages}) != len(self.pages):
            raise ValueError("Seitenpfade müssen eindeutig sein")
        if len({s.id for s in self.sections}) != len(self.sections):
            raise ValueError("Abschnitte müssen eindeutig sein")
        if any(s.slug not in {p.slug for p in self.pages} for s in self.services):
            raise ValueError("Leistungen müssen auf bestehende Seiten verweisen")
        for f in self.forms.values():
            if f.email and not self.modules.email:
                raise ValueError("E-Mail-Modul zuerst aktivieren")
            if f.telegram and not self.modules.telegram:
                raise ValueError("Telegram-Modul zuerst aktivieren")
        return self


class PropertyData(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    number: str = ""
    title: str = Field(min_length=3, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=160)
    offer: Literal["rent", "sale"] = "sale"
    type: Literal["house", "apartment"] = "house"
    status: Literal["draft", "published", "reserved", "sold", "archived"] = "draft"
    street: str = ""
    house_number: str = ""
    postcode: str = ""
    city: str = ""
    district: str = ""
    show_address: bool = False
    available: str = ""
    contact: str = ""
    area: float = Field(0, ge=0)
    land_area: float = Field(0, ge=0)
    rooms: float = Field(0, ge=0)
    bedrooms: int = Field(0, ge=0)
    bathrooms: int = Field(0, ge=0)
    floor: int | None = None
    floors: int | None = None
    year: int | None = Field(None, ge=1700, le=2200)
    modernized: int | None = Field(None, ge=1700, le=2200)
    condition: str = ""
    furnished: str = ""
    accessibility: str = ""
    pets: str = ""
    features: list[str] = []
    price: float = Field(0, ge=0)
    service_charge: float = Field(0, ge=0)
    heating_cost: float = Field(0, ge=0)
    heating_included: bool = True
    deposit: float = Field(0, ge=0)
    parking_cost: float = Field(0, ge=0)
    furniture_cost: float = Field(0, ge=0)
    maintenance: float = Field(0, ge=0)
    commission: str = ""
    heating: str = ""
    energy_source: str = ""
    certificate: Literal["unknown", "demand", "consumption", "exempt"] = "unknown"
    energy_value: float | None = Field(None, ge=0)
    energy_class: str = ""
    energy_until: str = ""
    energy_year: int | None = None
    exemption_reason: str = ""
    description: str = ""
    equipment: str = ""
    location: str = ""
    notes: str = ""
    images: list[dict[str, str]] = []
    documents: list[str] = []

    @model_validator(mode="after")
    def publication(self):
        if self.status in ["published", "reserved"]:
            if (
                not self.city
                or not self.postcode
                or self.price <= 0
                or self.area <= 0
                or self.rooms <= 0
                or not self.description
                or not self.images
            ):
                raise ValueError(
                    "Zur Veröffentlichung: Ort, PLZ, Preis, Fläche, Zimmer, Beschreibung und Titelbild ergänzen"
                )
            if self.certificate == "unknown":
                raise ValueError(
                    "Energieausweis ergänzen oder begründete Ausnahme angeben"
                )
            if self.certificate == "exempt" and not self.exemption_reason:
                raise ValueError("Ausnahme begründen")
            if self.certificate in ["demand", "consumption"] and (
                self.energy_value is None
                or not self.energy_until
                or not self.energy_class
                or not self.energy_source
            ):
                raise ValueError(
                    "Energiekennwert, Gültigkeit, Klasse und Energieträger ergänzen"
                )
        return self
