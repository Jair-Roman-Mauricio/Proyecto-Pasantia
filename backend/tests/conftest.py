"""
Test fixtures: SQLite in-memory engine, sessions, HTTP client, users, and domain data.
"""
import time
import uuid
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from jose import jwt
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.bar import Bar
from app.models.circuit import Circuit
from app.models.permission import Permission
from app.models.station import Station
from app.models.user import User
from app.utils.constants import PERMISSION_FEATURES

# ---------------------------------------------------------------------------
# Test engine — single SQLite in-memory database shared across all connections
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def set_fk_pragma(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)

# ---------------------------------------------------------------------------
# Table lifecycle — fresh schema per test
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate all tables before each test for full isolation."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


# ---------------------------------------------------------------------------
# Session fixture — one session per test, shared with the FastAPI app
# ---------------------------------------------------------------------------


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def override_get_db(db):
    """Override FastAPI's get_db to use the test session."""
    app.dependency_overrides[get_db] = lambda: (yield db)
    yield
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

JWT_SECRET = "test-secret-for-pytest-hs256"


def make_token(user_id: str) -> str:
    return jwt.encode(
        {"sub": user_id, "exp": time.time() + 3600},
        JWT_SECRET,
        algorithm="HS256",
    )


# ---------------------------------------------------------------------------
# Supabase Admin mock — applied automatically to every test
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_supabase_admin(monkeypatch):
    fake_id = str(uuid.uuid4())
    monkeypatch.setattr(
        "app.api.v1.users.create_supabase_auth_user",
        AsyncMock(return_value={"id": fake_id}),
    )
    monkeypatch.setattr(
        "app.api.v1.users.delete_supabase_auth_user",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "app.api.v1.users.update_supabase_auth_user",
        AsyncMock(return_value=None),
    )
    return fake_id  # tests can capture this via indirect fixture usage


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_user(db):
    user = User(
        id=uuid.uuid4(),
        username="admin_test",
        full_name="Admin Test",
        role="admin",
        status="active",
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def opersac_user(db):
    user = User(
        id=uuid.uuid4(),
        username="opersac_test",
        full_name="Opersac Test",
        role="opersac",
        status="active",
    )
    db.add(user)
    db.flush()
    for feature in PERMISSION_FEATURES:
        db.add(Permission(user_id=user.id, feature_key=feature, is_allowed=True))
    db.flush()
    return user


@pytest.fixture
def admin_token(admin_user):
    return make_token(str(admin_user.id))


@pytest.fixture
def opersac_token(opersac_user):
    return make_token(str(opersac_user.id))


# ---------------------------------------------------------------------------
# Domain data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def station(db):
    s = Station(
        code="E01",
        name="Villa El Salvador",
        order_index=1,
        transformer_capacity_kw=500,
        max_demand_kw=0,
        available_power_kw=500,
        status="green",
    )
    db.add(s)
    db.flush()
    return s


@pytest.fixture
def bar(db, station):
    b = Bar(
        station_id=station.id,
        name="Barra Normal E01",
        bar_type="normal",
        status="operative",
        capacity_kw=200,
        capacity_a=300,
    )
    db.add(b)
    db.flush()
    return b


@pytest.fixture
def circuit(db, bar):
    c = Circuit(
        bar_id=bar.id,
        denomination="C-01",
        name="Circuito 01",
        pi_kw=10,
        fd=0.8,
        md_kw=8,
        status="operative_normal",
    )
    db.add(c)
    db.flush()
    return c
