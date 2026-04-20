"""
Tests de routers/ventas_mapa.py

TDD: tests escritos antes de la implementación.
Mockea get_clientes_mapa y get_hover_cliente — sin DB real.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.jwt import create_access_token
from auth.models import UserInDB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    role_name: str = "admin",
    sucursales: list[int] | None = None,
    user_id: int = 1,
) -> UserInDB:
    return UserInDB(
        id=user_id,
        username="testuser",
        password_hash="x",
        full_name="Test User",
        role_id=1,
        role_name=role_name,
        is_active=True,
        sucursales=sucursales,
    )


def _make_token(role_name: str = "admin", sucursales: list[int] | None = None) -> str:
    return create_access_token(
        user_id=1,
        username="testuser",
        role=role_name,
        sucursales=sucursales,
    )


def _make_cliente_row(**kwargs) -> dict:
    defaults = {
        "id_cliente": 1,
        "fantasia": "Bar El Sol",
        "razon_social": "Juan Perez SRL",
        "latitud": -34.6,
        "longitud": -58.4,
        "canal": "TRADICIONAL",
        "sucursal": "Sucursal A",
        "ruta": "1|10",
        "preventista": "Pedro Gomez",
        "bultos": 120.0,
        "facturacion": 6000.0,
        "documentos": 4,
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def app_ventas_mapa():
    from routers.ventas_mapa import router

    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client_mapa(app_ventas_mapa):
    return TestClient(app_ventas_mapa, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests de autenticación requerida
# ---------------------------------------------------------------------------

class TestAuthRequired:
    def test_clientes_without_token_returns_401(self, client_mapa):
        r = client_mapa.get(
            "/api/ventas-mapa/clientes",
            params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
        )
        assert r.status_code == 401

    def test_hover_without_token_returns_401(self, client_mapa):
        r = client_mapa.get(
            "/api/ventas-mapa/cliente/1/hover",
            params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
        )
        assert r.status_code == 401

    def test_clientes_with_invalid_token_returns_401(self, client_mapa):
        r = client_mapa.get(
            "/api/ventas-mapa/clientes",
            params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
            headers={"Authorization": "Bearer token_invalido"},
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Tests de endpoint /api/ventas-mapa/clientes
# ---------------------------------------------------------------------------

class TestGetMapaClientes:
    def _headers(self, role="admin", sucursales=None):
        token = _make_token(role_name=role, sucursales=sucursales)
        return {"Authorization": f"Bearer {token}"}

    def _mock_user(self, role="admin", sucursales=None):
        return _make_user(role_name=role, sucursales=sucursales)

    def test_admin_gets_results(self, client_mapa, monkeypatch):
        """Admin autenticado recibe lista de clientes."""
        user = self._mock_user("admin")
        rows = [_make_cliente_row()]

        monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: {
            "id": 1, "username": "testuser", "password_hash": "x",
            "full_name": "Test", "role_id": 1, "role_name": "admin", "is_active": True,
        })
        monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: None)

        with patch("routers.ventas_mapa.get_connection") as mock_conn, \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_clientes_mapa", return_value=rows):
            r = client_mapa.get(
                "/api/ventas-mapa/clientes",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=self._headers("admin"),
            )

        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id_cliente"] == 1
        assert data[0]["bultos"] == 120.0

    def test_empty_result_returns_empty_list(self, client_mapa, monkeypatch):
        """Sin clientes en el período retorna lista vacía."""
        monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: {
            "id": 1, "username": "testuser", "password_hash": "x",
            "full_name": "Test", "role_id": 1, "role_name": "admin", "is_active": True,
        })
        monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: None)

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_clientes_mapa", return_value=[]):
            r = client_mapa.get(
                "/api/ventas-mapa/clientes",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=self._headers("admin"),
            )

        assert r.status_code == 200
        assert r.json() == []

    def test_invalid_date_range_returns_400(self, client_mapa, monkeypatch):
        """fecha_ini > fecha_fin → 400."""
        monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: {
            "id": 1, "username": "testuser", "password_hash": "x",
            "full_name": "Test", "role_id": 1, "role_name": "admin", "is_active": True,
        })
        monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: None)

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_clientes_mapa", return_value=[]):
            r = client_mapa.get(
                "/api/ventas-mapa/clientes",
                params={"fecha_ini": "2024-02-01", "fecha_fin": "2024-01-01"},
                headers=self._headers("admin"),
            )

        assert r.status_code == 400

    def test_invalid_metrica_returns_400(self, client_mapa, monkeypatch):
        """Métrica inválida → 400."""
        monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: {
            "id": 1, "username": "testuser", "password_hash": "x",
            "full_name": "Test", "role_id": 1, "role_name": "admin", "is_active": True,
        })
        monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: None)

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_clientes_mapa", return_value=[]):
            r = client_mapa.get(
                "/api/ventas-mapa/clientes",
                params={
                    "fecha_ini": "2024-01-01",
                    "fecha_fin": "2024-01-31",
                    "metrica": "invalida",
                },
                headers=self._headers("admin"),
            )

        assert r.status_code == 400

    def test_db_error_returns_503(self, client_mapa, monkeypatch):
        """Error de DB → 503."""
        monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: {
            "id": 1, "username": "testuser", "password_hash": "x",
            "full_name": "Test", "role_id": 1, "role_name": "admin", "is_active": True,
        })
        monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: None)

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_clientes_mapa", side_effect=Exception("DB error")):
            r = client_mapa.get(
                "/api/ventas-mapa/clientes",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=self._headers("admin"),
            )

        assert r.status_code == 503

    def test_response_schema_valid(self, client_mapa, monkeypatch):
        """Respuesta respeta el schema VentasCliente."""
        monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: {
            "id": 1, "username": "testuser", "password_hash": "x",
            "full_name": "Test", "role_id": 1, "role_name": "admin", "is_active": True,
        })
        monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: None)

        rows = [_make_cliente_row(fantasia=None)]

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_clientes_mapa", return_value=rows):
            r = client_mapa.get(
                "/api/ventas-mapa/clientes",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=self._headers("admin"),
            )

        assert r.status_code == 200
        item = r.json()[0]
        # Validar campos requeridos del schema
        assert "id_cliente" in item
        assert "razon_social" in item
        assert "latitud" in item
        assert "longitud" in item
        assert "bultos" in item
        assert "facturacion" in item
        assert "documentos" in item
        assert item["fantasia"] is None  # Optional field


# ---------------------------------------------------------------------------
# Tests de endpoint /api/ventas-mapa/cliente/{id}/hover
# ---------------------------------------------------------------------------

class TestGetHover:
    def _headers(self, role="admin"):
        token = _make_token(role_name=role)
        return {"Authorization": f"Bearer {token}"}

    def _mock_auth(self, monkeypatch):
        monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: {
            "id": 1, "username": "testuser", "password_hash": "x",
            "full_name": "Test", "role_id": 1, "role_name": "admin", "is_active": True,
        })
        monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: None)

    def _hover_data(self):
        return {
            "id_cliente": 42,
            "razon_social": "Cliente Test",
            "genericos": [
                {"generico": "CERVEZAS", "m_act": 100.0, "m_ant": 80.0},
                {"generico": "AGUAS DANONE", "m_act": 50.0, "m_ant": 40.0},
            ],
        }

    def test_hover_returns_correct_structure(self, client_mapa, monkeypatch):
        """Hover retorna id_cliente, razon_social y lista de genéricos."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_hover_cliente", return_value=self._hover_data()):
            r = client_mapa.get(
                "/api/ventas-mapa/cliente/42/hover",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=self._headers(),
            )

        assert r.status_code == 200
        data = r.json()
        assert data["id_cliente"] == 42
        assert data["razon_social"] == "Cliente Test"
        assert isinstance(data["genericos"], list)

    def test_hover_generico_schema(self, client_mapa, monkeypatch):
        """Cada item de genericos tiene generico, m_act, m_ant."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_hover_cliente", return_value=self._hover_data()):
            r = client_mapa.get(
                "/api/ventas-mapa/cliente/42/hover",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=self._headers(),
            )

        g = r.json()["genericos"][0]
        assert "generico" in g
        assert "m_act" in g
        assert "m_ant" in g

    def test_hover_invalid_date_range_returns_400(self, client_mapa, monkeypatch):
        """fecha_ini > fecha_fin → 400."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_hover_cliente", return_value=self._hover_data()):
            r = client_mapa.get(
                "/api/ventas-mapa/cliente/42/hover",
                params={"fecha_ini": "2024-02-01", "fecha_fin": "2024-01-01"},
                headers=self._headers(),
            )

        assert r.status_code == 400

    def test_hover_db_error_returns_503(self, client_mapa, monkeypatch):
        """Error de DB → 503."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_hover_cliente", side_effect=Exception("DB fail")):
            r = client_mapa.get(
                "/api/ventas-mapa/cliente/42/hover",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=self._headers(),
            )

        assert r.status_code == 503
