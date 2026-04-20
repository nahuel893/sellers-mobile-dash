"""
Capa de servicio para búsqueda de clientes.

Endpoint: GET /api/ventas-cliente/buscar?q=...&limit=50
Busca por razon_social, fantasia o id_cliente (ILIKE).
Aplica RBAC por sucursal (admin/gerente ven todo).
"""
from __future__ import annotations

import logging
from typing import Optional

from ventas_constants import ROLES_SIN_FILTRO_SUCURSAL
from services.ventas_mapa_service import _sucursal_filter

logger = logging.getLogger(__name__)

# Máximo de resultados que puede retornar el endpoint
LIMIT_MAX = 200
# Mínimo de caracteres para ejecutar la búsqueda
Q_MIN_LENGTH = 2


def buscar_clientes(
    conn,
    q: str,
    role_name: str,
    sucursales_usuario: list[int] | None,
    limit: int = 50,
) -> list[dict]:
    """
    Busca clientes en gold.dim_cliente por razon_social, fantasia o id_cliente.

    - q < Q_MIN_LENGTH → retorna [] sin ejecutar query (guard de performance).
    - limit se recorta a LIMIT_MAX si excede el máximo.
    - RBAC: admin/gerente ven todo; otros roles ven solo sus sucursales.
    - Incluye latitud/longitud (pueden ser NULL para clientes sin coords).

    Returns:
        Lista de dicts con keys:
            id_cliente, razon_social, fantasia, localidad, sucursal, latitud, longitud
    """
    if not q or len(q) < Q_MIN_LENGTH:
        return []

    # Recortar limit
    limit = min(limit, LIMIT_MAX)

    # Patrón ILIKE para razon_social y fantasia
    q_pattern = f"%{q}%"

    params: dict = {
        "q_ilike": q_pattern,
        "q_id": q,   # para cast de id_cliente (LIKE exacto sobre texto)
        "limit": limit,
    }

    # RBAC
    suc_sql, suc_params = _sucursal_filter(sucursales_usuario, role_name, table_alias="c")
    if suc_sql:
        # suc_sql viene como "AND c.id_sucursal = ANY(%(sucursales)s)"
        rbac_clause = f"\n              {suc_sql}"
        params.update(suc_params)
    else:
        rbac_clause = ""

    sql = f"""
        SELECT
            c.id_cliente,
            c.razon_social,
            c.fantasia,
            c.des_localidad        AS localidad,
            ds.descripcion         AS sucursal,
            c.latitud,
            c.longitud
        FROM gold.dim_cliente c
        LEFT JOIN gold.dim_sucursal ds
            ON ds.id_sucursal = c.id_sucursal
        WHERE c.anulado = FALSE
          AND (
            c.razon_social ILIKE %(q_ilike)s
            OR c.fantasia   ILIKE %(q_ilike)s
            OR CAST(c.id_cliente AS TEXT) LIKE %(q_id)s
          ){rbac_clause}
        ORDER BY c.fantasia NULLS LAST, c.razon_social
        LIMIT %(limit)s
    """

    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    finally:
        cur.close()

    return [dict(zip(cols, row)) for row in rows]
