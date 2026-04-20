"""
Tests para services/ventas_cliente_service.py

TDD: tests escritos antes de la implementación.
Se mockea psycopg2 — sin base de datos real.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from services.ventas_cliente_service import buscar_clientes


# ---------------------------------------------------------------------------
# Helpers de mock
# ---------------------------------------------------------------------------

def _make_cursor(fetchall_return=None, description=None):
    cur = MagicMock()
    cur.fetchall.return_value = fetchall_return or []
    cur.description = description or [
        ("id_cliente",), ("razon_social",), ("fantasia",),
        ("localidad",), ("sucursal",), ("latitud",), ("longitud",),
    ]
    return cur


def _make_conn(cursor=None):
    conn = MagicMock()
    conn.cursor.return_value = cursor or _make_cursor()
    return conn


def _default_description():
    return [
        ("id_cliente",), ("razon_social",), ("fantasia",),
        ("localidad",), ("sucursal",), ("latitud",), ("longitud",),
    ]


# ---------------------------------------------------------------------------
# Tests de buscar_clientes
# ---------------------------------------------------------------------------

class TestBuscarClientes:

    def _row(self, id_cliente=1, razon_social="JUAN PEREZ SRL", fantasia="Bar El Sol",
             localidad="Salta", sucursal="Salta Capital", lat=-24.7, lon=-65.4):
        return (id_cliente, razon_social, fantasia, localidad, sucursal, lat, lon)

    def _make_typed_conn(self, rows):
        cur = _make_cursor(fetchall_return=rows, description=_default_description())
        return _make_conn(cursor=cur)

    # -- Resultados básicos --------------------------------------------------

    def test_returns_list_of_dicts(self):
        """buscar_clientes retorna lista de dicts con las claves correctas."""
        conn = self._make_typed_conn([self._row()])

        result = buscar_clientes(conn, "bar", "admin", None)

        assert isinstance(result, list)
        assert len(result) == 1
        r = result[0]
        assert "id_cliente" in r
        assert "razon_social" in r
        assert "fantasia" in r
        assert "localidad" in r
        assert "sucursal" in r
        assert "latitud" in r
        assert "longitud" in r

    def test_empty_result_when_no_match(self):
        """Sin matches en DB → lista vacía."""
        conn = self._make_typed_conn([])
        result = buscar_clientes(conn, "inexistente", "admin", None)
        assert result == []

    def test_returns_correct_values(self):
        """Los valores del dict coinciden con los de la fila DB."""
        conn = self._make_typed_conn([
            self._row(id_cliente=42, razon_social="ACME SRL", fantasia="Kiosco Acme",
                      localidad="Tartagal", sucursal="Orán", lat=-22.5, lon=-63.8)
        ])
        result = buscar_clientes(conn, "acme", "admin", None)

        r = result[0]
        assert r["id_cliente"] == 42
        assert r["razon_social"] == "ACME SRL"
        assert r["fantasia"] == "Kiosco Acme"
        assert r["localidad"] == "Tartagal"
        assert r["sucursal"] == "Orán"
        assert r["latitud"] == -22.5
        assert r["longitud"] == -63.8

    # -- RBAC ----------------------------------------------------------------

    def test_admin_query_has_no_sucursal_filter(self):
        """Admin (ROLES_SIN_FILTRO_SUCURSAL) → query sin filtro de sucursal."""
        executed: list[str] = []

        cur = _make_cursor(fetchall_return=[], description=_default_description())

        def capture(sql, params=None):
            executed.append(sql if isinstance(sql, str) else str(sql))

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        buscar_clientes(conn, "bar", "admin", [1, 2, 3])

        assert len(executed) == 1
        assert "ANY(%(sucursales)s)" not in executed[0]

    def test_gerente_query_has_no_sucursal_filter(self):
        """Gerente → sin filtro de sucursal."""
        executed: list[str] = []
        cur = _make_cursor(fetchall_return=[], description=_default_description())

        def capture(sql, params=None):
            executed.append(sql if isinstance(sql, str) else str(sql))

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        buscar_clientes(conn, "sol", "gerente", [5])

        assert "ANY(%(sucursales)s)" not in executed[0]

    def test_supervisor_query_has_sucursal_filter(self):
        """Supervisor → WHERE id_sucursal = ANY(%(sucursales)s)."""
        executed: list[str] = []
        params_cap: list = []
        cur = _make_cursor(fetchall_return=[], description=_default_description())

        def capture(sql, params=None):
            executed.append(sql if isinstance(sql, str) else str(sql))
            params_cap.append(params or {})

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        buscar_clientes(conn, "sol", "supervisor", [1, 3])

        assert "ANY(%(sucursales)s)" in executed[0]
        assert params_cap[0]["sucursales"] == [1, 3]

    def test_supervisor_without_sucursales_no_filter(self):
        """Supervisor sin sucursales asignadas → sin filtro (no debe crashear)."""
        executed: list[str] = []
        cur = _make_cursor(fetchall_return=[], description=_default_description())

        def capture(sql, params=None):
            executed.append(sql if isinstance(sql, str) else str(sql))

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        buscar_clientes(conn, "test", "supervisor", None)
        assert len(executed) == 1

    # -- Params del query ----------------------------------------------------

    def test_q_is_passed_as_ilike_pattern(self):
        """El término de búsqueda se pasa como patrón ILIKE %q%."""
        params_cap: list = []
        cur = _make_cursor(fetchall_return=[], description=_default_description())

        def capture(sql, params=None):
            params_cap.append(params or {})

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        buscar_clientes(conn, "sol", "admin", None)

        p = params_cap[0]
        assert "q_ilike" in p
        assert "%sol%" in p["q_ilike"]

    def test_limit_default_is_50(self):
        """Sin limit explícito, se usa 50."""
        params_cap: list = []
        cur = _make_cursor(fetchall_return=[], description=_default_description())

        def capture(sql, params=None):
            params_cap.append(params or {})

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        buscar_clientes(conn, "bar", "admin", None)

        assert params_cap[0]["limit"] == 50

    def test_limit_custom_is_respected(self):
        """limit personalizado se pasa al query."""
        params_cap: list = []
        cur = _make_cursor(fetchall_return=[], description=_default_description())

        def capture(sql, params=None):
            params_cap.append(params or {})

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        buscar_clientes(conn, "bar", "admin", None, limit=10)

        assert params_cap[0]["limit"] == 10

    def test_limit_capped_at_200(self):
        """limit > 200 se recorta a 200."""
        params_cap: list = []
        cur = _make_cursor(fetchall_return=[], description=_default_description())

        def capture(sql, params=None):
            params_cap.append(params or {})

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        buscar_clientes(conn, "bar", "admin", None, limit=500)

        assert params_cap[0]["limit"] == 200

    def test_q_less_than_2_chars_returns_empty(self):
        """q con menos de 2 caracteres retorna lista vacía sin ejecutar query."""
        conn = _make_conn()
        result = buscar_clientes(conn, "a", "admin", None)
        assert result == []
        conn.cursor.assert_not_called()

    def test_q_empty_returns_empty(self):
        """q vacío retorna lista vacía sin ejecutar query."""
        conn = _make_conn()
        result = buscar_clientes(conn, "", "admin", None)
        assert result == []
        conn.cursor.assert_not_called()

    # -- Coords opcionales ---------------------------------------------------

    def test_null_coords_are_preserved(self):
        """latitud/longitud pueden ser None (cliente sin coordenadas)."""
        row = (99, "SIN COORDS SRL", None, "Capital", "Salta", None, None)
        cur = _make_cursor(fetchall_return=[row], description=_default_description())
        conn = _make_conn(cursor=cur)

        result = buscar_clientes(conn, "sin", "admin", None)

        assert result[0]["latitud"] is None
        assert result[0]["longitud"] is None
