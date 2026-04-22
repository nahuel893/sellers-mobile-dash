"""Tests de endpoint GET /api/preventistas."""
import pytest
from fastapi.testclient import TestClient

from main import app
from dependencies import get_df
from data.mock_data import get_mock_dataframe


@pytest.fixture(autouse=True)
def override_deps():
    """Usa mock data para todos los tests de este módulo."""
    app.dependency_overrides[get_df] = get_mock_dataframe
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_preventistas_200_with_sucursal(client):
    """GET /api/preventistas?sucursal=1 → 200 con lista."""
    r = client.get('/api/preventistas', params={'sucursal': 1})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_preventistas_schema_shape(client):
    """Cada item tiene nombre, slug, iniciales, ruta."""
    r = client.get('/api/preventistas', params={'sucursal': 1})
    assert r.status_code == 200
    for item in r.json():
        assert 'nombre' in item
        assert 'slug' in item
        assert 'iniciales' in item
        assert 'ruta' in item


def test_preventistas_sorted_by_nombre(client):
    """Lista viene ordenada por nombre."""
    r = client.get('/api/preventistas', params={'sucursal': 1})
    nombres = [item['nombre'] for item in r.json()]
    assert nombres == sorted(nombres)


def test_preventistas_initials_two_chars(client):
    """Iniciales siempre son 2 caracteres en mayúsculas."""
    r = client.get('/api/preventistas', params={'sucursal': 1})
    for item in r.json():
        assert len(item['iniciales']) == 2
        assert item['iniciales'].isupper()


def test_preventistas_unknown_sucursal_empty_list(client):
    """Sucursal desconocida → 200 con lista vacía."""
    r = client.get('/api/preventistas', params={'sucursal': 999})
    assert r.status_code == 200
    assert r.json() == []


def test_preventistas_default_sucursal_is_1(client):
    """Sin parámetro sucursal, usa default=1 y devuelve lista."""
    r = client.get('/api/preventistas')
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1
