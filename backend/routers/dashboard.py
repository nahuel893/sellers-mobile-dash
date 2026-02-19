"""Endpoints principales del dashboard."""
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from config import CATEGORIAS
from dependencies import get_df
from services.ventas_service import (
    get_sucursales, get_supervisores, get_vendedores_por_supervisor,
    get_datos_vendedor, get_resumen_vendedor,
    get_datos_supervisor, get_resumen_supervisor,
    get_datos_sucursal, get_resumen_sucursal,
)
from utils import to_slug, from_slug, find_sucursal
from schemas import (
    CategoryData, DatosMarcaResponse, ResumenResponse,
    VendedorListItem, VendedorDetailResponse,
    SupervisorDetailResponse, SucursalDetailResponse,
    DashboardResponse,
)

router = APIRouter(prefix="/api", tags=["dashboard"])


# ============================================================
# Helpers internos
# ============================================================

def _build_category_data(datos_df, resumen_dict):
    """Construye CategoryData desde un DataFrame de datos y un dict de resumen."""
    # Filtrar TOTAL_CERVEZAS de los datos (solo se usa internamente para cupo)
    datos_rows = datos_df[datos_df['grupo_marca'] != 'TOTAL_CERVEZAS']

    datos = [
        DatosMarcaResponse(
            grupo_marca=row.get('grupo_marca') if pd.notna(row.get('grupo_marca')) else None,
            pct_tendencia=round(float(row['pct_tendencia']), 2),
            ventas=int(row['ventas']),
            cupo=int(row['cupo']),
            falta=int(row['falta']),
            tendencia=round(float(row['tendencia']), 2),
        )
        for _, row in datos_rows.iterrows()
    ]

    resumen = ResumenResponse(
        pct_tendencia=round(float(resumen_dict['pct_tendencia']), 2),
        ventas=int(resumen_dict['ventas']),
        cupo=int(resumen_dict['cupo']),
        falta=int(resumen_dict['falta']),
        tendencia=int(resumen_dict['tendencia']),
    )

    return CategoryData(resumen=resumen, datos=datos)


def _build_all_categories(df, datos_fn, resumen_fn):
    """Construye dict de CategoryData para todas las categorías."""
    result = {}
    for cat in CATEGORIAS:
        datos_df = datos_fn(cat)
        resumen_dict = resumen_fn(cat)
        result[cat] = _build_category_data(datos_df, resumen_dict)
    return result


def _build_vendedor_item(df, vendedor):
    """Construye un VendedorListItem para el listado del dashboard."""
    return VendedorListItem(
        nombre=vendedor,
        slug=to_slug(vendedor),
        categories=_build_all_categories(
            df,
            datos_fn=lambda cat, v=vendedor: get_datos_vendedor(df, v, cat),
            resumen_fn=lambda cat, v=vendedor: get_resumen_vendedor(df, v, cat),
        ),
    )


# ============================================================
# Endpoints de filtros
# ============================================================

@router.get("/sucursales", response_model=list[str])
def listar_sucursales(df: pd.DataFrame = Depends(get_df)):
    return get_sucursales(df)


@router.get("/supervisores", response_model=list[str])
def listar_supervisores(
    sucursal: Optional[str] = Query(None),
    df: pd.DataFrame = Depends(get_df),
):
    return get_supervisores(df, sucursal)


@router.get("/vendedores", response_model=list[str])
def listar_vendedores(
    supervisor: str = Query(...),
    sucursal: Optional[str] = Query(None),
    df: pd.DataFrame = Depends(get_df),
):
    return get_vendedores_por_supervisor(df, supervisor, sucursal)


# ============================================================
# Dashboard completo (vista home)
# ============================================================

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    supervisor: str = Query(...),
    sucursal: str = Query(...),
    df: pd.DataFrame = Depends(get_df),
):
    vendedores = get_vendedores_por_supervisor(df, supervisor, sucursal)

    return DashboardResponse(
        sucursal=_build_all_categories(
            df,
            datos_fn=lambda cat: get_datos_sucursal(df, sucursal, cat),
            resumen_fn=lambda cat: get_resumen_sucursal(df, sucursal, cat),
        ),
        supervisor=_build_all_categories(
            df,
            datos_fn=lambda cat: get_datos_supervisor(df, supervisor, sucursal, cat),
            resumen_fn=lambda cat: get_resumen_supervisor(df, supervisor, sucursal, cat),
        ),
        vendedores=[_build_vendedor_item(df, v) for v in vendedores],
    )


# ============================================================
# Detalle de vendedor
# ============================================================

@router.get("/vendedor/{slug}", response_model=VendedorDetailResponse)
def get_vendedor_detail(
    slug: str,
    df: pd.DataFrame = Depends(get_df),
):
    vendedor = from_slug(slug)

    # Verificar que el vendedor existe
    if vendedor not in df['vendedor'].values:
        raise HTTPException(status_code=404, detail=f'Vendedor "{vendedor}" no encontrado')

    return VendedorDetailResponse(
        nombre=vendedor,
        categories=_build_all_categories(
            df,
            datos_fn=lambda cat: get_datos_vendedor(df, vendedor, cat),
            resumen_fn=lambda cat: get_resumen_vendedor(df, vendedor, cat),
        ),
    )


# ============================================================
# Detalle de supervisor
# ============================================================

@router.get("/supervisor/{slug}", response_model=SupervisorDetailResponse)
def get_supervisor_detail(
    slug: str,
    sucursal: Optional[str] = Query(None, description="ID numérico de sucursal"),
    df: pd.DataFrame = Depends(get_df),
):
    supervisor = from_slug(slug)

    # Resolver sucursal por ID numérico
    sucursal_str = None
    if sucursal:
        sucursal_str = find_sucursal(df, sucursal)
        if not sucursal_str:
            raise HTTPException(status_code=404, detail=f'Sucursal "{sucursal}" no encontrada')

    # Verificar que el supervisor existe
    if supervisor not in df['supervisor'].values:
        raise HTTPException(status_code=404, detail=f'Supervisor "{supervisor}" no encontrado')

    vendedores = get_vendedores_por_supervisor(df, supervisor, sucursal_str)

    return SupervisorDetailResponse(
        nombre=supervisor,
        categories=_build_all_categories(
            df,
            datos_fn=lambda cat: get_datos_supervisor(df, supervisor, sucursal_str, cat),
            resumen_fn=lambda cat: get_resumen_supervisor(df, supervisor, sucursal_str, cat),
        ),
        vendedores=[_build_vendedor_item(df, v) for v in vendedores],
    )


# ============================================================
# Detalle de sucursal
# ============================================================

@router.get("/sucursal/{suc_id}", response_model=SucursalDetailResponse)
def get_sucursal_detail(
    suc_id: str,
    df: pd.DataFrame = Depends(get_df),
):
    sucursal_str = find_sucursal(df, suc_id)
    if not sucursal_str:
        raise HTTPException(status_code=404, detail=f'Sucursal "{suc_id}" no encontrada')

    supervisores = get_supervisores(df, sucursal_str)

    return SucursalDetailResponse(
        sucursal=sucursal_str,
        categories=_build_all_categories(
            df,
            datos_fn=lambda cat: get_datos_sucursal(df, sucursal_str, cat),
            resumen_fn=lambda cat: get_resumen_sucursal(df, sucursal_str, cat),
        ),
        supervisores=supervisores,
    )
