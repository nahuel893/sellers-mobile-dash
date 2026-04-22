"""Tests para el servicio de preventistas."""
import pandas as pd
import pytest

from services.preventistas_service import (
    compute_initials,
    get_preventistas,
)


@pytest.fixture
def df_mock():
    """DataFrame mínimo que simula la estructura del DataFrame principal."""
    rows = [
        ('JUAN GARCIA',   'BADIE', '1 - CASA CENTRAL'),
        ('ANA DE LA TORRE', 'BADIE', '1 - CASA CENTRAL'),
        ('MARIA FERNANDEZ LOPEZ', 'BADIE', '1 - CASA CENTRAL'),
        ('PEDRO ROMERO',  'LOPEZ', '1 - CASA CENTRAL'),
        ('SOFÍA VARGAS',  'BADIE', '2 - GÜEMES'),
    ]
    return pd.DataFrame(rows, columns=['vendedor', 'supervisor', 'sucursal'])


# --- compute_initials ---

def test_initials_single_word():
    """Single-word name → first two chars uppercased."""
    assert compute_initials('JUAN') == 'JU'


def test_initials_double_word():
    """Two-word name → first letter of each word."""
    assert compute_initials('JUAN GARCIA') == 'JG'


def test_initials_three_words_takes_first_two():
    """Three-word name → first letter of the first TWO words."""
    assert compute_initials('MARIA FERNANDEZ LOPEZ') == 'MF'


def test_initials_lowercase_input_uppercase_output():
    """Input may be any case; output is always uppercase."""
    assert compute_initials('ana de la torre') == 'AD'


# --- get_preventistas ---

def test_get_preventistas_filters_by_sucursal(df_mock):
    """Returns only preventistas of the requested sucursal."""
    result = get_preventistas(df_mock, sucursal_id=1)
    nombres = [p['nombre'] for p in result]
    assert 'SOFÍA VARGAS' not in nombres
    assert all(nombre in {
        'JUAN GARCIA', 'ANA DE LA TORRE', 'MARIA FERNANDEZ LOPEZ', 'PEDRO ROMERO'
    } for nombre in nombres)


def test_get_preventistas_sorted_by_nombre(df_mock):
    """Result is sorted alphabetically by nombre."""
    result = get_preventistas(df_mock, sucursal_id=1)
    nombres = [p['nombre'] for p in result]
    assert nombres == sorted(nombres)


def test_get_preventistas_shape(df_mock):
    """Each item has nombre, slug, iniciales, ruta keys."""
    result = get_preventistas(df_mock, sucursal_id=1)
    assert len(result) >= 1
    for item in result:
        assert 'nombre' in item
        assert 'slug' in item
        assert 'iniciales' in item
        assert 'ruta' in item


def test_get_preventistas_initials_correct(df_mock):
    """Initials are correctly derived from nombre."""
    result = get_preventistas(df_mock, sucursal_id=1)
    by_nombre = {p['nombre']: p for p in result}
    assert by_nombre['JUAN GARCIA']['iniciales'] == 'JG'
    assert by_nombre['MARIA FERNANDEZ LOPEZ']['iniciales'] == 'MF'


def test_get_preventistas_unknown_sucursal_returns_empty(df_mock):
    """Unknown sucursal id returns empty list."""
    result = get_preventistas(df_mock, sucursal_id=99)
    assert result == []


def test_get_preventistas_slug_derived_from_nombre(df_mock):
    """Slug is URL-safe derivation of nombre."""
    result = get_preventistas(df_mock, sucursal_id=1)
    by_nombre = {p['nombre']: p for p in result}
    # 'JUAN GARCIA' → 'JUAN-GARCIA'
    assert by_nombre['JUAN GARCIA']['slug'] == 'JUAN-GARCIA'


def test_get_preventistas_unique_per_vendedor(df_mock):
    """No duplicate vendedores in result (even if df has multiple rows per vendor)."""
    # Add duplicate rows (multiple categoria/grupo_marca for same vendedor)
    extra_rows = pd.DataFrame([
        ('JUAN GARCIA', 'BADIE', '1 - CASA CENTRAL'),
        ('JUAN GARCIA', 'BADIE', '1 - CASA CENTRAL'),
    ], columns=['vendedor', 'supervisor', 'sucursal'])
    df_extended = pd.concat([df_mock, extra_rows], ignore_index=True)
    result = get_preventistas(df_extended, sucursal_id=1)
    nombres = [p['nombre'] for p in result]
    assert len(nombres) == len(set(nombres))
