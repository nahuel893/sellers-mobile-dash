"""Endpoint de filtros para ventas-mapa."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from auth.dependencies import get_current_active_user
from auth.models import UserInDB
from data.db import get_connection, release_connection
from schemas_ventas_mapa import VentasFiltrosOpciones
from services.ventas_mapa_service import get_filtros_opciones

router = APIRouter(prefix="/api/ventas-filtros", tags=["ventas-filtros"])
logger = logging.getLogger(__name__)


@router.get("/opciones", response_model=VentasFiltrosOpciones)
def get_opciones_filtros(
    fv: Optional[str] = Query(None, description="Fuerza de ventas: '1', '4' o 'AMBAS'"),
    fecha_ini: Optional[str] = Query(None, description="Fecha inicio ISO (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin ISO (YYYY-MM-DD)"),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Retorna las opciones disponibles para cada dimensión de filtro.

    Respeta RBAC: admin/gerente ven todas las sucursales; supervisor solo las suyas.
    Para Fase 2: retorna todos los valores sin cascade reactivo.
    """
    try:
        conn = get_connection()
        try:
            data = get_filtros_opciones(
                conn=conn,
                role_name=current_user.role_name,
                sucursales_usuario=current_user.sucursales,
            )
        finally:
            release_connection(conn)
    except Exception as exc:
        logger.error("Error obteniendo opciones de filtros: %s", exc)
        raise HTTPException(status_code=503, detail="Error al consultar opciones de filtros")

    return VentasFiltrosOpciones(**data)
