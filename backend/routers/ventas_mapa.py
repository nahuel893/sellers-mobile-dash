"""Endpoints del mapa de ventas: clientes con métricas y hover."""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from auth.dependencies import get_current_active_user
from auth.models import UserInDB
from data.db import get_connection, release_connection
from schemas_ventas_mapa import VentasCliente, VentasHoverCliente
from services.ventas_mapa_service import get_clientes_mapa, get_hover_cliente
from ventas_constants import METRICAS_VALIDAS, FV_PREVENTA

router = APIRouter(prefix="/api/ventas-mapa", tags=["ventas-mapa"])
logger = logging.getLogger(__name__)


@router.get("/clientes", response_model=list[VentasCliente])
def get_mapa_clientes(
    fecha_ini: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    fv: str = Query(FV_PREVENTA, description="Fuerza de ventas: '1' (preventa), '4' (autoventa), 'AMBAS'"),
    canal: Optional[str] = Query(None, description="Filtro canal de marketing"),
    subcanal: Optional[str] = Query(None, description="Filtro subcanal de marketing"),
    localidad: Optional[str] = Query(None, description="Filtro localidad"),
    lista_precio: Optional[int] = Query(None, description="Filtro lista de precio"),
    sucursal_id: Optional[int] = Query(None, description="Filtro sucursal por ID"),
    ruta: Optional[str] = Query(None, description="Ruta compuesta 'id_sucursal|id_ruta'"),
    preventista: Optional[str] = Query(None, description="Nombre del preventista"),
    genericos: Optional[list[str]] = Query(None, description="Lista de genéricos a filtrar"),
    marcas: Optional[list[str]] = Query(None, description="Lista de marcas a filtrar"),
    metrica: str = Query("bultos", description="Métrica: bultos | facturacion | documentos"),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Retorna clientes con coordenadas y métricas agregadas para el período.

    Solo clientes con latitud/longitud válidas (no null, no 0).
    Respeta RBAC por sucursal.
    """
    if fecha_ini > fecha_fin:
        raise HTTPException(status_code=400, detail="fecha_ini no puede ser posterior a fecha_fin")

    if metrica not in METRICAS_VALIDAS:
        raise HTTPException(
            status_code=400,
            detail=f"Métrica inválida. Opciones: {', '.join(sorted(METRICAS_VALIDAS))}",
        )

    try:
        conn = get_connection()
        try:
            rows = get_clientes_mapa(
                conn=conn,
                role_name=current_user.role_name,
                sucursales_usuario=current_user.sucursales,
                fecha_ini=fecha_ini,
                fecha_fin=fecha_fin,
                fv=fv,
                canal=canal,
                subcanal=subcanal,
                localidad=localidad,
                lista_precio=lista_precio,
                sucursal_id=sucursal_id,
                ruta=ruta,
                preventista=preventista,
                genericos=genericos,
                marcas=marcas,
                metrica=metrica,
            )
        finally:
            release_connection(conn)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error cargando clientes mapa: %s", exc)
        raise HTTPException(status_code=503, detail="Error al consultar datos de clientes")

    return [VentasCliente(**row) for row in rows]


@router.get("/cliente/{id_cliente}/hover", response_model=VentasHoverCliente)
def get_hover(
    id_cliente: int,
    fecha_ini: date = Query(..., description="Fecha inicio del período actual (YYYY-MM-DD)"),
    fecha_fin: date = Query(..., description="Fecha fin del período actual (YYYY-MM-DD)"),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Retorna top 5 genéricos (por total histórico) + GENERICOS_HOVER_FIJOS para un cliente.

    MAct = suma del período seleccionado.
    MAnt = suma del mismo rango pero del mes/período anterior.
    """
    if fecha_ini > fecha_fin:
        raise HTTPException(status_code=400, detail="fecha_ini no puede ser posterior a fecha_fin")

    try:
        conn = get_connection()
        try:
            data = get_hover_cliente(
                conn=conn,
                id_cliente=id_cliente,
                fecha_ini=fecha_ini,
                fecha_fin=fecha_fin,
            )
        finally:
            release_connection(conn)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error cargando hover para cliente %s: %s", id_cliente, exc)
        raise HTTPException(status_code=503, detail="Error al consultar datos del cliente")

    return VentasHoverCliente(**data)
