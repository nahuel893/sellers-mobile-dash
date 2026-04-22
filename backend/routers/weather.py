"""Endpoint del clima: proxy hacia OpenWeatherMap con cache en proceso."""
from fastapi import APIRouter, HTTPException, Query

from schemas import WeatherResponse
from services.weather_service import CITY_MAP, get_weather

router = APIRouter(prefix="/api", tags=["weather"])


@router.get("/weather", response_model=WeatherResponse)
async def get_weather_endpoint(
    city: str = Query('salta', description="Ciudad (solo 'salta' soportada actualmente)"),
):
    """Retorna datos del clima para la ciudad solicitada.

    Responde 200 incluso si OpenWeatherMap falla (fallback con condition='desconocido').
    """
    if city not in CITY_MAP:
        raise HTTPException(status_code=400, detail=f'Ciudad no soportada: {city}')

    data = await get_weather(city)
    return WeatherResponse(**data)
