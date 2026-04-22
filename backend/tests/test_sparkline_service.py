"""Tests para el servicio de sparkline."""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from services.ventas_service import get_sparkline_vendedor


def _make_cursor_rows(rows: list[tuple]):
    """Creates a mock cursor that returns the given rows from fetchall()."""
    cur = MagicMock()
    cur.fetchall.return_value = rows
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    return cur


def _make_conn(rows):
    """Creates a mock psycopg2-like connection with a cursor returning rows."""
    conn = MagicMock()
    cur = _make_cursor_rows(rows)
    conn.cursor.return_value = cur
    return conn


def _today():
    return date.today()


def _ago(days):
    return _today() - timedelta(days=days)


# --- Zero-fill: response always has exactly `dias` points ---

def test_sparkline_zero_fill_missing_days():
    """Zero-fill missing days so response has exactly `dias` points."""
    dias = 5
    # Only 2 real days with data
    rows = [
        (_ago(4), 'SALTA', 10),
        (_ago(2), 'HEINEKEN', 5),
    ]
    conn = _make_conn(rows)
    result = get_sparkline_vendedor(conn, vendedor='TEST VENDEDOR', dias=dias, id_sucursal=1)
    assert result['dias'] == dias
    assert len(result['puntos']) == dias


def test_sparkline_zero_fill_missing_brands():
    """Days with no data for a brand have 0 for that brand."""
    dias = 3
    rows = [
        (_ago(2), 'SALTA', 10),
        (_ago(0), 'HEINEKEN', 5),
    ]
    conn = _make_conn(rows)
    result = get_sparkline_vendedor(conn, vendedor='TEST VENDEDOR', dias=dias, id_sucursal=1)
    # Find the day with SALTA data
    punto_ago2 = next(p for p in result['puntos'] if p['fecha'] == _ago(2).isoformat())
    assert punto_ago2['por_grupo']['SALTA'] == 10
    # HEINEKEN is 0 on that day
    assert punto_ago2['por_grupo'].get('HEINEKEN', 0) == 0


def test_sparkline_marca_to_grupo_marca_mapping():
    """Marca from DB is mapped to grupo_marca via MAPEO_MARCA_GRUPO."""
    dias = 3
    rows = [
        (_ago(1), 'SCHNEIDER', 20),   # SCHNEIDER → MULTICERVEZAS
        (_ago(1), 'SALTA', 15),
    ]
    conn = _make_conn(rows)
    result = get_sparkline_vendedor(conn, vendedor='TEST VENDEDOR', dias=dias, id_sucursal=1)
    punto = next(p for p in result['puntos'] if p['fecha'] == _ago(1).isoformat())
    # SCHNEIDER should be bucketed under MULTICERVEZAS
    assert 'MULTICERVEZAS' in punto['por_grupo']
    assert punto['por_grupo']['MULTICERVEZAS'] == 20
    assert 'SCHNEIDER' not in punto['por_grupo']
    assert punto['por_grupo'].get('SALTA') == 15


def test_sparkline_aggregate_case_no_vendedor_filter():
    """When vendedor=None (casa-central), no vendedor filter is applied."""
    dias = 2
    rows = [
        (_ago(1), 'SALTA', 100),
    ]
    conn = _make_conn(rows)
    result = get_sparkline_vendedor(conn, vendedor=None, dias=dias, id_sucursal=1)
    assert result['vendedor'] == 'casa-central'
    assert result['dias'] == dias
    assert len(result['puntos']) == dias


def test_sparkline_default_dias_is_18():
    """Default value of dias is 18."""
    conn = _make_conn([])
    result = get_sparkline_vendedor(conn, vendedor='TEST VENDEDOR', id_sucursal=1)
    assert result['dias'] == 18
    assert len(result['puntos']) == 18


def test_sparkline_caps_dias_at_90():
    """dias is capped at 90 even if caller passes a larger value."""
    conn = _make_conn([])
    result = get_sparkline_vendedor(conn, vendedor='TEST VENDEDOR', dias=200, id_sucursal=1)
    assert result['dias'] == 90
    assert len(result['puntos']) == 90


def test_sparkline_marks_correct_vendor_name():
    """Response vendedor matches the requested slug name."""
    conn = _make_conn([])
    result = get_sparkline_vendedor(conn, vendedor='MARTIN GUZMAN', dias=3, id_sucursal=1)
    assert result['vendedor'] == 'MARTIN GUZMAN'


def test_sparkline_aggregates_same_marca_same_day():
    """Multiple rows for same marca+day are summed."""
    dias = 2
    rows = [
        (_ago(1), 'SALTA', 30),
        (_ago(1), 'SALTA', 20),  # Same day, same marca
    ]
    conn = _make_conn(rows)
    result = get_sparkline_vendedor(conn, vendedor='TEST VENDEDOR', dias=dias, id_sucursal=1)
    punto = next(p for p in result['puntos'] if p['fecha'] == _ago(1).isoformat())
    assert punto['por_grupo']['SALTA'] == 50
