"""Endpoint de preventistas: listado para la barra lateral del dashboard."""
import pandas as pd
from fastapi import APIRouter, Depends, Query

from dependencies import get_df
from schemas import PreventistaItem
from services.preventistas_service import get_preventistas

router = APIRouter(prefix="/api", tags=["preventistas"])


@router.get("/preventistas", response_model=list[PreventistaItem])
def listar_preventistas(
    sucursal: int = Query(1, description="ID numérico de sucursal"),
    df: pd.DataFrame = Depends(get_df),
):
    """Lista preventistas de una sucursal, ordenados por nombre."""
    items = get_preventistas(df, sucursal_id=sucursal)
    return [PreventistaItem(**item) for item in items]
