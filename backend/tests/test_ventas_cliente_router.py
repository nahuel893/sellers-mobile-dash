"""
Tests de routers/ventas_cliente.py

TDD: tests escritos antes de la implementación.
Mockea buscar_clientes — sin DB real.
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


def _mock_auth(monkeypatch, role: str = "admin", sucursales=None):
    monkeypatch.setattr("auth.dependencies.get_user_by_username", lambda u, conn=None: {
        "id": 1, "username": "testuser", "password_hash": "x",
        "full_name": "Test", "role_id": 1, "role_name": role, "is_active": True,
    })
    monkeypatch.setattr("auth.dependencies.get_user_sucursales", lambda uid, conn=None: sucursales)


def _make_result_row(**kwargs) -> dict:
    defaults = {
        "id_cliente": 1,
        "razon_social": "JUAN PEREZ SRL",
        "fantasia": "Bar El Sol",
        "localidad": "Salta",
        "sucursal": "Salta Capital",
        "latitud": -24.7,
        "longitud": -65.4,
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def app_cliente():
    from routers.ventas_cliente import router
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client(app_cliente):
    return TestClient(app_cliente, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests de autenticación
# ---------------------------------------------------------------------------

class TestAuthRequired:
    def test_buscar_without_token_returns_401(self, client):
        r = client.get("/api/ventas-cliente/buscar", params={"q": "bar"})
        assert r.status_code == 401

    def test_buscar_with_invalid_token_returns_401(self, client):
        r = client.get(
            "/api/ventas-cliente/buscar",
            params={"q": "bar"},
            headers={"Authorization": "Bearer token_invalido"},
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Tests de /api/ventas-cliente/buscar
# ---------------------------------------------------------------------------

class TestBuscarClientes:
    def _headers(self, role: str = "admin") -> dict:
        return {"Authorization": f"Bearer {_make_token(role_name=role)}"}

    def test_returns_list_of_results(self, client, monkeypatch):
        """Con q válido y resultados en DB → 200 con lista."""
        _mock_auth(monkeypatch)
        rows = [_make_result_row()]

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch("routers.ventas_cliente.buscar_clientes", return_value=rows):
            r = client.get(
                "/api/ventas-cliente/buscar",
                params={"q": "bar"},
                headers=self._headers(),
            )

        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id_cliente"] == 1

    def test_empty_q_returns_empty_list(self, client, monkeypatch):
        """q de 1 carácter → 200 con lista vacía (sin llamar a buscar_clientes)."""
        _mock_auth(monkeypatch)

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch("routers.ventas_cliente.buscar_clientes", return_value=[]) as mock_svc:
            r = client.get(
                "/api/ventas-cliente/buscar",
                params={"q": "b"},
                headers=self._headers(),
            )

        assert r.status_code == 200
        assert r.json() == []

    def test_response_schema_has_all_fields(self, client, monkeypatch):
        """Respuesta tiene todos los campos del schema VentasClienteBusqueda."""
        _mock_auth(monkeypatch)
        rows = [_make_result_row()]

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch("routers.ventas_cliente.buscar_clientes", return_value=rows):
            r = client.get(
                "/api/ventas-cliente/buscar",
                params={"q": "bar"},
                headers=self._headers(),
            )

        item = r.json()[0]
        for field in ["id_cliente", "razon_social", "fantasia", "localidad", "sucursal", "latitud", "longitud"]:
            assert field in item, f"Campo faltante: {field}"

    def test_null_coords_serialized_correctly(self, client, monkeypatch):
        """Cliente sin coordenadas → latitud/longitud son null en JSON."""
        _mock_auth(monkeypatch)
        rows = [_make_result_row(latitud=None, longitud=None)]

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch("routers.ventas_cliente.buscar_clientes", return_value=rows):
            r = client.get(
                "/api/ventas-cliente/buscar",
                params={"q": "bar"},
                headers=self._headers(),
            )

        assert r.status_code == 200
        item = r.json()[0]
        assert item["latitud"] is None
        assert item["longitud"] is None

    def test_db_error_returns_503(self, client, monkeypatch):
        """Error de DB → 503."""
        _mock_auth(monkeypatch)

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch("routers.ventas_cliente.buscar_clientes", side_effect=Exception("DB error")):
            r = client.get(
                "/api/ventas-cliente/buscar",
                params={"q": "bar"},
                headers=self._headers(),
            )

        assert r.status_code == 503

    def test_limit_query_param_is_passed(self, client, monkeypatch):
        """El parámetro limit se pasa al servicio."""
        _mock_auth(monkeypatch)
        captured_limit = []

        def mock_buscar(conn, q, role_name, sucursales_usuario, limit=50):
            captured_limit.append(limit)
            return []

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch("routers.ventas_cliente.buscar_clientes", side_effect=mock_buscar):
            r = client.get(
                "/api/ventas-cliente/buscar",
                params={"q": "bar", "limit": 25},
                headers=self._headers(),
            )

        assert r.status_code == 200
        assert captured_limit == [25]


# ---------------------------------------------------------------------------
# Tests de GET /api/ventas-cliente/{id}
# ---------------------------------------------------------------------------

def _make_detalle_response(**kwargs) -> dict:
    """Respuesta completa de get_cliente_detalle."""
    defaults = {
        "info": {
            "id_cliente": 42,
            "fantasia": "Bar El Toro",
            "razon_social": "JUAN PEREZ SRL",
            "localidad": "Salta",
            "canal": "CAFETERIA",
            "sucursal": "Salta Capital",
            "preventista_fv1": "Pedro García",
            "ruta_fv1": "1|5",
            "lista_precio": "Lista A",
            "latitud": -24.7,
            "longitud": -65.4,
        },
        "kpis": {
            "bultos_mes": 120,
            "facturacion_mes": 85000.50,
            "documentos_mes": 3,
        },
        "tabla": [],
    }
    defaults.update(kwargs)
    return defaults


class TestGetClienteDetalle:
    def _headers(self, role: str = "admin") -> dict:
        return {"Authorization": f"Bearer {_make_token(role_name=role)}"}

    def test_returns_200_with_valid_id(self, client, monkeypatch):
        """GET /{id} con cliente existente → 200."""
        _mock_auth(monkeypatch)
        detalle = _make_detalle_response()

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch("routers.ventas_cliente.get_cliente_detalle", return_value=detalle):
            r = client.get("/api/ventas-cliente/42", headers=self._headers())

        assert r.status_code == 200

    def test_response_has_info_kpis_tabla(self, client, monkeypatch):
        """Respuesta contiene las secciones info, kpis, tabla."""
        _mock_auth(monkeypatch)
        detalle = _make_detalle_response()

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch("routers.ventas_cliente.get_cliente_detalle", return_value=detalle):
            r = client.get("/api/ventas-cliente/42", headers=self._headers())

        data = r.json()
        assert "info" in data
        assert "kpis" in data
        assert "tabla" in data

    def test_info_fields_correct(self, client, monkeypatch):
        """Campos de info son los esperados."""
        _mock_auth(monkeypatch)
        detalle = _make_detalle_response()

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch("routers.ventas_cliente.get_cliente_detalle", return_value=detalle):
            r = client.get("/api/ventas-cliente/42", headers=self._headers())

        info = r.json()["info"]
        assert info["id_cliente"] == 42
        assert info["fantasia"] == "Bar El Toro"

    def test_cliente_not_found_returns_404(self, client, monkeypatch):
        """get_cliente_detalle lanza 404 → se propaga al cliente."""
        _mock_auth(monkeypatch)
        from fastapi import HTTPException

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch(
                "routers.ventas_cliente.get_cliente_detalle",
                side_effect=HTTPException(status_code=404, detail="Cliente no encontrado"),
             ):
            r = client.get("/api/ventas-cliente/9999", headers=self._headers())

        assert r.status_code == 404

    def test_forbidden_sucursal_returns_403(self, client, monkeypatch):
        """get_cliente_detalle lanza 403 → se propaga."""
        _mock_auth(monkeypatch)
        from fastapi import HTTPException

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch(
                "routers.ventas_cliente.get_cliente_detalle",
                side_effect=HTTPException(status_code=403, detail="Acceso denegado"),
             ):
            r = client.get("/api/ventas-cliente/42", headers=self._headers("vendedor"))

        assert r.status_code == 403

    def test_without_token_returns_401(self, client):
        """Sin token → 401."""
        r = client.get("/api/ventas-cliente/42")
        assert r.status_code == 401

    def test_db_error_returns_503(self, client, monkeypatch):
        """Error inesperado de DB → 503."""
        _mock_auth(monkeypatch)

        with patch("routers.ventas_cliente.get_connection"), \
             patch("routers.ventas_cliente.release_connection"), \
             patch(
                "routers.ventas_cliente.get_cliente_detalle",
                side_effect=Exception("DB down"),
             ):
            r = client.get("/api/ventas-cliente/42", headers=self._headers())

        assert r.status_code == 503
