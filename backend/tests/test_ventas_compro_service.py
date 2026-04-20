"""
Tests para services/ventas_compro_service.py

TDD: tests escritos antes de la implementación.
Se mockea psycopg2 — sin base de datos real.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from services.ventas_compro_service import get_compro_data
from ventas_constants import FV_PREVENTA, FV_AUTOVENTA, FV_AMBAS


# ---------------------------------------------------------------------------
# Helpers de mock
# ---------------------------------------------------------------------------

def _make_cursor(fetchall_return=None, description=None):
    cur = MagicMock()
    cur.fetchall.return_value = fetchall_return or []
    cur.description = description or [
        ("id_cliente",), ("latitud",), ("longitud",),
        ("compro",), ("ultima_compra",),
    ]
    return cur


def _make_conn(cursor=None):
    conn = MagicMock()
    conn.cursor.return_value = cursor or _make_cursor()
    return conn


# ---------------------------------------------------------------------------
# Datos de prueba
# ---------------------------------------------------------------------------

FECHA_INI = date(2024, 1, 1)
FECHA_FIN = date(2024, 1, 31)

_RAW_ROW_COMPRADOR = (
    42, -24.79, -65.41, True, date(2024, 1, 15)
)
_RAW_ROW_NO_COMPRADOR = (
    99, -24.80, -65.42, False, date(2023, 11, 5)
)
_RAW_ROW_SIN_COMPRA = (
    77, -24.81, -65.43, False, None
)


# ---------------------------------------------------------------------------
# Tests de get_compro_data
# ---------------------------------------------------------------------------

class TestGetComproData:
    def test_returns_list(self):
        """get_compro_data retorna una lista."""
        cur = _make_cursor(fetchall_return=[])
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
        )
        assert isinstance(result, list)

    def test_empty_when_no_rows(self):
        """Retorna lista vacía si no hay clientes con coordenadas válidas."""
        cur = _make_cursor(fetchall_return=[])
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
        )
        assert result == []

    def test_comprador_row_mapped_correctly(self):
        """Un cliente que compró en el período → compro=True, ultima_compra correcta."""
        cur = _make_cursor(fetchall_return=[_RAW_ROW_COMPRADOR])
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
        )
        assert len(result) == 1
        row = result[0]
        assert row["id_cliente"] == 42
        assert row["lat"] == -24.79
        assert row["lon"] == -65.41
        assert row["compro"] is True
        assert row["ultima_compra"] == date(2024, 1, 15)

    def test_no_comprador_row_mapped_correctly(self):
        """Un cliente que NO compró en el período → compro=False."""
        cur = _make_cursor(fetchall_return=[_RAW_ROW_NO_COMPRADOR])
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
        )
        assert len(result) == 1
        assert result[0]["compro"] is False
        assert result[0]["ultima_compra"] == date(2023, 11, 5)

    def test_sin_compra_historica_ultima_compra_none(self):
        """Cliente sin ninguna compra histórica → ultima_compra=None."""
        cur = _make_cursor(fetchall_return=[_RAW_ROW_SIN_COMPRA])
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
        )
        assert result[0]["ultima_compra"] is None

    def test_multiple_rows(self):
        """Maneja múltiples clientes correctamente."""
        rows = [_RAW_ROW_COMPRADOR, _RAW_ROW_NO_COMPRADOR, _RAW_ROW_SIN_COMPRA]
        cur = _make_cursor(fetchall_return=rows)
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
        )
        assert len(result) == 3

    def test_rbac_supervisor_passes_sucursales(self):
        """Un supervisor pasa sucursales al filtro RBAC (se ejecuta la query)."""
        cur = _make_cursor(fetchall_return=[])
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="supervisor",
            sucursales_usuario=[1, 2],
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
        )
        # Que no explote — la query se ejecutó
        cur.execute.assert_called_once()
        assert isinstance(result, list)

    def test_fv_preventa_default(self):
        """FV_PREVENTA (default) no explota la función."""
        cur = _make_cursor(fetchall_return=[])
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
            fv=FV_PREVENTA,
        )
        assert isinstance(result, list)

    def test_fv_autoventa(self):
        """FV_AUTOVENTA no explota la función."""
        cur = _make_cursor(fetchall_return=[])
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
            fv=FV_AUTOVENTA,
        )
        assert isinstance(result, list)

    def test_fv_ambas(self):
        """FV_AMBAS no explota la función."""
        cur = _make_cursor(fetchall_return=[])
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
            fv=FV_AMBAS,
        )
        assert isinstance(result, list)

    def test_cursor_closed_on_success(self):
        """El cursor se cierra aunque la query sea exitosa."""
        cur = _make_cursor(fetchall_return=[_RAW_ROW_COMPRADOR])
        conn = _make_conn(cur)
        get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
        )
        cur.close.assert_called_once()

    def test_cursor_closed_on_exception(self):
        """El cursor se cierra incluso si la query lanza excepción."""
        cur = _make_cursor()
        cur.execute.side_effect = Exception("DB explota")
        conn = _make_conn(cur)
        with pytest.raises(Exception, match="DB explota"):
            get_compro_data(
                conn=conn,
                role_name="admin",
                sucursales_usuario=None,
                fecha_ini=FECHA_INI,
                fecha_fin=FECHA_FIN,
            )
        cur.close.assert_called_once()

    def test_canal_filter_applied(self):
        """Filtro canal se pasa sin romper la query."""
        cur = _make_cursor(fetchall_return=[])
        conn = _make_conn(cur)
        result = get_compro_data(
            conn=conn,
            role_name="admin",
            sucursales_usuario=None,
            fecha_ini=FECHA_INI,
            fecha_fin=FECHA_FIN,
            canal="TRADICIONAL",
        )
        cur.execute.assert_called_once()
        # El SQL ejecutado debe contener la referencia al parámetro canal
        sql_executed = cur.execute.call_args[0][0]
        assert "canal" in sql_executed.lower() or "%(canal)s" in sql_executed
