"""Tests para GET /api/weather."""
from unittest.mock import AsyncMock, patch

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


MOCK_WEATHER_PAYLOAD = {
    'city': 'Salta',
    'temp_c': 23,
    'feels_like_c': 22,
    'min_c': 18,
    'max_c': 27,
    'humidity_pct': 55,
    'wind_kmh': 15,
    'condition': 'Cielo despejado',
    'icon': '01d',
    'observed_at': '2026-04-22T12:00:00+00:00',
}


@pytest.fixture(autouse=True)
def mock_weather_service(monkeypatch):
    """Mock get_weather para evitar llamadas reales a OpenWeatherMap."""
    async def _fake_get_weather(city: str) -> dict:
        return MOCK_WEATHER_PAYLOAD

    monkeypatch.setattr('routers.weather.get_weather', _fake_get_weather)


def test_weather_200_for_salta(client):
    """GET /api/weather?city=salta → 200."""
    r = client.get('/api/weather', params={'city': 'salta'})
    assert r.status_code == 200


def test_weather_response_schema(client):
    """Response matches the WeatherResponse schema."""
    r = client.get('/api/weather', params={'city': 'salta'})
    data = r.json()
    for key in ('city', 'temp_c', 'feels_like_c', 'min_c', 'max_c',
                'humidity_pct', 'wind_kmh', 'condition', 'icon', 'observed_at'):
        assert key in data, f"Missing key: {key}"


def test_weather_400_unknown_city(client):
    """GET /api/weather?city=london → 400 (not supported)."""
    r = client.get('/api/weather', params={'city': 'london'})
    assert r.status_code == 400


def test_weather_default_city_is_salta(client):
    """No ?city param → defaults to salta and returns 200."""
    r = client.get('/api/weather')
    assert r.status_code == 200


def test_weather_payload_values(client):
    """Returned payload matches the mocked values."""
    r = client.get('/api/weather', params={'city': 'salta'})
    data = r.json()
    assert data['city'] == 'Salta'
    assert data['condition'] == 'Cielo despejado'
    assert isinstance(data['temp_c'], int)
