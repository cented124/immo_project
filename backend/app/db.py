import os
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATA = Path(
    os.getenv("DATA_DIR", str(Path(__file__).resolve().parents[2] / ".local/data"))
).resolve()
DATA.mkdir(parents=True, exist_ok=True)
url = os.getenv("DATABASE_URL", f"sqlite:///{DATA}/app.db")
engine = create_engine(
    url,
    connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    pool_pre_ping=True,
)
Session = sessionmaker(engine, expire_on_commit=False)


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="admin")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class LoginSession(Base):
    __tablename__ = "sessions"
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Property(Base):
    __tablename__ = "properties"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    data: Mapped[dict] = mapped_column(JSON)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Inquiry(Base):
    __tablename__ = "inquiries"
    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int | None] = mapped_column(ForeignKey("properties.id"))
    kind: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="new")
    data: Mapped[dict] = mapped_column(JSON)
    notes: Mapped[str] = mapped_column(Text, default="")
    retained: Mapped[bool] = mapped_column(Boolean, default=True)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Submission(Base):
    __tablename__ = "submissions"
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    inquiry_id: Mapped[int] = mapped_column(Integer)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Delivery(Base):
    __tablename__ = "deliveries"
    id: Mapped[int] = mapped_column(primary_key=True)
    inquiry_id: Mapped[int] = mapped_column(
        ForeignKey("inquiries.id", ondelete="CASCADE")
    )
    channel: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    error: Mapped[str] = mapped_column(Text, default="")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class File(Base):
    __tablename__ = "files"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(80))
    purpose: Mapped[str] = mapped_column(String(30))
    property_id: Mapped[int | None] = mapped_column(ForeignKey("properties.id"))
    inquiry_id: Mapped[int | None] = mapped_column(ForeignKey("inquiries.id"))
    size: Mapped[int] = mapped_column(Integer)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(30))
    path: Mapped[str] = mapped_column(String(200))
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(254))
    action: Mapped[str] = mapped_column(String(100))
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Revision(Base):
    __tablename__ = "revisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(254))
    label: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(20))
    config: Mapped[dict] = mapped_column(JSON)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
