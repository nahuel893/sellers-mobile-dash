"""Tests para el servicio de clima (OpenWeatherMap proxy con cache)."""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.weather_service import (
    CACHE_TTL,
    CITY_MAP,
    _cache,
    _fallback,
    _normalize,
    get_weather,
)

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

SAMPLE_OWM_RESPONSE = {
    'name': 'Salta',
    'main': {
        'temp': 23.4,
        'feels_like': 22.1,
        'temp_min': 18.0,
        'temp_max': 26.5,
        'humidity': 55,
    },
    'wind': {'speed': 4.2},   # m/s → 15 km/h
    'weather': [{'description': 'cielo despejado', 'icon': '01d'}],
    'dt': 1714000000,
}


def _make_httpx_mock(response_data: dict | None = None, status_code: int = 200):
    """Creates an async context manager mock for httpx.AsyncClient."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    if response_data:
        mock_response.json.return_value = response_data
        mock_response.raise_for_status = MagicMock()  # no-op
    else:
        mock_response.raise_for_status.side_effect = Exception("upstream error")

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# --------------------------------------------------------------------------
# _normalize
# --------------------------------------------------------------------------

def test_normalize_temp_rounded():
    """temp_c is int (rounded)."""
    result = _normalize(SAMPLE_OWM_RESPONSE)
    assert result['temp_c'] == 23  # round(23.4)


def test_normalize_wind_kmh():
    """wind_kmh = m/s * 3.6, rounded."""
    result = _normalize(SAMPLE_OWM_RESPONSE)
    assert result['wind_kmh'] == round(4.2 * 3.6)


def test_normalize_condition_capitalized():
    """condition is the description capitalized."""
    result = _normalize(SAMPLE_OWM_RESPONSE)
    assert result['condition'] == 'Cielo despejado'


def test_normalize_all_fields():
    """All required fields are present."""
    result = _normalize(SAMPLE_OWM_RESPONSE)
    for key in ('city', 'temp_c', 'feels_like_c', 'min_c', 'max_c',
                'humidity_pct', 'wind_kmh', 'condition', 'icon', 'observed_at'):
        assert key in result, f"Missing key: {key}"


# --------------------------------------------------------------------------
# _fallback
# --------------------------------------------------------------------------

def test_fallback_condition_desconocido():
    """Fallback payload has condition='desconocido'."""
    fb = _fallback()
    assert fb['condition'] == 'desconocido'


def test_fallback_all_fields_present():
    """Fallback payload has all required keys."""
    fb = _fallback()
    for key in ('city', 'temp_c', 'feels_like_c', 'min_c', 'max_c',
                'humidity_pct', 'wind_kmh', 'condition', 'icon', 'observed_at'):
        assert key in fb, f"Missing key in fallback: {key}"


# --------------------------------------------------------------------------
# get_weather — success
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_weather_success_normalizes_payload(monkeypatch):
    """Success path normalizes the OWM response correctly."""
    _cache.clear()
    monkeypatch.setenv('OPENWEATHER_API_KEY', 'test-key')
    mock_client = _make_httpx_mock(SAMPLE_OWM_RESPONSE)

    with patch('services.weather_service.httpx.AsyncClient', return_value=mock_client):
        result = await get_weather('salta')

    assert result['condition'] == 'Cielo despejado'
    assert result['wind_kmh'] == round(4.2 * 3.6)
    assert isinstance(result['temp_c'], int)


# --------------------------------------------------------------------------
# get_weather — upstream failure → fallback
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_weather_upstream_503_returns_fallback(monkeypatch):
    """Upstream error → fallback with condition='desconocido', status 200 to caller."""
    _cache.clear()
    monkeypatch.setenv('OPENWEATHER_API_KEY', 'test-key')
    mock_client = _make_httpx_mock(None, status_code=503)

    with patch('services.weather_service.httpx.AsyncClient', return_value=mock_client):
        result = await get_weather('salta')

    assert result['condition'] == 'desconocido'


# --------------------------------------------------------------------------
# get_weather — cache
# --------------------------------------------------------------------------

@pytest.mark.anyio
async def test_cache_hit_within_ttl_single_httpx_call(monkeypatch):
    """Second call within TTL uses cache — only one httpx call total."""
    _cache.clear()
    monkeypatch.setenv('OPENWEATHER_API_KEY', 'test-key')
    call_count = 0
    original_response = dict(SAMPLE_OWM_RESPONSE)

    # httpx.AsyncClient is instantiated synchronously; the factory must be sync.
    def _fake_client_factory(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return _make_httpx_mock(original_response)

    with patch('services.weather_service.httpx.AsyncClient', side_effect=_fake_client_factory):
        await get_weather('salta')
        await get_weather('salta')  # Should hit cache

    assert call_count == 1


@pytest.mark.anyio
async def test_cache_miss_after_ttl_two_httpx_calls(monkeypatch):
    """After TTL expires, next call makes a fresh httpx request."""
    _cache.clear()
    monkeypatch.setenv('OPENWEATHER_API_KEY', 'test-key')
    call_count = 0

    def _fake_client_factory(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return _make_httpx_mock(SAMPLE_OWM_RESPONSE)

    with patch('services.weather_service.httpx.AsyncClient', side_effect=_fake_client_factory):
        await get_weather('salta')
        # Manually expire the cache entry
        city_key = 'salta'
        if city_key in _cache:
            ts, payload = _cache[city_key]
            _cache[city_key] = (ts - CACHE_TTL - 1, payload)
        await get_weather('salta')  # Should miss cache

    assert call_count == 2
