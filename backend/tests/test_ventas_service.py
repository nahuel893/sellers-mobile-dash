"""Tests para la capa de servicios."""
import pytest
from data.mock_data import get_mock_dataframe
from services.ventas_service import (
    calcular_tendencia, calcular_pct_tendencia,
    get_supervisores, get_vendedores_por_supervisor,
    get_datos_vendedor, get_resumen_vendedor,
)


@pytest.fixture
def df():
    return get_mock_dataframe()


# --- Tests de cálculos ---

def test_calcular_tendencia_basic():
    # 100 vendidos en 10 días, 20 hábiles → 200
    assert calcular_tendencia(100, dias_trans=10, dias_hab=20) == 200


def test_calcular_tendencia_zero_days():
    assert calcular_tendencia(100, dias_trans=0, dias_hab=20) == 0


def test_calcular_pct_tendencia_basic():
    # 100 vendidos, cupo 200, 10/20 días → tendencia=200, pct=100%
    assert calcular_pct_tendencia(100, cupo=200, dias_trans=10, dias_hab=20) == 100


def test_calcular_pct_tendencia_zero_cupo():
    assert calcular_pct_tendencia(100, cupo=0, dias_trans=10, dias_hab=20) == 0


def test_calcular_pct_tendencia_over_100():
    # 150 vendidos, cupo 200, 10/20 días → tendencia=300, pct=150%
    assert calcular_pct_tendencia(150, cupo=200, dias_trans=10, dias_hab=20) == 150


# --- Tests de filtros ---

def test_get_supervisores(df):
    supervisores = get_supervisores(df)
    assert isinstance(supervisores, list)
    assert len(supervisores) >= 2
    assert supervisores == sorted(supervisores)


def test_get_vendedores_por_supervisor(df):
    supervisores = get_supervisores(df)
    vendedores = get_vendedores_por_supervisor(df, supervisores[0])
    assert isinstance(vendedores, list)
    assert len(vendedores) >= 1
    assert vendedores == sorted(vendedores)


def test_get_vendedores_supervisor_inexistente(df):
    vendedores = get_vendedores_por_supervisor(df, 'NO_EXISTE')
    assert vendedores == []


def test_get_datos_vendedor_cervezas(df):
    primer_vendedor = df['vendedor'].iloc[0]
    datos = get_datos_vendedor(df, primer_vendedor, 'CERVEZAS')
    assert len(datos) > 0
    assert (datos['vendedor'] == primer_vendedor).all()
    assert (datos['categoria'] == 'CERVEZAS').all()


def test_get_datos_vendedor_multiccu(df):
    primer_vendedor = df['vendedor'].iloc[0]
    datos = get_datos_vendedor(df, primer_vendedor, 'MULTICCU')
    assert len(datos) == 1
    assert (datos['categoria'] == 'MULTICCU').all()


# --- Tests de resumen ---

def test_get_resumen_vendedor(df):
    primer_vendedor = df['vendedor'].iloc[0]
    resumen = get_resumen_vendedor(df, primer_vendedor)
    assert 'vendedor' in resumen
    assert 'ventas' in resumen
    assert 'cupo' in resumen
    assert 'falta' in resumen
    assert 'tendencia' in resumen
    assert 'pct_tendencia' in resumen
    assert resumen['vendedor'] == primer_vendedor


def test_resumen_falta_equals_cupo_minus_ventas(df):
    primer_vendedor = df['vendedor'].iloc[0]
    resumen = get_resumen_vendedor(df, primer_vendedor)
    assert resumen['falta'] == resumen['cupo'] - resumen['ventas']


def test_resumen_pct_is_reasonable(df):
    for vendedor in df['vendedor'].unique():
        resumen = get_resumen_vendedor(df, vendedor, 'CERVEZAS')
        assert 0 <= resumen['pct_tendencia'] <= 300


def test_resumen_multiccu(df):
    primer_vendedor = df['vendedor'].iloc[0]
    resumen = get_resumen_vendedor(df, primer_vendedor, 'MULTICCU')
    assert resumen['ventas'] > 0
    assert resumen['cupo'] > 0
    assert resumen['falta'] == resumen['cupo'] - resumen['ventas']


def test_resumen_aguas_danone(df):
    primer_vendedor = df['vendedor'].iloc[0]
    resumen = get_resumen_vendedor(df, primer_vendedor, 'AGUAS_DANONE')
    assert resumen['ventas'] > 0
    assert resumen['cupo'] > 0
