"""
conftest.py — Fixtures globales compartidas por todos los tests.

Provee:
  - db_session : sesión SQLite en memoria, aislada por test
  - client     : TestClient de FastAPI con la BD sobreescrita
  - admin_token: token JWT de un usuario admin de prueba
  - opersac_token: token JWT de un usuario opersac de prueba
  - station    : estación de prueba con capacidad 100 kW
  - bar        : barra eléctrica asociada a la estación de prueba
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.station import Station
from app.models.bar import Bar
from app.utils.security import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Base de datos en memoria (SQLite) — aislada por función
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_session():
    """
    Crea una BD SQLite en memoria para cada test.
    Se destruye al finalizar el test garantizando aislamiento completo.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Cliente HTTP con la BD sobreescrita
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client(db_session):
    """
    TestClient con la dependencia get_db apuntando a la BD de test.
    Limpia los overrides tras cada test.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers: creación de usuarios de prueba
# ---------------------------------------------------------------------------

def _create_user(db_session, username: str, role: str) -> User:
    user = User(
        username=username,
        password_hash=hash_password("test1234"),
        full_name=f"Usuario {role.capitalize()} Test",
        role=role,
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _get_token(user: User) -> str:
    return create_access_token(data={"sub": str(user.id), "role": user.role})


# ---------------------------------------------------------------------------
# Fixtures: tokens JWT
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(db_session) -> User:
    return _create_user(db_session, "admin_test", "admin")


@pytest.fixture
def opersac_user(db_session) -> User:
    return _create_user(db_session, "opersac_test", "opersac")


@pytest.fixture
def admin_token(admin_user) -> str:
    """Token JWT válido para un usuario admin."""
    return _get_token(admin_user)


@pytest.fixture
def opersac_token(opersac_user) -> str:
    """Token JWT válido para un usuario opersac."""
    return _get_token(opersac_user)


@pytest.fixture
def auth_admin(admin_token) -> dict:
    """Header Authorization listo para usar en client.get/post."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_opersac(opersac_token) -> dict:
    return {"Authorization": f"Bearer {opersac_token}"}


# ---------------------------------------------------------------------------
# Fixtures: datos de prueba comunes
# ---------------------------------------------------------------------------

@pytest.fixture
def station(db_session) -> Station:
    """
    Estación de prueba con capacidad de 100 kW.
    Reutilizable en tests de circuitos, barras y cálculo energético.
    """
    s = Station(
        code="TST01",
        name="Estacion Test",
        order_index=1,
        transformer_capacity_kw=Decimal("100.00"),
        max_demand_kw=Decimal("0.00"),
        available_power_kw=Decimal("100.00"),
        status="green",
    )
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


@pytest.fixture
def bar(db_session, station) -> Bar:
    """Barra eléctrica principal asociada a la estación de prueba."""
    b = Bar(
        station_id=station.id,
        name="Barra A",
        bar_type="principal",
        status="operative",
        capacity_kw=Decimal("100.00"),
        capacity_a=Decimal("200.00"),
    )
    db_session.add(b)
    db_session.commit()
    db_session.refresh(b)
    return b
