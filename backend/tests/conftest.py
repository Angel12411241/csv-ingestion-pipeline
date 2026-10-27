import os
from pathlib import Path

# Must be set before the app modules are imported (the engine is created at import time).
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+pysqlite://")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.db import Base, get_db, get_sessionmaker  # noqa: E402
from app.main import create_app  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.fixture(scope="session")
def engine():
    if TEST_DATABASE_URL.startswith("sqlite"):
        # One shared in-memory connection so every session sees the same database.
        engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(session_factory):
    app = create_app()

    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_sessionmaker] = lambda: session_factory
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def login(client):
    """Register (if needed) and log in a user, returning Authorization headers."""

    def _login(email: str = "alice@example.com", password: str = "password123") -> dict[str, str]:
        client.post("/api/register", json={"email": email, "password": password})
        response = client.post("/api/login", data={"username": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login


@pytest.fixture
def auth_headers(login):
    return login()


@pytest.fixture
def upload(client, auth_headers):
    """Upload a fixture file synchronously and return the response."""

    def _upload(name: str = "sample_sales.csv", headers: dict | None = None, **params):
        files = {"file": (name, fixture_bytes(name), "text/csv")}
        return client.post("/api/upload", files=files, params=params, headers=headers or auth_headers)

    return _upload
