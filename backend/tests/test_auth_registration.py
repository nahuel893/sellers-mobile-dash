"""Tests para verificar que el auth router está registrado correctamente en main.py.

Verifica:
- Las rutas /api/auth/* existen (no 404)
- GET /api/auth/me sin header retorna 401 (no 404)
- Los endpoints existentes siguen funcionando sin auth (sin regresiones)
"""
import pytest
from fastapi.testclient import TestClient

from main import app
from dependencies import get_df
from data.mock_data import get_mock_dataframe


@pytest.fixture(autouse=True)
def override_deps():
    """Usa mock data para todos los tests — igual que test_api.py."""
    app.dependency_overrides[get_df] = get_mock_dataframe
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# test_auth_login_route_exists
# Verifica que POST /api/auth/login está montado (devuelve algo distinto de 404).
# Con credenciales vacías esperamos 401 o 422 (validación), NUNCA 404.
# ---------------------------------------------------------------------------

def test_auth_login_route_exists(client):
    """POST /api/auth/login debe estar montado — cualquier respuesta que no sea 404."""
    r = client.post("/api/auth/login", json={"username": "noexiste", "password": "wrong"})
    assert r.status_code != 404, (
        f"Router auth no montado: /api/auth/login devolvió 404. "
        f"Respuesta: {r.status_code} {r.text}"
    )


# ---------------------------------------------------------------------------
# test_auth_me_without_header_returns_401
# Verifica que GET /api/auth/me sin Authorization header devuelve 401, no 404.
# ---------------------------------------------------------------------------

def test_auth_me_without_header_returns_401(client):
    """GET /api/auth/me sin header de auth debe devolver 401, NO 404."""
    r = client.get("/api/auth/me")
    assert r.status_code == 401, (
        f"Se esperaba 401 (auth required), se obtuvo {r.status_code}. "
        f"Respuesta: {r.text}"
    )


# ---------------------------------------------------------------------------
# test_existing_dashboard_still_works
# Sin regresiones: GET /api/dashboard sigue devolviendo 200 sin auth.
# ---------------------------------------------------------------------------

def test_existing_dashboard_still_works(client):
    """GET /api/dashboard debe seguir respondiendo 200 sin autenticación."""
    r = client.get("/api/dashboard", params={
        "supervisor": "BADIE",
        "sucursal": "1 - CASA CENTRAL",
    })
    assert r.status_code == 200, (
        f"Regresión detectada: /api/dashboard devolvió {r.status_code}. "
        f"Respuesta: {r.text}"
    )


# ---------------------------------------------------------------------------
# test_existing_sucursales_still_public
# Sin regresiones: GET /api/sucursales sigue siendo público (200 sin auth).
# ---------------------------------------------------------------------------

def test_existing_sucursales_still_public(client):
    """GET /api/sucursales debe responder 200 sin ningún header de autenticación."""
    r = client.get("/api/sucursales")
    assert r.status_code == 200, (
        f"Regresión detectada: /api/sucursales devolvió {r.status_code}. "
        f"Respuesta: {r.text}"
    )
