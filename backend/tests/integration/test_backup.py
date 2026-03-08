"""
Tests de Integración — Backups
================================
Endpoints: /api/v1/backups

Casos de prueba:
  TC-I13  Crear backup devuelve 201 con file_name en formato correcto
  TC-I14  Descargar backup JSON devuelve archivo con Content-Disposition
  TC-I15  Restaurar backup devuelve 200 con mensaje de confirmación
  TC-I16  Descargar backup inexistente devuelve 404
  TC-I17  Opersac no puede crear backup (403)
"""

import json
import re
import pytest


# ---------------------------------------------------------------------------
# TC-I13: Crear backup devuelve 201 con file_name en formato correcto
# ---------------------------------------------------------------------------

def test_create_backup_returns_201_with_correct_filename(client, auth_admin):
    # Arrange
    payload = {"description": "Backup de prueba", "includes_audit": True}

    # Act
    response = client.post("/api/v1/backups", json=payload, headers=auth_admin)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "file_name" in data
    assert re.match(r"backup_\d{8}_\d{6}\.json", data["file_name"]), (
        f"file_name '{data['file_name']}' no coincide con el formato esperado"
    )
    assert data["includes_audit"] is True


# ---------------------------------------------------------------------------
# TC-I14: Descargar backup JSON devuelve archivo con Content-Disposition
# ---------------------------------------------------------------------------

def test_download_backup_returns_json_file(client, auth_admin):
    # Arrange — crear un backup primero
    create_resp = client.post(
        "/api/v1/backups",
        json={"description": "Para descarga", "includes_audit": False},
        headers=auth_admin,
    )
    backup_id = create_resp.json()["id"]

    # Act
    response = client.get(f"/api/v1/backups/{backup_id}/download", headers=auth_admin)

    # Assert
    assert response.status_code == 200
    assert "attachment" in response.headers.get("content-disposition", "")
    assert ".json" in response.headers.get("content-disposition", "")
    # El cuerpo debe ser JSON válido con las claves esperadas
    body = json.loads(response.content)
    assert "stations" in body
    assert "bars" in body
    assert "circuits" in body


# ---------------------------------------------------------------------------
# TC-I15: Restaurar backup devuelve 200 con mensaje de confirmación
# ---------------------------------------------------------------------------

def test_restore_backup_returns_200_with_success_message(client, auth_admin):
    # Arrange — crear un backup
    create_resp = client.post(
        "/api/v1/backups",
        json={"description": "Para restaurar", "includes_audit": False},
        headers=auth_admin,
    )
    backup_id = create_resp.json()["id"]

    # Act
    response = client.post(f"/api/v1/backups/{backup_id}/restore", headers=auth_admin)

    # Assert
    assert response.status_code == 200
    assert "restaurado" in response.json()["message"].lower()


# ---------------------------------------------------------------------------
# TC-I16: Descargar backup inexistente devuelve 404
# ---------------------------------------------------------------------------

def test_download_nonexistent_backup_returns_404(client, auth_admin):
    # Act
    response = client.get("/api/v1/backups/9999/download", headers=auth_admin)

    # Assert
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# TC-I17: Opersac no puede crear backup — devuelve 403
# ---------------------------------------------------------------------------

def test_opersac_cannot_create_backup_returns_403(client, auth_opersac):
    # Arrange
    payload = {"description": "Intento opersac", "includes_audit": False}

    # Act
    response = client.post("/api/v1/backups", json=payload, headers=auth_opersac)

    # Assert
    assert response.status_code == 403
