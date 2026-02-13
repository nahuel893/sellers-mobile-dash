"""Tests para la capa de datos mock."""
import pytest
from src.data.mock_data import get_mock_dataframe


@pytest.fixture
def df():
    return get_mock_dataframe()


def test_dataframe_not_empty(df):
    assert len(df) > 0


def test_dataframe_columns(df):
    expected = [
        'vendedor', 'supervisor', 'grupo_marca', 'ventas', 'cupo',
        'falta', 'tendencia', 'pct_tendencia', 'vta_diaria_necesaria',
    ]
    for col in expected:
        assert col in df.columns, f"Falta columna: {col}"


def test_falta_is_cupo_minus_ventas(df):
    assert (df['falta'] == df['cupo'] - df['ventas']).all()


def test_ventas_non_negative(df):
    assert (df['ventas'] >= 0).all()


def test_cupo_non_negative(df):
    assert (df['cupo'] >= 0).all()


def test_supervisores_exist(df):
    supervisores = df['supervisor'].unique()
    assert len(supervisores) >= 1


def test_each_vendor_has_all_groups(df):
    from config import GRUPOS_MARCA
    for vendedor in df['vendedor'].unique():
        grupos = df[df['vendedor'] == vendedor]['grupo_marca'].tolist()
        for g in GRUPOS_MARCA:
            assert g in grupos, f"{vendedor} no tiene grupo {g}"
