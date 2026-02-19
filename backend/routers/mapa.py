"""Endpoint de mapa: clientes con coordenadas para un vendedor."""
import logging

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from utils import from_slug
from dependencies import get_df
from schemas import ClienteResponse

router = APIRouter(prefix="/api", tags=["mapa"])
logger = logging.getLogger(__name__)


@router.get("/mapa/{vendor_slug}", response_model=list[ClienteResponse])
def get_mapa_vendedor(
    vendor_slug: str,
    sucursal: Optional[str] = Query(None, description="ID numérico de sucursal"),
    df: pd.DataFrame = Depends(get_df),
):
    vendedor = from_slug(vendor_slug)

    # Resolver sucursal ID
    id_sucursal = sucursal
    if not id_sucursal:
        vendor_data = df[df['vendedor'] == vendedor]
        if vendor_data.empty:
            raise HTTPException(status_code=404, detail=f'Vendedor "{vendedor}" no encontrado')
        suc = str(vendor_data.iloc[0]['sucursal'])
        id_sucursal = suc.split(' - ')[0] if ' - ' in suc else None

    if not id_sucursal:
        raise HTTPException(status_code=400, detail='No se pudo determinar la sucursal')

    try:
        from data.db import get_connection, release_connection
        from data.queries import query_clientes_vendedor
        conn = get_connection()
        try:
            df_clientes = query_clientes_vendedor(conn, vendedor, id_sucursal)
        finally:
            release_connection(conn)
    except Exception as e:
        logger.error('Error cargando mapa para %s (suc %s): %s', vendedor, id_sucursal, e)
        raise HTTPException(status_code=503, detail='Error al consultar datos de clientes')

    return [
        ClienteResponse(
            razon_social=row['razon_social'],
            fantasia=row.get('fantasia'),
            latitud=row['latitud'],
            longitud=row['longitud'],
            des_localidad=row.get('des_localidad'),
        )
        for _, row in df_clientes.iterrows()
    ]
