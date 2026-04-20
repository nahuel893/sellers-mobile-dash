"""Endpoints de búsqueda y detalle de clientes para el mapa de ventas."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from auth.dependencies import get_current_active_user
from auth.models import UserInDB
from data.db import get_connection, release_connection
from schemas_ventas_mapa import VentasClienteBusqueda, VentasClienteDetalle
from services.ventas_cliente_service import buscar_clientes, LIMIT_MAX
from services.ventas_cliente_detalle_service import get_cliente_detalle

router = APIRouter(prefix="/api/ventas-cliente", tags=["ventas-cliente"])
logger = logging.getLogger(__name__)


@router.get("/buscar", response_model=list[VentasClienteBusqueda])
def buscar(
    q: str = Query(..., description="Término de búsqueda (mínimo 2 caracteres)"),
    limit: int = Query(50, ge=1, le=LIMIT_MAX, description="Máximo de resultados (1-200)"),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Busca clientes por razon_social, fantasia o id_cliente.

    - Mínimo 2 caracteres para ejecutar la búsqueda (retorna [] si q < 2).
    - Respeta RBAC por sucursal.
    - Incluye latitud/longitud para hacer flyTo al seleccionar un resultado.
      Si latitud/longitud son null el cliente no tiene coordenadas registradas.
    """
    try:
        conn = get_connection()
        try:
            rows = buscar_clientes(
                conn=conn,
                q=q,
                role_name=current_user.role_name,
                sucursales_usuario=current_user.sucursales,
                limit=limit,
            )
        finally:
            release_connection(conn)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error buscando clientes (q=%r): %s", q, exc)
        raise HTTPException(status_code=503, detail="Error al buscar clientes")

    return [VentasClienteBusqueda(**row) for row in rows]


@router.get("/{id_cliente}", response_model=VentasClienteDetalle)
def detalle_cliente(
    id_cliente: int,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """
    Retorna el detalle de un cliente: info maestros, KPIs del mes actual
    y tabla jerárquica de ventas de los últimos 12 meses calendario.

    - Respeta RBAC por sucursal (admin/gerente ven todos).
    - 404 si el cliente no existe o está anulado.
    - 403 si el usuario no tiene acceso a la sucursal del cliente.
    """
    try:
        conn = get_connection()
        try:
            result = get_cliente_detalle(
                conn=conn,
                id_cliente=id_cliente,
                role_name=current_user.role_name,
                sucursales_usuario=current_user.sucursales,
            )
        finally:
            release_connection(conn)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error obteniendo detalle de cliente (id=%d): %s", id_cliente, exc)
        raise HTTPException(status_code=503, detail="Error al obtener detalle del cliente")

    return VentasClienteDetalle(**result)
