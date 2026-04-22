"""Endpoints de avance: sparkline diario y delta vs mes anterior."""
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from data.gold_db import get_connection as get_gold_connection
from data.gold_db import release_connection as release_gold_connection
from dependencies import get_df
from schemas import DeltaResponse, SparklineDia, SparklineResponse
from services.ventas_service import get_delta_vendedor, get_sparkline_vendedor
from utils import from_slug

router = APIRouter(prefix="/api/avance", tags=["avance"])

_AGGREGATE_SLUGS = {'casa-central', 'cc'}


# ============================================================
# Sparkline endpoint
# ============================================================

@router.get("/sparkline/{slug}", response_model=SparklineResponse)
def get_sparkline(
    slug: str,
    dias: int = Query(18, ge=1, le=90),
    categoria: str = Query('CERVEZAS'),
    df: pd.DataFrame = Depends(get_df),
):
    """Retorna serie de ventas diarias por grupo_marca para el sparkline."""
    if slug.lower() in _AGGREGATE_SLUGS:
        vendedor = None
    else:
        vendedor = from_slug(slug)
        if vendedor not in df['vendedor'].values:
            raise HTTPException(status_code=404, detail=f'Vendedor "{vendedor}" no encontrado')

    conn = get_gold_connection()
    try:
        data = get_sparkline_vendedor(conn, vendedor=vendedor, dias=dias,
                                      categoria=categoria, id_sucursal=1)
    finally:
        release_gold_connection(conn)

    return SparklineResponse(
        vendedor=data['vendedor'],
        dias=data['dias'],
        puntos=[
            SparklineDia(fecha=p['fecha'], por_grupo=p['por_grupo'])
            for p in data['puntos']
        ],
    )


# ============================================================
# Delta endpoint
# ============================================================

@router.get("/delta/{slug}", response_model=DeltaResponse)
def get_delta(
    slug: str,
    categoria: str = Query('CERVEZAS'),
    df: pd.DataFrame = Depends(get_df),
):
    """Retorna delta pp (mes actual vs mes anterior) por grupo_marca."""
    if slug.lower() in _AGGREGATE_SLUGS:
        vendedor = None
    else:
        vendedor = from_slug(slug)
        if vendedor not in df['vendedor'].values:
            raise HTTPException(status_code=404, detail=f'Vendedor "{vendedor}" no encontrado')

    conn = get_gold_connection()
    try:
        data = get_delta_vendedor(conn, df=df, vendedor=vendedor,
                                  categoria=categoria, id_sucursal=1)
    finally:
        release_gold_connection(conn)

    return data
