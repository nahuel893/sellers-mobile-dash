"""Tests para GET /api/avance/delta/{slug}."""
from unittest.mock import MagicMock

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


@pytest.fixture(autouse=True)
def mock_delta_service(monkeypatch):
    """Mock get_delta_vendedor para evitar conexiones reales a la BD."""
    def _fake_delta(conn, df, vendedor, categoria='CERVEZAS', id_sucursal=1):
        nombre = vendedor if vendedor else 'casa-central'
        return {
            'vendedor': nombre,
            'deltas': [
                {
                    'grupo_marca': 'SALTA',
                    'pct_actual': 73.8,
                    'pct_anterior': 67.0,
                    'delta_pp': 6.8,
                }
            ],
        }

    monkeypatch.setattr('routers.avance.get_delta_vendedor', _fake_delta)
    monkeypatch.setattr('routers.avance.get_gold_connection', lambda: MagicMock())
    monkeypatch.setattr('routers.avance.release_gold_connection', lambda conn: None)


def test_delta_200_known_vendor(client):
    """GET /api/avance/delta/<slug> → 200 for a known vendor."""
    r = client.get('/api/avance/delta/FACUNDO-CACERES')
    assert r.status_code == 200


def test_delta_response_shape(client):
    """Response has vendedor and deltas list."""
    r = client.get('/api/avance/delta/FACUNDO-CACERES')
    data = r.json()
    assert 'vendedor' in data
    assert 'deltas' in data
    assert isinstance(data['deltas'], list)


def test_delta_item_shape(client):
    """Each delta item has grupo_marca, pct_actual, pct_anterior, delta_pp."""
    r = client.get('/api/avance/delta/FACUNDO-CACERES')
    for item in r.json()['deltas']:
        assert 'grupo_marca' in item
        assert 'pct_actual' in item
        assert 'pct_anterior' in item
        assert 'delta_pp' in item


def test_delta_404_unknown_vendor(client):
    """GET /api/avance/delta/<unknown-slug> → 404."""
    r = client.get('/api/avance/delta/VENDEDOR-INEXISTENTE-XYZ')
    assert r.status_code == 404


def test_delta_casa_central_aggregate(client):
    """slug='casa-central' → aggregate (vendedor='casa-central' in response)."""
    r = client.get('/api/avance/delta/casa-central')
    assert r.status_code == 200
    data = r.json()
    assert data['vendedor'] == 'casa-central'


def test_delta_null_deltas_when_no_prior(monkeypatch, client):
    """Null deltas when prior month has no data."""
    def _no_prior(conn, df, vendedor, categoria='CERVEZAS', id_sucursal=1):
        nombre = vendedor if vendedor else 'casa-central'
        return {
            'vendedor': nombre,
            'deltas': [
                {
                    'grupo_marca': 'SALTA',
                    'pct_actual': 60.0,
                    'pct_anterior': None,
                    'delta_pp': None,
                }
            ],
        }

    monkeypatch.setattr('routers.avance.get_delta_vendedor', _no_prior)
    r = client.get('/api/avance/delta/FACUNDO-CACERES')
    assert r.status_code == 200
    deltas = r.json()['deltas']
    assert len(deltas) >= 1
    salta = next((d for d in deltas if d['grupo_marca'] == 'SALTA'), None)
    assert salta is not None
    assert salta['pct_anterior'] is None
    assert salta['delta_pp'] is None
