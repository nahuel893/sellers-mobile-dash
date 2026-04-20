"""
Tests para GET /api/ventas-mapa/zonas

TDD: tests escritos antes de la implementación final.
Mockea get_zonas — sin base de datos real.
Mismo patrón de auth que test_ventas_mapa_router.py.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.jwt import create_access_token
from auth.models import UserInDB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(role_name: str = "admin", sucursales: list[int] | None = None) -> UserInDB:
    return UserInDB(
        id=1,
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


def _headers(role_name: str = "admin", sucursales: list[int] | None = None) -> dict:
    return {"Authorization": f"Bearer {_make_token(role_name, sucursales)}"}


def _mock_auth(monkeypatch):
    monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: {
        "id": 1, "username": "testuser", "password_hash": "x",
        "full_name": "Test", "role_id": 1, "role_name": "admin", "is_active": True,
    })
    monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: None)


def _make_zona_dict(**kwargs) -> dict:
    defaults = {
        "nombre": "1|10",
        "color_idx": 0,
        "coords": [[-65.41, -24.78], [-65.42, -24.79], [-65.40, -24.77]],
        "n_clientes": 3,
        "metricas": {
            "bultos_m_act": 100.0,
            "bultos_m_ant": 80.0,
            "compradores_m_act": 3,
            "compradores_m_ant": 2,
            "por_generico": [{"generico": "CERVEZAS", "m_act": 100.0, "m_ant": 80.0}],
        },
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def app_zonas():
    from routers.ventas_mapa import router
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client_zonas(app_zonas):
    return TestClient(app_zonas, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetMapaZonas:
    def test_ok_devuelve_lista_zonas(self, client_zonas, monkeypatch):
        _mock_auth(monkeypatch)
        with (
            patch("routers.ventas_mapa.get_connection"),
            patch("routers.ventas_mapa.release_connection"),
            patch("routers.ventas_mapa.get_zonas", return_value=[_make_zona_dict()]),
        ):
            resp = client_zonas.get(
                "/api/ventas-mapa/zonas",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=_headers(),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["nombre"] == "1|10"
        assert len(data[0]["coords"]) == 3

    def test_lista_vacia_cuando_no_hay_zonas(self, client_zonas, monkeypatch):
        _mock_auth(monkeypatch)
        with (
            patch("routers.ventas_mapa.get_connection"),
            patch("routers.ventas_mapa.release_connection"),
            patch("routers.ventas_mapa.get_zonas", return_value=[]),
        ):
            resp = client_zonas.get(
                "/api/ventas-mapa/zonas",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=_headers(),
            )

        assert resp.status_code == 200
        assert resp.json() == []

    def test_fecha_ini_posterior_a_fecha_fin_retorna_400(self, client_zonas, monkeypatch):
        _mock_auth(monkeypatch)
        with (
            patch("routers.ventas_mapa.get_connection"),
            patch("routers.ventas_mapa.release_connection"),
        ):
            resp = client_zonas.get(
                "/api/ventas-mapa/zonas",
                params={"fecha_ini": "2024-02-01", "fecha_fin": "2024-01-01"},
                headers=_headers(),
            )

        assert resp.status_code == 400
        assert "fecha_ini" in resp.json()["detail"]

    def test_agrupacion_invalida_retorna_400(self, client_zonas, monkeypatch):
        _mock_auth(monkeypatch)
        with (
            patch("routers.ventas_mapa.get_connection"),
            patch("routers.ventas_mapa.release_connection"),
        ):
            resp = client_zonas.get(
                "/api/ventas-mapa/zonas",
                params={
                    "fecha_ini": "2024-01-01",
                    "fecha_fin": "2024-01-31",
                    "agrupacion": "invalida",
                },
                headers=_headers(),
            )

        assert resp.status_code == 400

    def test_agrupacion_preventista_aceptada(self, client_zonas, monkeypatch):
        _mock_auth(monkeypatch)
        with (
            patch("routers.ventas_mapa.get_connection"),
            patch("routers.ventas_mapa.release_connection"),
            patch("routers.ventas_mapa.get_zonas", return_value=[]),
        ):
            resp = client_zonas.get(
                "/api/ventas-mapa/zonas",
                params={
                    "fecha_ini": "2024-01-01",
                    "fecha_fin": "2024-01-31",
                    "agrupacion": "preventista",
                },
                headers=_headers(),
            )

        assert resp.status_code == 200

    def test_error_db_retorna_503(self, client_zonas, monkeypatch):
        _mock_auth(monkeypatch)
        with (
            patch("routers.ventas_mapa.get_connection"),
            patch("routers.ventas_mapa.release_connection"),
            patch("routers.ventas_mapa.get_zonas", side_effect=RuntimeError("DB down")),
        ):
            resp = client_zonas.get(
                "/api/ventas-mapa/zonas",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=_headers(),
            )

        assert resp.status_code == 503

    def test_metricas_estructura_correcta(self, client_zonas, monkeypatch):
        _mock_auth(monkeypatch)
        zona = _make_zona_dict()
        with (
            patch("routers.ventas_mapa.get_connection"),
            patch("routers.ventas_mapa.release_connection"),
            patch("routers.ventas_mapa.get_zonas", return_value=[zona]),
        ):
            resp = client_zonas.get(
                "/api/ventas-mapa/zonas",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
                headers=_headers(),
            )

        assert resp.status_code == 200
        data = resp.json()
        m = data[0]["metricas"]
        assert "bultos_m_act" in m
        assert "bultos_m_ant" in m
        assert "compradores_m_act" in m
        assert "compradores_m_ant" in m
        assert isinstance(m["por_generico"], list)

    def test_sin_token_retorna_401(self, client_zonas):
        resp = client_zonas.get(
            "/api/ventas-mapa/zonas",
            params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-01-31"},
        )
        assert resp.status_code == 401
