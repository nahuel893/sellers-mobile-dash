"""
Tests de routers/ventas_mapa.py — endpoint GET /api/ventas-mapa/compro

TDD: tests escritos antes de la implementación del endpoint.
Mockea get_compro_data — sin DB real.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.jwt import create_access_token
from auth.models import UserInDB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_token(role_name: str = "admin", sucursales: list[int] | None = None) -> str:
    return create_access_token(
        user_id=1,
        username="testuser",
        role=role_name,
        sucursales=sucursales,
    )


def _make_compro_row(**kwargs) -> dict:
    defaults = {
        "id_cliente": 1,
        "lat": -24.79,
        "lon": -65.41,
        "compro": True,
        "ultima_compra": date(2024, 1, 15),
    }
    defaults.update(kwargs)
    return defaults


def _mock_auth(monkeypatch):
    monkeypatch.setattr(
        "auth.dependencies.get_user_by_username",
        lambda u, conn=None: {
            "id": 1,
            "username": "testuser",
            "password_hash": "x",
            "full_name": "Test",
            "role_id": 1,
            "role_name": "admin",
            "is_active": True,
        },
    )
    monkeypatch.setattr(
        "auth.dependencies.get_user_sucursales",
        lambda uid, conn=None: None,
    )


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def app_compro():
    from routers.ventas_mapa import router

    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client_compro(app_compro):
    return TestClient(app_compro, raise_server_exceptions=False)


def _headers(role: str = "admin") -> dict:
    return {"Authorization": f"Bearer {_make_token(role_name=role)}"}


# ---------------------------------------------------------------------------
# Tests: autenticación
# ---------------------------------------------------------------------------

class TestComproAuthRequired:
    def test_without_token_returns_401(self, client_compro):
        r = client_compro.get(
            "/api/ventas-mapa/compro",
            params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
        )
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, client_compro):
        r = client_compro.get(
            "/api/ventas-mapa/compro",
            params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
            headers={"Authorization": "Bearer token_invalido"},
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Tests: validación de parámetros
# ---------------------------------------------------------------------------

class TestComproValidation:
    def test_invalid_date_range_returns_400(self, client_compro, monkeypatch):
        """fecha_ini > fecha_fin → 400."""
        _mock_auth(monkeypatch)
        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_compro_data", return_value=[]):
            r = client_compro.get(
                "/api/ventas-mapa/compro",
                params={"fecha_ini": "2024-02-01", "fecha_fin": "2024-01-01"},
                headers=_headers(),
            )
        assert r.status_code == 400

    def test_missing_fecha_ini_returns_422(self, client_compro, monkeypatch):
        """Sin fecha_ini → 422 (FastAPI validation)."""
        _mock_auth(monkeypatch)
        r = client_compro.get(
            "/api/ventas-mapa/compro",
            params={"fecha_fin": "2024-01-31"},
            headers=_headers(),
        )
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Tests: respuesta
# ---------------------------------------------------------------------------

class TestComproResponse:
    def test_returns_list_with_compro_fields(self, client_compro, monkeypatch):
        """Respuesta incluye id_cliente, lat, lon, compro, ultima_compra."""
        _mock_auth(monkeypatch)
        rows = [_make_compro_row()]

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_compro_data", return_value=rows):
            r = client_compro.get(
                "/api/ventas-mapa/compro",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=_headers(),
            )

        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 1
        item = data[0]
        assert item["id_cliente"] == 1
        assert item["lat"] == -24.79
        assert item["lon"] == -65.41
        assert item["compro"] is True
        assert item["ultima_compra"] == "2024-01-15"

    def test_ultima_compra_null_serializes_correctly(self, client_compro, monkeypatch):
        """ultima_compra=None se serializa como null en JSON."""
        _mock_auth(monkeypatch)
        rows = [_make_compro_row(ultima_compra=None)]

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_compro_data", return_value=rows):
            r = client_compro.get(
                "/api/ventas-mapa/compro",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=_headers(),
            )

        assert r.status_code == 200
        item = r.json()[0]
        assert item["ultima_compra"] is None

    def test_empty_result_returns_empty_list(self, client_compro, monkeypatch):
        """Sin clientes → lista vacía."""
        _mock_auth(monkeypatch)

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_compro_data", return_value=[]):
            r = client_compro.get(
                "/api/ventas-mapa/compro",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=_headers(),
            )

        assert r.status_code == 200
        assert r.json() == []

    def test_db_error_returns_503(self, client_compro, monkeypatch):
        """Error de DB → 503."""
        _mock_auth(monkeypatch)

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_compro_data", side_effect=Exception("DB boom")):
            r = client_compro.get(
                "/api/ventas-mapa/compro",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=_headers(),
            )

        assert r.status_code == 503

    def test_mixed_compro_no_compro(self, client_compro, monkeypatch):
        """Lista con compradores y no-compradores mezclados."""
        _mock_auth(monkeypatch)
        rows = [
            _make_compro_row(id_cliente=1, compro=True),
            _make_compro_row(id_cliente=2, compro=False, ultima_compra=date(2023, 11, 1)),
        ]

        with patch("routers.ventas_mapa.get_connection"), \
             patch("routers.ventas_mapa.release_connection"), \
             patch("routers.ventas_mapa.get_compro_data", return_value=rows):
            r = client_compro.get(
                "/api/ventas-mapa/compro",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=_headers(),
            )

        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["compro"] is True
        assert data[1]["compro"] is False
