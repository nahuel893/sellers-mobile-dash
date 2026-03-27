"""Endpoints de cobertura por marca."""
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, Query

from data.data_loader import get_cobertura_dataframe
from schemas import (
    CoberturaMarcaItem,
    CoberturaVendedorResponse,
    CoberturaResponse,
)

router = APIRouter(prefix="/api", tags=["cobertura"])


def _get_cobertura_df() -> pd.DataFrame:
    """Dependency: provee DataFrame de cobertura cacheado por día."""
    return get_cobertura_dataframe()


@router.get("/cobertura", response_model=CoberturaResponse)
def get_cobertura(
    sucursal: Optional[str] = Query(None),
    supervisor: Optional[str] = Query(None),
    vendedor: Optional[str] = Query(None),
    df: pd.DataFrame = Depends(_get_cobertura_df),
):
    """Cobertura por marca agrupada por vendedor."""
    if df.empty:
        return CoberturaResponse(sucursal=sucursal or "TODAS", vendedores=[])

    # Filtrar por sucursal
    if sucursal:
        df = df[df['sucursal'] == sucursal]

    # Filtrar por supervisor
    if supervisor:
        df = df[df['supervisor'] == supervisor]

    # Filtrar por vendedor
    if vendedor:
        df = df[df['vendedor'] == vendedor]

    if df.empty:
        return CoberturaResponse(sucursal=sucursal or "TODAS", vendedores=[])

    # Agrupar por vendedor
    vendedores = []
    for (vendedor, suc), grupo in df.groupby(['vendedor', 'sucursal'], sort=True):
        # Marcas ordenadas por cupo descendente
        marcas_df = grupo.sort_values('cupo_cobertura', ascending=False)
        marcas = [
            CoberturaMarcaItem(
                marca=row['marca'],
                cobertura=int(row['cobertura']),
                cupo=int(row['cupo_cobertura']),
                pct_cobertura=round(float(row['pct_cobertura']), 1),
            )
            for _, row in marcas_df.iterrows()
        ]

        total_cobertura = int(grupo['cobertura'].sum())
        total_cupo = int(grupo['cupo_cobertura'].sum())
        pct_total = round(total_cobertura / total_cupo * 100, 1) if total_cupo > 0 else 0.0

        vendedores.append(CoberturaVendedorResponse(
            vendedor=vendedor,
            sucursal=suc,
            marcas=marcas,
            total_cobertura=total_cobertura,
            total_cupo=total_cupo,
            pct_total=pct_total,
        ))

    # Ordenar vendedores alfabéticamente
    vendedores.sort(key=lambda v: v.vendedor)

    return CoberturaResponse(
        sucursal=sucursal or "TODAS",
        vendedores=vendedores,
    )
