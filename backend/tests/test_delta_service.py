"""Tests para el servicio de delta pp (mes actual vs mes anterior)."""
from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest

from services.ventas_service import get_delta_vendedor


def _make_conn_with_prior(rows: list[tuple]):
    """Creates mock conn whose cursor returns rows for prior-month query."""
    cur = MagicMock()
    cur.fetchall.return_value = rows
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn


def _make_df(vendedor: str, grupo_marca: str, ventas: int, cupo: int,
             pct_tendencia: float) -> pd.DataFrame:
    """Minimal DataFrame imitating the main app DataFrame structure."""
    from config import get_dias_habiles
    hab, trans, _ = get_dias_habiles()
    tendencia = ventas * hab / trans if trans > 0 else 0
    return pd.DataFrame([{
        'vendedor': vendedor,
        'supervisor': 'BADIE',
        'sucursal': '1 - CASA CENTRAL',
        'categoria': 'CERVEZAS',
        'grupo_marca': grupo_marca,
        'ventas': ventas,
        'cupo': cupo,
        'falta': cupo - ventas,
        'tendencia': tendencia,
        'pct_tendencia': pct_tendencia,
        'vta_diaria_necesaria': 0,
    }])


# --- pct_actual uses current-month logic ---

def test_delta_pct_actual_from_df():
    """pct_actual is derived from the main DataFrame (current month tendencia)."""
    df = _make_df('JUAN GARCIA', 'SALTA', ventas=100, cupo=200, pct_tendencia=75.0)
    conn = _make_conn_with_prior([])
    result = get_delta_vendedor(conn, df=df, vendedor='JUAN GARCIA',
                                categoria='CERVEZAS', id_sucursal=1)
    assert result['vendedor'] == 'JUAN GARCIA'
    deltas = {d['grupo_marca']: d for d in result['deltas']}
    assert 'SALTA' in deltas
    assert abs(deltas['SALTA']['pct_actual'] - 75.0) < 0.1


# --- pct_anterior from prior-month query ---

def test_delta_pct_anterior_from_query():
    """pct_anterior comes from prior-month cursor data."""
    df = _make_df('JUAN GARCIA', 'SALTA', ventas=100, cupo=200, pct_tendencia=75.0)
    # Prior month: 150 ventas, 200 cupo → 75.0%
    prior_rows = [('SALTA', 150, 200)]
    conn = _make_conn_with_prior(prior_rows)
    result = get_delta_vendedor(conn, df=df, vendedor='JUAN GARCIA',
                                categoria='CERVEZAS', id_sucursal=1)
    deltas = {d['grupo_marca']: d for d in result['deltas']}
    assert abs(deltas['SALTA']['pct_anterior'] - 75.0) < 0.1


# --- delta_pp is signed and rounded to 1 decimal ---

def test_delta_pp_positive():
    """delta_pp positive when pct_actual > pct_anterior."""
    df = _make_df('JUAN GARCIA', 'IMPERIAL', ventas=100, cupo=200, pct_tendencia=73.8)
    # Prior: 67.0%
    prior_rows = [('IMPERIAL', 134, 200)]  # 134/200 = 67%
    conn = _make_conn_with_prior(prior_rows)
    result = get_delta_vendedor(conn, df=df, vendedor='JUAN GARCIA',
                                categoria='CERVEZAS', id_sucursal=1)
    deltas = {d['grupo_marca']: d for d in result['deltas']}
    delta_pp = deltas['IMPERIAL']['delta_pp']
    assert delta_pp is not None
    assert delta_pp > 0


def test_delta_pp_negative():
    """delta_pp negative when pct_actual < pct_anterior."""
    df = _make_df('JUAN GARCIA', 'HEINEKEN', ventas=100, cupo=200, pct_tendencia=60.0)
    # Prior: 80%
    prior_rows = [('HEINEKEN', 160, 200)]
    conn = _make_conn_with_prior(prior_rows)
    result = get_delta_vendedor(conn, df=df, vendedor='JUAN GARCIA',
                                categoria='CERVEZAS', id_sucursal=1)
    deltas = {d['grupo_marca']: d for d in result['deltas']}
    delta_pp = deltas['HEINEKEN']['delta_pp']
    assert delta_pp is not None
    assert delta_pp < 0


def test_delta_pp_rounded_to_1_decimal():
    """delta_pp is rounded to 1 decimal place."""
    df = _make_df('JUAN GARCIA', 'SALTA', ventas=100, cupo=300, pct_tendencia=73.8)
    prior_rows = [('SALTA', 201, 300)]  # 67.0%
    conn = _make_conn_with_prior(prior_rows)
    result = get_delta_vendedor(conn, df=df, vendedor='JUAN GARCIA',
                                categoria='CERVEZAS', id_sucursal=1)
    deltas = {d['grupo_marca']: d for d in result['deltas']}
    delta_pp = deltas['SALTA']['delta_pp']
    assert delta_pp is not None
    # Should have at most 1 decimal place
    assert round(delta_pp, 1) == delta_pp


# --- null when prior missing ---

def test_delta_pp_null_when_no_prior_data():
    """delta_pp and pct_anterior are None when prior month has no data."""
    df = _make_df('JUAN GARCIA', 'MILLER', ventas=50, cupo=100, pct_tendencia=65.0)
    conn = _make_conn_with_prior([])  # Empty prior data
    result = get_delta_vendedor(conn, df=df, vendedor='JUAN GARCIA',
                                categoria='CERVEZAS', id_sucursal=1)
    deltas = {d['grupo_marca']: d for d in result['deltas']}
    assert 'MILLER' in deltas
    assert deltas['MILLER']['pct_anterior'] is None
    assert deltas['MILLER']['delta_pp'] is None


# --- Aggregate / casa-central case ---

def test_delta_aggregate_case_no_vendedor():
    """vendedor=None → aggregate over all preventistas in sucursal."""
    # Multi-vendor df
    rows = []
    for v in ['JUAN GARCIA', 'ANA LOPEZ']:
        rows.append({
            'vendedor': v,
            'supervisor': 'BADIE',
            'sucursal': '1 - CASA CENTRAL',
            'categoria': 'CERVEZAS',
            'grupo_marca': 'SALTA',
            'ventas': 100,
            'cupo': 200,
            'falta': 100,
            'tendencia': 120.0,
            'pct_tendencia': 60.0,
            'vta_diaria_necesaria': 5,
        })
    df = pd.DataFrame(rows)
    conn = _make_conn_with_prior([])
    result = get_delta_vendedor(conn, df=df, vendedor=None,
                                categoria='CERVEZAS', id_sucursal=1)
    assert result['vendedor'] == 'casa-central'
    assert isinstance(result['deltas'], list)
