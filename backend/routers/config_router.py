"""Endpoints de configuración."""
from datetime import date

from fastapi import APIRouter

from config import get_dias_habiles
from schemas import DiasHabilesResponse

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/dias-habiles", response_model=DiasHabilesResponse)
def dias_habiles():
    habiles, transcurridos, restantes = get_dias_habiles()
    return DiasHabilesResponse(
        habiles=habiles,
        transcurridos=transcurridos,
        restantes=restantes,
        fecha=date.today().isoformat(),
    )
