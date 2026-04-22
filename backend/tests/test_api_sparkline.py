"""Tests para GET /api/avance/sparkline/{slug}."""
from datetime import date
from unittest.mock import MagicMock, patch

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


def _mock_sparkline(vendedor, dias=18, categoria='CERVEZAS', id_sucursal=1):
    """Retorna datos de sparkline ficticios para tests."""
    today = date.today().isoformat()
    return {
        'vendedor': vendedor if vendedor else 'casa-central',
        'dias': dias,
        'puntos': [
            {'fecha': today, 'por_grupo': {'SALTA': 10, 'HEINEKEN': 5}}
        ] * dias,
    }


# Patch the service so tests don't need a real DB connection
@pytest.fixture(autouse=True)
def mock_sparkline_service(monkeypatch):
    """Mock get_sparkline_vendedor to avoid real DB connections."""
    def _fake_sparkline(conn, vendedor, dias=18, categoria='CERVEZAS', id_sucursal=1):
        return _mock_sparkline(vendedor, dias, categoria, id_sucursal)

    monkeypatch.setattr(
        'routers.avance.get_sparkline_vendedor',
        _fake_sparkline,
    )
    # Also mock gold_db.get_connection and release_connection
    monkeypatch.setattr(
        'routers.avance.get_gold_connection',
        lambda: MagicMock(),
    )
    monkeypatch.setattr(
        'routers.avance.release_gold_connection',
        lambda conn: None,
    )


def test_sparkline_200_known_vendor(client):
    """GET /api/avance/sparkline/<slug> → 200 for a known vendor."""
    r = client.get('/api/avance/sparkline/FACUNDO-CACERES')
    assert r.status_code == 200


def test_sparkline_response_shape(client):
    """Response has vendedor, dias, puntos."""
    r = client.get('/api/avance/sparkline/FACUNDO-CACERES')
    data = r.json()
    assert 'vendedor' in data
    assert 'dias' in data
    assert 'puntos' in data
    assert isinstance(data['puntos'], list)


def test_sparkline_puntos_have_fecha_and_por_grupo(client):
    """Each punto has fecha (ISO date) and por_grupo (dict)."""
    r = client.get('/api/avance/sparkline/FACUNDO-CACERES')
    for punto in r.json()['puntos']:
        assert 'fecha' in punto
        assert 'por_grupo' in punto
        assert isinstance(punto['por_grupo'], dict)


def test_sparkline_404_unknown_vendor(client):
    """GET /api/avance/sparkline/<unknown-slug> → 404."""
    r = client.get('/api/avance/sparkline/VENDEDOR-INEXISTENTE-XYZ')
    assert r.status_code == 404


def test_sparkline_casa_central_aggregate(client):
    """slug='casa-central' → aggregate (vendedor='casa-central' in response)."""
    r = client.get('/api/avance/sparkline/casa-central')
    assert r.status_code == 200
    data = r.json()
    assert data['vendedor'] == 'casa-central'


def test_sparkline_dias_param_respected(client):
    """?dias=5 → puntos list has 5 items, dias=5 in response."""
    r = client.get('/api/avance/sparkline/FACUNDO-CACERES', params={'dias': 5})
    data = r.json()
    assert data['dias'] == 5
    assert len(data['puntos']) == 5


def test_sparkline_default_dias_18(client):
    """No ?dias param → dias=18 in response."""
    r = client.get('/api/avance/sparkline/FACUNDO-CACERES')
    data = r.json()
    assert data['dias'] == 18
