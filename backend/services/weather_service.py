"""
Servicio de clima: proxy hacia OpenWeatherMap con cache en proceso.

Configuración:
  OPENWEATHER_API_KEY — variable de entorno (sin key usa fallback silencioso).
  CACHE_TTL = 600 s (10 min).
"""
import os
import time
from datetime import datetime, timezone

import httpx

# --- Configuración ---
CACHE_TTL = 600  # 10 minutos

# Ciudades soportadas: nombre público → query para OWM
CITY_MAP: dict[str, str] = {
    'salta': 'Salta,AR',
}

# Cache en proceso: city → (timestamp, payload)
_cache: dict[str, tuple[float, dict]] = {}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _normalize(d: dict) -> dict:
    """Normaliza la respuesta JSON de OpenWeatherMap al schema interno."""
    return {
        'city': d['name'],
        'temp_c': round(d['main']['temp']),
        'feels_like_c': round(d['main']['feels_like']),
        'min_c': round(d['main']['temp_min']),
        'max_c': round(d['main']['temp_max']),
        'humidity_pct': d['main']['humidity'],
        'wind_kmh': round(d['wind']['speed'] * 3.6),
        'condition': d['weather'][0]['description'].capitalize(),
        'icon': d['weather'][0]['icon'],
        'observed_at': datetime.fromtimestamp(d['dt'], tz=timezone.utc).isoformat(),
    }


def _fallback(city: str = 'salta') -> dict:
    """Payload de fallback cuando la API falla o la key está ausente."""
    return {
        'city': city.capitalize(),
        'temp_c': 0,
        'feels_like_c': 0,
        'min_c': 0,
        'max_c': 0,
        'humidity_pct': 0,
        'wind_kmh': 0,
        'condition': 'desconocido',
        'icon': '',
        'observed_at': datetime.now(tz=timezone.utc).isoformat(),
    }


# --------------------------------------------------------------------------
# Servicio principal
# --------------------------------------------------------------------------

async def get_weather(city: str) -> dict:
    """Retorna datos del clima para la ciudad solicitada.

    Args:
        city: nombre corto de ciudad (debe estar en CITY_MAP).

    Returns:
        Dict con keys: city, temp_c, feels_like_c, min_c, max_c, humidity_pct,
        wind_kmh, condition, icon, observed_at.
        En caso de error upstream, retorna fallback con condition='desconocido'.
    """
    now = time.time()

    # Verificar cache
    if city in _cache:
        ts, payload = _cache[city]
        if now - ts < CACHE_TTL:
            return payload

    api_key = os.environ.get('OPENWEATHER_API_KEY', '')

    if not api_key:
        payload = _fallback(city)
        _cache[city] = (now, payload)
        return payload

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                'https://api.openweathermap.org/data/2.5/weather',
                params={
                    'q': CITY_MAP[city],
                    'appid': api_key,
                    'units': 'metric',
                    'lang': 'es',
                },
            )
            r.raise_for_status()
            data = r.json()
        payload = _normalize(data)
    except Exception:
        payload = _fallback(city)

    _cache[city] = (now, payload)
    return payload
