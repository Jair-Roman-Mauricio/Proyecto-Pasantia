"""
Tests de Integración — Autenticación
=====================================
Endpoint: /api/v1/auth

Casos de prueba:
  TC-I01  Login exitoso devuelve token JWT y datos del usuario
  TC-I02  Login fallido con contraseña incorrecta devuelve 401
  TC-I03  Login fallido con usuario inexistente devuelve 401
  TC-I04  Acceso a ruta protegida sin token devuelve 401
  TC-I05  Opersac accede a endpoint exclusivo de admin devuelve 403
  TC-I06  GET /auth/me con token válido devuelve datos del usuario
"""

import pytest
from app.models.user import User
from app.utils.security import hash_password


# ---------------------------------------------------------------------------
# Fixtures locales
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_credentials(db_session):
    """Crea un usuario admin y retorna sus credenciales."""
    user = User(
        username="admin_login_test",
        password_hash=hash_password("password123"),
        full_name="Admin Login",
        role="admin",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    return {"username": "admin_login_test", "password": "password123"}


@pytest.fixture
def opersac_credentials(db_session):
    user = User(
        username="opersac_login_test",
        password_hash=hash_password("password123"),
        full_name="Opersac Login",
        role="opersac",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    return {"username": "opersac_login_test", "password": "password123"}


# ---------------------------------------------------------------------------
# TC-I01: Login exitoso devuelve token JWT y datos del usuario
# ---------------------------------------------------------------------------

def test_login_with_valid_credentials_returns_token(client, admin_credentials):
    # Arrange
    payload = admin_credentials

    # Act
    response = client.post("/api/v1/auth/login", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "admin_login_test"
    assert data["user"]["role"] == "admin"


# ---------------------------------------------------------------------------
# TC-I02: Login fallido con contraseña incorrecta devuelve 401
# ---------------------------------------------------------------------------

def test_login_with_wrong_password_returns_401(client, admin_credentials):
    # Arrange
    payload = {"username": admin_credentials["username"], "password": "wrong_pass"}

    # Act
    response = client.post("/api/v1/auth/login", json=payload)

    # Assert
    assert response.status_code == 401
    assert "Credenciales" in response.json()["detail"]


# ---------------------------------------------------------------------------
# TC-I03: Login con usuario inexistente devuelve 401
# ---------------------------------------------------------------------------

def test_login_with_nonexistent_user_returns_401(client):
    # Arrange
    payload = {"username": "no_existe", "password": "cualquier"}

    # Act
    response = client.post("/api/v1/auth/login", json=payload)

    # Assert
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# TC-I04: Acceso a ruta protegida sin token devuelve 401
# ---------------------------------------------------------------------------

def test_protected_route_without_token_returns_401(client):
    # Act
    response = client.get("/api/v1/stations")

    # Assert
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# TC-I05: Opersac no puede acceder a endpoints exclusivos de admin
# ---------------------------------------------------------------------------

def test_opersac_access_to_admin_endpoint_returns_403(client, opersac_credentials):
    # Arrange — obtener token opersac
    login_resp = client.post("/api/v1/auth/login", json=opersac_credentials)
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Act — intentar listar usuarios (solo admin)
    response = client.get("/api/v1/users", headers=headers)

    # Assert
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# TC-I06: GET /auth/me con token válido retorna datos del usuario
# ---------------------------------------------------------------------------

def test_get_me_with_valid_token_returns_user_data(client, admin_credentials):
    # Arrange
    login_resp = client.post("/api/v1/auth/login", json=admin_credentials)
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Act
    response = client.get("/api/v1/auth/me", headers=headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin_login_test"
    assert data["role"] == "admin"
