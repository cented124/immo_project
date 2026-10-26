import os, sys, subprocess, tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="raumwerk-test-")
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "sqlite:///" + os.environ["DATA_DIR"] + "/test.db"
)
os.environ["DELIVERY_WORKER"] = "0"
os.environ["ALLOW_INSECURE_SMTP"] = "1"
import pytest
from fastapi.testclient import TestClient
from app.db import Base, engine, Session, User
from app.main import app, initialize, _limits
from app.security import hasher


@pytest.fixture(scope="session", autouse=True)
def migration():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "backend/alembic.ini",
            "upgrade",
            "head",
        ],
        check=True,
    )
    yield


@pytest.fixture(autouse=True)
def clean(migration):
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    _limits.clear()
    initialize()
    with Session() as db:
        db.add(
            User(
                email="admin@example.com",
                password=hasher.hash("test-password-1234"),
                role="admin",
            )
        )
        db.add(
            User(
                email="staff@example.com",
                password=hasher.hash("test-password-1234"),
                role="staff",
            )
        )
        db.commit()


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def admin(client):
    client.headers["X-Requested-With"] = "Raumwerk"
    assert (
        client.post(
            "/api/admin/login",
            json={"email": "admin@example.com", "password": "test-password-1234"},
        ).status_code
        == 200
    )
    return client
