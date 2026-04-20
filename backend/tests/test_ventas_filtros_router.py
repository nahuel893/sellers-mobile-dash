"""
Tests de routers/ventas_filtros.py

TDD: tests escritos antes de la implementación.
Mockea get_filtros_opciones — sin DB real.
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

def _make_token(role_name: str = "admin", sucursales: list[int] | None = None) -> str:
    return create_access_token(
        user_id=1,
        username="testuser",
        role=role_name,
        sucursales=sucursales,
    )


def _opciones_base() -> dict:
    return {
        "canales": ["TRADICIONAL", "MODERNO"],
        "subcanales": ["BAR", "KIOSKO"],
        "localidades": ["SALTA", "JUJUY"],
        "listas_precio": [{"id_lista_precio": 1, "des_lista_precio": "Lista A"}],
        "sucursales": [{"id_sucursal": 1, "des_sucursal": "Casa Central"}],
        "rutas": ["1|10", "1|20"],
        "preventistas": ["Preventista A", "Preventista B"],
        "genericos": ["CERVEZAS", "AGUAS DANONE"],
        "marcas": ["SALTA", "HEINEKEN"],
        "fecha_min": "2024-01-01",
        "fecha_max": "2024-12-31",
    }


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def app_filtros():
    from routers.ventas_filtros import router

    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client_filtros(app_filtros):
    return TestClient(app_filtros, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests de autenticación requerida
# ---------------------------------------------------------------------------

class TestFiltrosAuthRequired:
    def test_opciones_without_token_returns_401(self, client_filtros):
        r = client_filtros.get("/api/ventas-filtros/opciones")
        assert r.status_code == 401

    def test_opciones_with_invalid_token_returns_401(self, client_filtros):
        r = client_filtros.get(
            "/api/ventas-filtros/opciones",
            headers={"Authorization": "Bearer token_invalido"},
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Tests de endpoint /api/ventas-filtros/opciones
# ---------------------------------------------------------------------------

class TestGetOpcionesFiltros:
    def _headers(self, role="admin", sucursales=None):
        token = _make_token(role_name=role, sucursales=sucursales)
        return {"Authorization": f"Bearer {token}"}

    def _mock_auth(self, monkeypatch, role="admin", sucursales=None):
        monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: {
            "id": 1, "username": "testuser", "password_hash": "x",
            "full_name": "Test", "role_id": 1, "role_name": role, "is_active": True,
        })
        monkeypatch.setattr(
            "auth.dependencies.get_user_sucursales",
            lambda uid, conn=None: sucursales,
        )

    def test_admin_gets_all_categories(self, client_filtros, monkeypatch):
        """Admin autenticado recibe todas las categorías de opciones."""
        self._mock_auth(monkeypatch, role="admin")

        with patch("routers.ventas_filtros.get_connection"), \
             patch("routers.ventas_filtros.release_connection"), \
             patch("routers.ventas_filtros.get_filtros_opciones", return_value=_opciones_base()):
            r = client_filtros.get(
                "/api/ventas-filtros/opciones",
                headers=self._headers("admin"),
            )

        assert r.status_code == 200
        data = r.json()
        assert "canales" in data
        assert "subcanales" in data
        assert "localidades" in data
        assert "listas_precio" in data
        assert "sucursales" in data
        assert "rutas" in data
        assert "preventistas" in data
        assert "genericos" in data
        assert "marcas" in data
        assert "fecha_min" in data
        assert "fecha_max" in data

    def test_admin_sees_all_data(self, client_filtros, monkeypatch):
        """Admin ve todos los canales/sucursales sin restricción."""
        self._mock_auth(monkeypatch, role="admin")

        with patch("routers.ventas_filtros.get_connection"), \
             patch("routers.ventas_filtros.release_connection"), \
             patch("routers.ventas_filtros.get_filtros_opciones", return_value=_opciones_base()) as mock_service:
            r = client_filtros.get(
                "/api/ventas-filtros/opciones",
                headers=self._headers("admin"),
            )
            # Verificar que el servicio fue llamado con role_name="admin" y sucursales=None
            call_args = mock_service.call_args
            assert call_args.kwargs["role_name"] == "admin"
            assert call_args.kwargs["sucursales_usuario"] is None

        assert r.status_code == 200

    def test_supervisor_filtered_by_sucursales(self, client_filtros, monkeypatch):
        """Supervisor pasa sus sucursales al servicio para filtrar."""
        self._mock_auth(monkeypatch, role="supervisor", sucursales=[1, 2])

        opciones = _opciones_base()
        opciones["sucursales"] = [{"id_sucursal": 1, "des_sucursal": "Casa Central"}]

        with patch("routers.ventas_filtros.get_connection"), \
             patch("routers.ventas_filtros.release_connection"), \
             patch("routers.ventas_filtros.get_filtros_opciones", return_value=opciones) as mock_service:
            r = client_filtros.get(
                "/api/ventas-filtros/opciones",
                headers=self._headers("supervisor", sucursales=[1, 2]),
            )
            call_args = mock_service.call_args
            assert call_args.kwargs["role_name"] == "supervisor"
            assert call_args.kwargs["sucursales_usuario"] == [1, 2]

        assert r.status_code == 200

    def test_lista_precio_schema(self, client_filtros, monkeypatch):
        """listas_precio tiene los campos id_lista_precio y des_lista_precio."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_filtros.get_connection"), \
             patch("routers.ventas_filtros.release_connection"), \
             patch("routers.ventas_filtros.get_filtros_opciones", return_value=_opciones_base()):
            r = client_filtros.get(
                "/api/ventas-filtros/opciones",
                headers=self._headers(),
            )

        data = r.json()
        assert len(data["listas_precio"]) == 1
        lp = data["listas_precio"][0]
        assert "id_lista_precio" in lp
        assert "des_lista_precio" in lp

    def test_sucursal_option_schema(self, client_filtros, monkeypatch):
        """sucursales tiene los campos id_sucursal y des_sucursal."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_filtros.get_connection"), \
             patch("routers.ventas_filtros.release_connection"), \
             patch("routers.ventas_filtros.get_filtros_opciones", return_value=_opciones_base()):
            r = client_filtros.get(
                "/api/ventas-filtros/opciones",
                headers=self._headers(),
            )

        data = r.json()
        suc = data["sucursales"][0]
        assert "id_sucursal" in suc
        assert "des_sucursal" in suc

    def test_rutas_as_composite_key(self, client_filtros, monkeypatch):
        """Las rutas tienen formato 'id_sucursal|id_ruta'."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_filtros.get_connection"), \
             patch("routers.ventas_filtros.release_connection"), \
             patch("routers.ventas_filtros.get_filtros_opciones", return_value=_opciones_base()):
            r = client_filtros.get(
                "/api/ventas-filtros/opciones",
                headers=self._headers(),
            )

        data = r.json()
        for ruta in data["rutas"]:
            assert "|" in ruta, f"Ruta sin formato compuesto: {ruta!r}"

    def test_db_error_returns_503(self, client_filtros, monkeypatch):
        """Error de DB → 503."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_filtros.get_connection"), \
             patch("routers.ventas_filtros.release_connection"), \
             patch("routers.ventas_filtros.get_filtros_opciones", side_effect=Exception("DB fail")):
            r = client_filtros.get(
                "/api/ventas-filtros/opciones",
                headers=self._headers(),
            )

        assert r.status_code == 503

    def test_fecha_min_max_in_response(self, client_filtros, monkeypatch):
        """fecha_min y fecha_max están presentes en la respuesta."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_filtros.get_connection"), \
             patch("routers.ventas_filtros.release_connection"), \
             patch("routers.ventas_filtros.get_filtros_opciones", return_value=_opciones_base()):
            r = client_filtros.get(
                "/api/ventas-filtros/opciones",
                headers=self._headers(),
            )

        data = r.json()
        assert data["fecha_min"] == "2024-01-01"
        assert data["fecha_max"] == "2024-12-31"

    def test_accepts_fv_param(self, client_filtros, monkeypatch):
        """El endpoint acepta el parámetro fv sin errores."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_filtros.get_connection"), \
             patch("routers.ventas_filtros.release_connection"), \
             patch("routers.ventas_filtros.get_filtros_opciones", return_value=_opciones_base()):
            r = client_filtros.get(
                "/api/ventas-filtros/opciones",
                params={"fv": "1"},
                headers=self._headers(),
            )

        assert r.status_code == 200

    def test_accepts_fecha_params(self, client_filtros, monkeypatch):
        """El endpoint acepta fecha_ini y fecha_fin sin errores."""
        self._mock_auth(monkeypatch)

        with patch("routers.ventas_filtros.get_connection"), \
             patch("routers.ventas_filtros.release_connection"), \
             patch("routers.ventas_filtros.get_filtros_opciones", return_value=_opciones_base()):
            r = client_filtros.get(
                "/api/ventas-filtros/opciones",
                params={"fecha_ini": "2024-01-01", "fecha_fin": "2024-03-31"},
                headers=self._headers(),
            )

        assert r.status_code == 200
