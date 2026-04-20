"""
Servicio: compro/no-compro de clientes para el mapa de ventas.

Consulta clientes con coordenadas válidas e indica si compraron
en el período solicitado, más la última fecha de compra histórica.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from services.ventas_mapa_service import (
    _sucursal_filter,
    _fv_join_columns,
    _fv_fact_ventas_filter,
)
from ventas_constants import FV_PREVENTA

logger = logging.getLogger(__name__)


def get_compro_data(
    conn,
    role_name: str,
    sucursales_usuario: list[int] | None,
    fecha_ini: date,
    fecha_fin: date,
    fv: str = FV_PREVENTA,
    canal: Optional[str] = None,
    subcanal: Optional[str] = None,
    localidad: Optional[str] = None,
    lista_precio: Optional[int] = None,
    sucursal_id: Optional[int] = None,
    ruta: Optional[str] = None,
    preventista: Optional[str] = None,
) -> list[dict]:
    """
    Retorna clientes con coordenadas e indicador de compra en el período.

    - compro = True si el cliente tiene alguna venta en [fecha_ini, fecha_fin]
    - ultima_compra = MAX(fecha_comprobante) de TODA la historia (no limitada al período)
      Muestra cuándo fue la última vez que compró, independientemente del período analizado.

    Solo incluye clientes con latitud/longitud válidas (no null, no 0).
    Respeta RBAC por sucursal.
    """
    params: dict = {
        "fecha_ini": fecha_ini,
        "fecha_fin": fecha_fin,
    }

    where_clauses: list[str] = [
        "c.anulado = FALSE",
        "c.latitud IS NOT NULL",
        "c.latitud != 0",
        "c.longitud IS NOT NULL",
        "c.longitud != 0",
    ]

    # RBAC
    suc_sql, suc_params = _sucursal_filter(sucursales_usuario, role_name, table_alias="c")
    if suc_sql:
        where_clauses.append(suc_sql.lstrip("AND ").strip())
        params.update(suc_params)

    # Filtro canal
    if canal:
        where_clauses.append("c.des_canal_mkt = %(canal)s")
        params["canal"] = canal

    # Filtro subcanal
    if subcanal:
        where_clauses.append("c.des_subcanal_mkt = %(subcanal)s")
        params["subcanal"] = subcanal

    # Filtro localidad
    if localidad:
        where_clauses.append("c.des_localidad = %(localidad)s")
        params["localidad"] = localidad

    # Filtro lista de precio
    if lista_precio is not None:
        where_clauses.append("c.id_lista_precio = %(lista_precio)s")
        params["lista_precio"] = lista_precio

    # Filtro sucursal explícito
    if sucursal_id is not None:
        where_clauses.append("c.id_sucursal = %(sucursal_id)s")
        params["sucursal_id"] = sucursal_id

    # Fuerza de ventas — columnas de ruta/preventista en dim_cliente
    ruta_col, preventista_col = _fv_join_columns(fv)

    # Filtro ruta (clave compuesta "id_sucursal|id_ruta")
    if ruta:
        parts = ruta.split("|", 1)
        if len(parts) == 2:
            where_clauses.append(
                f"c.id_sucursal || '|' || c.{ruta_col} = %(ruta)s"
            )
            params["ruta"] = ruta

    # Filtro preventista
    if preventista:
        where_clauses.append(f"c.{preventista_col} = %(preventista)s")
        params["preventista"] = preventista

    # FV filter para fact_ventas del período
    fv_sql, fv_params = _fv_fact_ventas_filter(fv)
    params.update(fv_params)

    where_sql = "\n              AND ".join(where_clauses)

    sql = f"""
        SELECT
            c.id_cliente,
            c.latitud,
            c.longitud,
            -- compro: True si tiene al menos una venta en el período
            CASE
                WHEN COUNT(f_period.nro_doc) > 0 THEN TRUE
                ELSE FALSE
            END                                                     AS compro,
            -- ultima_compra: MAX histórico, no limitado al período
            (
                SELECT MAX(fh.fecha_comprobante)
                FROM gold.fact_ventas fh
                WHERE fh.id_cliente = c.id_cliente
                  AND fh.id_sucursal = c.id_sucursal
            )                                                       AS ultima_compra
        FROM gold.dim_cliente c
        LEFT JOIN gold.fact_ventas f_period
            ON f_period.id_cliente = c.id_cliente
            AND f_period.id_sucursal = c.id_sucursal
            AND f_period.fecha_comprobante BETWEEN %(fecha_ini)s AND %(fecha_fin)s
            {fv_sql}
        WHERE {where_sql}
        GROUP BY c.id_cliente, c.latitud, c.longitud
        ORDER BY c.id_cliente
    """

    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
    finally:
        cur.close()

    return [
        {
            "id_cliente": row[0],
            "lat": float(row[1]),
            "lon": float(row[2]),
            "compro": bool(row[3]),
            "ultima_compra": row[4],  # date | None
        }
        for row in rows
    ]
