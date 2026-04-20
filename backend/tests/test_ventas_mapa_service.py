"""
Tests para services/ventas_mapa_service.py

TDD: todos los tests escritos antes de la implementación final.
Se mockea psycopg2 — sin base de datos real.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch, call

import pytest

from services.ventas_mapa_service import (
    get_filtros_opciones,
    get_clientes_mapa,
    get_hover_cliente,
    _sucursal_filter,
    _fv_join_columns,
    _fv_fact_ventas_filter,
    _get_articulo_ids,
)
from ventas_constants import (
    FV_PREVENTA,
    FV_AUTOVENTA,
    FV_AMBAS,
    GENERICOS_HOVER_FIJOS,
    ROLES_SIN_FILTRO_SUCURSAL,
)


# ---------------------------------------------------------------------------
# Helpers de mock
# ---------------------------------------------------------------------------

def _make_cursor(fetchall_return=None, fetchone_return=None, description=None):
    """Crea un cursor mock con los retornos especificados."""
    cur = MagicMock()
    cur.fetchall.return_value = fetchall_return or []
    cur.fetchone.return_value = fetchone_return
    cur.description = description or [
        ("col1",), ("col2",)
    ]
    return cur


def _make_conn(cursor=None):
    """Crea una conexión mock que devuelve el cursor dado."""
    conn = MagicMock()
    conn.cursor.return_value = cursor or _make_cursor()
    return conn


# ---------------------------------------------------------------------------
# Tests de helpers internos
# ---------------------------------------------------------------------------

class TestSucursalFilter:
    def test_admin_no_filter(self):
        sql, params = _sucursal_filter([1, 2], "admin", "c")
        assert sql == ""
        assert params == {}

    def test_gerente_no_filter(self):
        sql, params = _sucursal_filter([3], "gerente", "c")
        assert sql == ""
        assert params == {}

    def test_supervisor_with_sucursales(self):
        sql, params = _sucursal_filter([1, 2], "supervisor", "c")
        assert "id_sucursal = ANY(%(sucursales)s)" in sql
        assert params["sucursales"] == [1, 2]

    def test_no_sucursales_no_filter(self):
        """Si el usuario no tiene sucursales asignadas y no es admin, tampoco filtra."""
        sql, params = _sucursal_filter(None, "supervisor", "c")
        assert sql == ""

    def test_custom_table_alias(self):
        sql, params = _sucursal_filter([1], "vendedor", "x")
        assert "x.id_sucursal" in sql


class TestFvHelpers:
    def test_fv1_columns(self):
        ruta_col, prev_col = _fv_join_columns(FV_PREVENTA)
        assert ruta_col == "id_ruta_fv1"
        assert prev_col == "des_personal_fv1"

    def test_fv4_columns(self):
        ruta_col, prev_col = _fv_join_columns(FV_AUTOVENTA)
        assert ruta_col == "id_ruta_fv4"
        assert prev_col == "des_personal_fv4"

    def test_ambas_uses_fv1(self):
        ruta_col, prev_col = _fv_join_columns(FV_AMBAS)
        assert ruta_col == "id_ruta_fv1"

    def test_fv1_fact_filter(self):
        sql, params = _fv_fact_ventas_filter(FV_PREVENTA)
        assert "id_fuerza_ventas" in sql
        assert params["fv_id"] == 1

    def test_fv4_fact_filter(self):
        sql, params = _fv_fact_ventas_filter(FV_AUTOVENTA)
        assert params["fv_id"] == 4

    def test_ambas_no_filter(self):
        sql, params = _fv_fact_ventas_filter(FV_AMBAS)
        assert sql == ""
        assert params == {}


# ---------------------------------------------------------------------------
# Tests de get_filtros_opciones
# ---------------------------------------------------------------------------

class TestGetFiltrosOpciones:
    def _make_multi_cursor(self, side_effects):
        """
        Cursor que retorna distintos fetchall por cada ejecución de execute.
        """
        cur = MagicMock()
        # fetchall se llama una vez por cada execute; usamos side_effect
        cur.fetchall.side_effect = side_effects
        return cur

    def test_returns_all_categories(self):
        """get_filtros_opciones retorna todas las claves esperadas."""
        # 10 queries: canales, subcanales, localidades, listas_precio,
        # sucursales, rutas, preventistas, genericos, marcas, rango_fechas
        side_effects = [
            [("canal1",)],                          # canales
            [("sub1",)],                            # subcanales
            [("loc1",)],                            # localidades
            [(1, "Lista A")],                       # listas_precio
            [(1, "Sucursal A")],                    # sucursales
            [(1, 10)],                              # rutas
            [("Preventista A",)],                   # preventistas
            [("CERVEZAS",)],                        # genericos
            [("SALTA",)],                           # marcas
        ]
        # last query (fetchone for rango_fechas)
        cur = self._make_multi_cursor(side_effects)
        cur.fetchone.return_value = ("2024-01-01", "2024-12-31")
        conn = _make_conn(cursor=cur)

        result = get_filtros_opciones(conn, "admin", None)

        assert "canales" in result
        assert "subcanales" in result
        assert "localidades" in result
        assert "listas_precio" in result
        assert "sucursales" in result
        assert "rutas" in result
        assert "preventistas" in result
        assert "genericos" in result
        assert "marcas" in result
        assert "fecha_min" in result
        assert "fecha_max" in result

    def test_admin_sees_all_sucursales(self):
        """Admin no recibe filtro de sucursal en las queries."""
        executed_sqls: list[str] = []

        cur = MagicMock()
        cur.fetchall.return_value = []
        cur.fetchone.return_value = (None, None)

        original_execute = cur.execute

        def capture_execute(sql, params=None):
            executed_sqls.append(sql)

        cur.execute.side_effect = capture_execute
        conn = _make_conn(cursor=cur)

        get_filtros_opciones(conn, "admin", [1, 2])

        # Ninguna query debe tener filtro de sucursal
        for sql in executed_sqls:
            assert "ANY(%(sucursales)s)" not in sql

    def test_supervisor_filtered_by_sucursales(self):
        """Supervisor recibe filtro de sucursal en las queries."""
        executed_sqls: list[str] = []

        cur = MagicMock()
        cur.fetchall.return_value = []
        cur.fetchone.return_value = (None, None)

        def capture_execute(sql, params=None):
            executed_sqls.append(sql if isinstance(sql, str) else str(sql))

        cur.execute.side_effect = capture_execute
        conn = _make_conn(cursor=cur)

        get_filtros_opciones(conn, "supervisor", [1, 2])

        # Al menos la query de canales debe tener filtro de sucursal
        canales_sql = executed_sqls[0]
        assert "ANY(%(sucursales)s)" in canales_sql

    def test_rutas_formatted_as_composite_key(self):
        """Las rutas se formatean como 'id_sucursal|id_ruta'."""
        side_effects = [
            [],   # canales
            [],   # subcanales
            [],   # localidades
            [],   # listas_precio
            [],   # sucursales
            [(1, 10), (2, 20)],   # rutas raw: (id_sucursal, id_ruta)
            [],   # preventistas
            [],   # genericos
            [],   # marcas
        ]
        cur = self._make_multi_cursor(side_effects)
        cur.fetchone.return_value = (None, None)
        conn = _make_conn(cursor=cur)

        result = get_filtros_opciones(conn, "admin", None)

        assert "1|10" in result["rutas"]
        assert "2|20" in result["rutas"]


# ---------------------------------------------------------------------------
# Tests de get_clientes_mapa
# ---------------------------------------------------------------------------

class TestGetClientesMapa:
    _FECHA_INI = date(2024, 1, 1)
    _FECHA_FIN = date(2024, 1, 31)

    def _make_cliente_cursor(self, rows):
        """Cursor con description completa para get_clientes_mapa."""
        description = [
            ("id_cliente",), ("fantasia",), ("razon_social",),
            ("latitud",), ("longitud",),
            ("canal",), ("sucursal",), ("ruta",), ("preventista",),
            ("bultos",), ("facturacion",), ("documentos",),
        ]
        cur = _make_cursor(fetchall_return=rows, description=description)
        return cur

    def test_admin_sees_all_no_sucursal_filter(self):
        """Admin (sucursales=None) → no WHERE de sucursal en la query."""
        executed_sqls: list[str] = []
        cur = self._make_cliente_cursor([])

        def capture(sql, params=None):
            executed_sqls.append(sql if isinstance(sql, str) else str(sql))

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        get_clientes_mapa(
            conn, "admin", None,
            self._FECHA_INI, self._FECHA_FIN,
        )

        assert len(executed_sqls) == 1
        sql = executed_sqls[0]
        assert "ANY(%(sucursales)s)" not in sql

    def test_supervisor_filtered_by_sucursales(self):
        """Supervisor → WHERE id_sucursal = ANY(%(sucursales)s)."""
        executed_sqls: list[str] = []
        params_captured: list[dict] = []
        cur = self._make_cliente_cursor([])

        def capture(sql, params=None):
            executed_sqls.append(sql if isinstance(sql, str) else str(sql))
            params_captured.append(params or {})

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        get_clientes_mapa(
            conn, "supervisor", [1, 2],
            self._FECHA_INI, self._FECHA_FIN,
        )

        sql = executed_sqls[0]
        assert "ANY(%(sucursales)s)" in sql
        assert params_captured[0]["sucursales"] == [1, 2]

    def test_with_canal_filter(self):
        """Filtro por canal se agrega al WHERE."""
        executed_sqls: list[str] = []
        params_captured: list[dict] = []
        cur = self._make_cliente_cursor([])

        def capture(sql, params=None):
            executed_sqls.append(sql if isinstance(sql, str) else str(sql))
            params_captured.append(params or {})

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        get_clientes_mapa(
            conn, "admin", None,
            self._FECHA_INI, self._FECHA_FIN,
            canal="TRADICIONAL",
        )

        sql = executed_sqls[0]
        assert "des_canal_mkt" in sql
        assert params_captured[0]["canal"] == "TRADICIONAL"

    def test_with_genericos_filter_empty_result(self):
        """Si no hay artículos para los genéricos, retorna lista vacía sin ejecutar query principal."""
        # Mock _get_articulo_ids retornando lista vacía
        cur = _make_cursor(fetchall_return=[])  # Para la query de artículos
        conn = _make_conn(cursor=cur)

        result = get_clientes_mapa(
            conn, "admin", None,
            self._FECHA_INI, self._FECHA_FIN,
            genericos=["GENERICO_INEXISTENTE"],
        )

        assert result == []

    def test_with_genericos_filter_with_articles(self):
        """Filtro por genéricos → articulo_ids se pasan al join de fact_ventas."""
        executed_sqls: list[str] = []
        params_captured: list[dict] = []

        # Primera call a execute es _get_articulo_ids (retorna ids)
        # Segunda call es la query principal
        articulo_cur = _make_cursor(fetchall_return=[(100,), (200,)])
        cliente_description = [
            ("id_cliente",), ("fantasia",), ("razon_social",),
            ("latitud",), ("longitud",),
            ("canal",), ("sucursal",), ("ruta",), ("preventista",),
            ("bultos",), ("facturacion",), ("documentos",),
        ]
        # Simular múltiples cursors: primero para artículos, luego para clientes
        conn = MagicMock()
        call_count = [0]

        def make_cursor_factory():
            def cursor_factory():
                call_count[0] += 1
                if call_count[0] == 1:
                    # _get_articulo_ids cursor
                    c = _make_cursor(fetchall_return=[(100,), (200,)])
                    return c
                else:
                    # main query cursor
                    c = _make_cursor(
                        fetchall_return=[],
                        description=cliente_description,
                    )

                    def capture(sql, params=None):
                        executed_sqls.append(sql if isinstance(sql, str) else str(sql))
                        params_captured.append(params or {})

                    c.execute.side_effect = capture
                    return c

            return cursor_factory

        conn.cursor.side_effect = make_cursor_factory()

        result = get_clientes_mapa(
            conn, "admin", None,
            self._FECHA_INI, self._FECHA_FIN,
            genericos=["CERVEZAS"],
        )

        assert len(executed_sqls) == 1
        sql = executed_sqls[0]
        assert "articulo_ids" in sql
        assert params_captured[0]["articulo_ids"] == [100, 200]

    def test_returns_valid_dict_structure(self):
        """Los rows retornados tienen las claves correctas."""
        rows = [
            (1, "Fantasia", "Razon S.", -34.6, -58.4, "CANAL", "Sucursal A", "1|10", "Prev.", 100.0, 5000.0, 3),
        ]
        description = [
            ("id_cliente",), ("fantasia",), ("razon_social",),
            ("latitud",), ("longitud",),
            ("canal",), ("sucursal",), ("ruta",), ("preventista",),
            ("bultos",), ("facturacion",), ("documentos",),
        ]
        cur = _make_cursor(fetchall_return=rows, description=description)
        conn = _make_conn(cursor=cur)

        result = get_clientes_mapa(
            conn, "admin", None,
            self._FECHA_INI, self._FECHA_FIN,
        )

        assert len(result) == 1
        r = result[0]
        assert r["id_cliente"] == 1
        assert r["latitud"] == -34.6
        assert r["bultos"] == 100.0
        assert r["ruta"] == "1|10"

    def test_fv_preventa_filter_applied(self):
        """FV=1 agrega filtro id_fuerza_ventas=1 en fact_ventas join."""
        executed_sqls: list[str] = []
        params_captured: list[dict] = []
        cur = self._make_cliente_cursor([])

        def capture(sql, params=None):
            executed_sqls.append(sql if isinstance(sql, str) else str(sql))
            params_captured.append(params or {})

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        get_clientes_mapa(
            conn, "admin", None,
            self._FECHA_INI, self._FECHA_FIN,
            fv=FV_PREVENTA,
        )

        sql = executed_sqls[0]
        assert "id_fuerza_ventas" in sql
        assert params_captured[0]["fv_id"] == 1

    def test_fv_ambas_no_fv_filter(self):
        """FV=AMBAS no agrega filtro de fuerza de ventas."""
        executed_sqls: list[str] = []
        cur = self._make_cliente_cursor([])

        def capture(sql, params=None):
            executed_sqls.append(sql if isinstance(sql, str) else str(sql))

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        get_clientes_mapa(
            conn, "admin", None,
            self._FECHA_INI, self._FECHA_FIN,
            fv=FV_AMBAS,
        )

        sql = executed_sqls[0]
        assert "fv_id" not in sql

    def test_date_range_in_params(self):
        """Las fechas están en los params de la query principal."""
        params_captured: list[dict] = []
        cur = self._make_cliente_cursor([])

        def capture(sql, params=None):
            params_captured.append(params or {})

        cur.execute.side_effect = capture
        conn = _make_conn(cursor=cur)

        get_clientes_mapa(
            conn, "admin", None,
            date(2024, 3, 1), date(2024, 3, 31),
        )

        p = params_captured[0]
        assert p["fecha_ini"] == date(2024, 3, 1)
        assert p["fecha_fin"] == date(2024, 3, 31)


# ---------------------------------------------------------------------------
# Tests de get_hover_cliente
# ---------------------------------------------------------------------------

class TestGetHoverCliente:
    _FECHA_INI = date(2024, 2, 1)
    _FECHA_FIN = date(2024, 2, 29)
    _ID_CLIENTE = 42

    def _make_hover_conn(self, ventas_rows, razon_social="Cliente Test"):
        """Conexión mock con dos execute (hover + nombre cliente)."""
        conn = MagicMock()
        call_count = [0]

        def cursor_factory():
            c = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                c.fetchall.return_value = ventas_rows
                c.fetchone.return_value = (razon_social,)
            return c

        conn.cursor.side_effect = cursor_factory
        return conn

    def test_hover_returns_expected_structure(self):
        """Retorna id_cliente, razon_social y lista de genéricos."""
        ventas_rows = [
            ("CERVEZAS", 100.0, 80.0, 500.0),
            ("AGUAS DANONE", 50.0, 40.0, 200.0),
        ]
        conn = self._make_hover_conn(ventas_rows)

        result = get_hover_cliente(conn, self._ID_CLIENTE, self._FECHA_INI, self._FECHA_FIN)

        assert result["id_cliente"] == self._ID_CLIENTE
        assert result["razon_social"] == "Cliente Test"
        assert isinstance(result["genericos"], list)

    def test_hover_includes_fijos(self):
        """GENERICOS_HOVER_FIJOS siempre aparecen, aunque con m_act=m_ant=0."""
        # Solo 1 genérico en DB
        ventas_rows = [("VINOS", 10.0, 5.0, 50.0)]
        conn = self._make_hover_conn(ventas_rows)

        result = get_hover_cliente(conn, self._ID_CLIENTE, self._FECHA_INI, self._FECHA_FIN)

        genericos_names = [g["generico"] for g in result["genericos"]]
        for fijo in GENERICOS_HOVER_FIJOS:
            assert fijo in genericos_names, f"Fijo {fijo!r} no encontrado en hover"

    def test_hover_top5_by_historical(self):
        """Los top 5 vienen antes que el resto (excluidos los fijos ya en top5)."""
        # 7 genéricos — top 5 por total_historico: G1..G5
        ventas_rows = [
            ("G1", 0.0, 0.0, 1000.0),
            ("G2", 0.0, 0.0, 900.0),
            ("G3", 0.0, 0.0, 800.0),
            ("G4", 0.0, 0.0, 700.0),
            ("G5", 0.0, 0.0, 600.0),
            ("G6", 0.0, 0.0, 500.0),
            ("G7", 0.0, 0.0, 400.0),
        ]
        conn = self._make_hover_conn(ventas_rows)

        result = get_hover_cliente(conn, self._ID_CLIENTE, self._FECHA_INI, self._FECHA_FIN)

        genericos_names = [g["generico"] for g in result["genericos"]]
        # Los primeros 5 deben ser G1..G5 (top histórico)
        top_5 = genericos_names[:5]
        assert set(top_5) == {"G1", "G2", "G3", "G4", "G5"}

    def test_hover_no_duplicates(self):
        """GENERICOS_HOVER_FIJOS que ya están en top 5 no se duplican."""
        # CERVEZAS está en la DB (fijo también) → no duplicar
        ventas_rows = [
            ("CERVEZAS", 500.0, 400.0, 2000.0),
            ("G2", 0.0, 0.0, 900.0),
            ("G3", 0.0, 0.0, 800.0),
            ("G4", 0.0, 0.0, 700.0),
            ("G5", 0.0, 0.0, 600.0),
        ]
        conn = self._make_hover_conn(ventas_rows)

        result = get_hover_cliente(conn, self._ID_CLIENTE, self._FECHA_INI, self._FECHA_FIN)

        genericos_names = [g["generico"] for g in result["genericos"]]
        # CERVEZAS debe aparecer exactamente una vez
        assert genericos_names.count("CERVEZAS") == 1

    def test_hover_mact_mant_values(self):
        """m_act y m_ant corresponden a los valores del período actual y anterior."""
        ventas_rows = [("CERVEZAS", 150.0, 120.0, 500.0)]
        conn = self._make_hover_conn(ventas_rows)

        result = get_hover_cliente(conn, self._ID_CLIENTE, self._FECHA_INI, self._FECHA_FIN)

        cervezas = next(g for g in result["genericos"] if g["generico"] == "CERVEZAS")
        assert cervezas["m_act"] == 150.0
        assert cervezas["m_ant"] == 120.0

    def test_hover_fijo_with_zero_if_not_in_db(self):
        """Fijo no presente en DB tiene m_act=0 y m_ant=0."""
        ventas_rows = []  # sin ventas en DB
        conn = self._make_hover_conn(ventas_rows)

        result = get_hover_cliente(conn, self._ID_CLIENTE, self._FECHA_INI, self._FECHA_FIN)

        # Todos los fijos tienen zeros
        for g in result["genericos"]:
            if g["generico"] in GENERICOS_HOVER_FIJOS:
                assert g["m_act"] == 0.0
                assert g["m_ant"] == 0.0


# ---------------------------------------------------------------------------
# Tests de _get_articulo_ids
# ---------------------------------------------------------------------------

class TestGetArticuloIds:
    def test_returns_none_when_no_filter(self):
        conn = _make_conn()
        result = _get_articulo_ids(conn, genericos=None, marcas=None)
        assert result is None

    def test_returns_ids_for_genericos(self):
        cur = _make_cursor(fetchall_return=[(1,), (2,), (3,)])
        conn = _make_conn(cursor=cur)

        result = _get_articulo_ids(conn, genericos=["CERVEZAS"])

        assert result == [1, 2, 3]

    def test_returns_ids_for_marcas(self):
        cur = _make_cursor(fetchall_return=[(10,)])
        conn = _make_conn(cursor=cur)

        result = _get_articulo_ids(conn, marcas=["SALTA"])

        assert result == [10]

    def test_returns_empty_list_when_no_match(self):
        cur = _make_cursor(fetchall_return=[])
        conn = _make_conn(cursor=cur)

        result = _get_articulo_ids(conn, genericos=["INEXISTENTE"])

        assert result == []
