"""
Capa de servicio para ventas-mapa y ventas-filtros.

Toda consulta va directo a PostgreSQL (capa Gold) via psycopg2.
No usa Pandas para las queries mapa — devuelve dicts y listas Python.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

from ventas_constants import (
    GENERICOS_EXCLUIDOS,
    GENERICOS_HOVER_FIJOS,
    FV_PREVENTA,
    FV_AUTOVENTA,
    FV_AMBAS,
    ROLES_SIN_FILTRO_SUCURSAL,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _sucursal_filter(
    sucursales_usuario: list[int] | None,
    role_name: str,
    table_alias: str = "c",
) -> tuple[str, dict]:
    """
    Genera la cláusula WHERE para RBAC de sucursales.

    Admin/gerente → sin filtro (returns empty string and empty params).
    Otros roles → WHERE {table_alias}.id_sucursal = ANY(%(sucursales)s)

    Returns:
        (sql_fragment, params_dict)
    """
    if role_name in ROLES_SIN_FILTRO_SUCURSAL or not sucursales_usuario:
        return "", {}
    return (
        f"AND {table_alias}.id_sucursal = ANY(%(sucursales)s)",
        {"sucursales": sucursales_usuario},
    )


def _fv_join_columns(fv: str) -> tuple[str, str]:
    """
    Devuelve (columna_ruta, columna_preventista) para la fuerza de ventas.
    FV_AMBAS usa FV1 como referencia en dim_cliente.
    """
    if fv == FV_AUTOVENTA:
        return "id_ruta_fv4", "des_personal_fv4"
    # FV1 o AMBAS
    return "id_ruta_fv1", "des_personal_fv1"


def _fv_fact_ventas_filter(fv: str) -> tuple[str, dict]:
    """
    Genera el fragmento SQL + params para filtrar fact_ventas por fuerza de ventas.
    """
    if fv == FV_PREVENTA:
        return "AND f.id_fuerza_ventas = %(fv_id)s", {"fv_id": 1}
    if fv == FV_AUTOVENTA:
        return "AND f.id_fuerza_ventas = %(fv_id)s", {"fv_id": 4}
    # AMBAS — sin filtro adicional
    return "", {}


# ---------------------------------------------------------------------------
# Servicio: filtros opciones
# ---------------------------------------------------------------------------

def get_filtros_opciones(
    conn,
    role_name: str,
    sucursales_usuario: list[int] | None,
) -> dict:
    """
    Retorna todas las opciones de filtro disponibles.

    Para Fase 2: devuelve todos los valores sin cascade reactivo.
    La cascade es responsabilidad del frontend (Fase 3).
    """
    suc_sql, suc_params = _sucursal_filter(sucursales_usuario, role_name, table_alias="c")

    cur = conn.cursor()
    result: dict = {}

    try:
        # canales
        cur.execute(
            f"""
            SELECT DISTINCT des_canal_mkt
            FROM gold.dim_cliente c
            WHERE c.anulado = FALSE
              AND des_canal_mkt IS NOT NULL
              {suc_sql}
            ORDER BY 1
            """,
            suc_params,
        )
        result["canales"] = [r[0] for r in cur.fetchall()]

        # subcanales
        cur.execute(
            f"""
            SELECT DISTINCT des_subcanal_mkt
            FROM gold.dim_cliente c
            WHERE c.anulado = FALSE
              AND des_subcanal_mkt IS NOT NULL
              {suc_sql}
            ORDER BY 1
            """,
            suc_params,
        )
        result["subcanales"] = [r[0] for r in cur.fetchall()]

        # localidades
        cur.execute(
            f"""
            SELECT DISTINCT des_localidad
            FROM gold.dim_cliente c
            WHERE c.anulado = FALSE
              AND des_localidad IS NOT NULL
              {suc_sql}
            ORDER BY 1
            """,
            suc_params,
        )
        result["localidades"] = [r[0] for r in cur.fetchall()]

        # listas de precio
        cur.execute(
            f"""
            SELECT DISTINCT id_lista_precio, des_lista_precio
            FROM gold.dim_cliente c
            WHERE c.anulado = FALSE
              AND id_lista_precio IS NOT NULL
              {suc_sql}
            ORDER BY 1
            """,
            suc_params,
        )
        result["listas_precio"] = [
            {"id_lista_precio": r[0], "des_lista_precio": r[1]}
            for r in cur.fetchall()
        ]

        # sucursales (RBAC-aware)
        cur.execute(
            f"""
            SELECT DISTINCT c.id_sucursal, ds.descripcion
            FROM gold.dim_cliente c
            JOIN gold.dim_sucursal ds ON ds.id_sucursal = c.id_sucursal
            WHERE c.anulado = FALSE
              {suc_sql}
            ORDER BY 1
            """,
            suc_params,
        )
        result["sucursales"] = [
            {"id_sucursal": r[0], "des_sucursal": r[1]}
            for r in cur.fetchall()
        ]

        # rutas (clave compuesta id_sucursal|id_ruta_fv1)
        cur.execute(
            f"""
            SELECT DISTINCT c.id_sucursal, c.id_ruta_fv1
            FROM gold.dim_cliente c
            WHERE c.anulado = FALSE
              AND c.id_ruta_fv1 IS NOT NULL
              {suc_sql}
            ORDER BY 1, 2
            """,
            suc_params,
        )
        result["rutas"] = [
            f"{r[0]}|{r[1]}"
            for r in cur.fetchall()
        ]

        # preventistas (FV1 + FV4 unión)
        cur.execute(
            f"""
            SELECT DISTINCT preventista
            FROM (
                SELECT des_personal_fv1 AS preventista
                FROM gold.dim_cliente c
                WHERE c.anulado = FALSE AND des_personal_fv1 IS NOT NULL
                  {suc_sql}
                UNION
                SELECT des_personal_fv4
                FROM gold.dim_cliente c
                WHERE c.anulado = FALSE AND des_personal_fv4 IS NOT NULL
                  {suc_sql}
            ) sub
            ORDER BY 1
            """,
            {**suc_params},
        )
        result["preventistas"] = [r[0] for r in cur.fetchall()]

        # genéricos (excluir GENERICOS_EXCLUIDOS)
        cur.execute(
            """
            SELECT DISTINCT generico
            FROM gold.dim_articulo
            WHERE generico IS NOT NULL
              AND generico != ALL(%(excluidos)s)
            ORDER BY 1
            """,
            {"excluidos": GENERICOS_EXCLUIDOS},
        )
        result["genericos"] = [r[0] for r in cur.fetchall()]

        # marcas (excluir genéricos excluidos)
        cur.execute(
            """
            SELECT DISTINCT marca
            FROM gold.dim_articulo
            WHERE generico IS NOT NULL
              AND generico != ALL(%(excluidos)s)
              AND marca IS NOT NULL
            ORDER BY 1
            """,
            {"excluidos": GENERICOS_EXCLUIDOS},
        )
        result["marcas"] = [r[0] for r in cur.fetchall()]

        # rango de fechas
        cur.execute(
            """
            SELECT
              MIN(fecha_comprobante)::text,
              MAX(fecha_comprobante)::text
            FROM gold.fact_ventas
            WHERE fecha_comprobante IS NOT NULL
            """
        )
        row = cur.fetchone()
        result["fecha_min"] = row[0] if row else None
        result["fecha_max"] = row[1] if row else None

    finally:
        cur.close()

    return result


# ---------------------------------------------------------------------------
# Servicio: clientes para el mapa
# ---------------------------------------------------------------------------

def get_clientes_mapa(
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
    genericos: Optional[list[str]] = None,
    marcas: Optional[list[str]] = None,
    metrica: str = "bultos",
) -> list[dict]:
    """
    Retorna clientes con coordenadas y métricas agregadas para el período.

    Aplica RBAC por sucursal: admin/gerente ven todo, otros solo sus sucursales.
    Filtra dim_cliente.anulado = FALSE.
    Solo incluye clientes con latitud/longitud válidas (no null, no 0).
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

    # Fuerza de ventas — para determinar columnas de ruta/preventista en dim_cliente
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

    # Filtro genéricos/marcas — pre-query id_articulo
    articulo_ids: list[int] | None = None
    if genericos or marcas:
        articulo_ids = _get_articulo_ids(conn, genericos=genericos, marcas=marcas)
        if articulo_ids is not None and len(articulo_ids) == 0:
            # No hay artículos que coincidan — retornar vacío
            return []

    # FV filter para fact_ventas
    fv_sql, fv_params = _fv_fact_ventas_filter(fv)
    params.update(fv_params)

    # Subquery de artículos si aplica
    articulo_subquery = ""
    if articulo_ids is not None:
        articulo_subquery = "AND f.id_articulo = ANY(%(articulo_ids)s)"
        params["articulo_ids"] = articulo_ids

    where_sql = "\n              AND ".join(where_clauses)

    sql = f"""
        SELECT
            c.id_cliente,
            c.fantasia,
            c.razon_social,
            c.latitud,
            c.longitud,
            c.des_canal_mkt                              AS canal,
            ds.descripcion                               AS sucursal,
            c.id_sucursal || '|' || c.{ruta_col}        AS ruta,
            c.{preventista_col}                         AS preventista,
            COALESCE(SUM(f.cantidades_total), 0)         AS bultos,
            COALESCE(SUM(f.subtotal_final), 0)           AS facturacion,
            COUNT(DISTINCT f.nro_doc)                    AS documentos
        FROM gold.dim_cliente c
        LEFT JOIN gold.dim_sucursal ds
            ON ds.id_sucursal = c.id_sucursal
        LEFT JOIN gold.fact_ventas f
            ON f.id_cliente = c.id_cliente
            AND f.id_sucursal = c.id_sucursal
            AND f.fecha_comprobante BETWEEN %(fecha_ini)s AND %(fecha_fin)s
            {fv_sql}
            {articulo_subquery}
        WHERE {where_sql}
        GROUP BY
            c.id_cliente, c.fantasia, c.razon_social,
            c.latitud, c.longitud, c.des_canal_mkt,
            ds.descripcion,
            c.id_sucursal, c.{ruta_col}, c.{preventista_col}
        ORDER BY c.razon_social
    """

    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
    finally:
        cur.close()

    return [dict(zip(cols, row)) for row in rows]


def _get_articulo_ids(
    conn,
    genericos: Optional[list[str]] = None,
    marcas: Optional[list[str]] = None,
) -> list[int] | None:
    """
    Retorna IDs de artículos que coinciden con la lista de genéricos y/o marcas.
    Si ningún filtro especificado, retorna None (sin filtro).
    """
    if not genericos and not marcas:
        return None

    where_parts: list[str] = []
    params: dict = {}

    if genericos:
        where_parts.append("generico = ANY(%(genericos)s)")
        params["genericos"] = genericos

    if marcas:
        where_parts.append("marca = ANY(%(marcas)s)")
        params["marcas"] = marcas

    # OR entre genérico y marca (un artículo puede satisfacer cualquiera)
    where_sql = " OR ".join(where_parts)

    sql = f"SELECT id_articulo FROM gold.dim_articulo WHERE {where_sql}"

    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return [r[0] for r in cur.fetchall()]
    finally:
        cur.close()


# ---------------------------------------------------------------------------
# Servicio: hover de cliente
# ---------------------------------------------------------------------------

def get_hover_cliente(
    conn,
    id_cliente: int,
    fecha_ini: date,
    fecha_fin: date,
) -> dict:
    """
    Retorna top 5 genéricos por ventas históricas + GENERICOS_HOVER_FIJOS.

    MAct = suma del período solicitado (fecha_ini → fecha_fin).
    MAnt = suma del mismo rango pero del mes anterior.
    """
    # Calcular período anterior (mismo número de días, mes anterior)
    duracion = (fecha_fin - fecha_ini).days
    fecha_ant_fin = fecha_ini - timedelta(days=1)
    fecha_ant_ini = fecha_ant_fin - timedelta(days=duracion)

    params = {
        "id_cliente": id_cliente,
        "fecha_ini": fecha_ini,
        "fecha_fin": fecha_fin,
        "fecha_ant_ini": fecha_ant_ini,
        "fecha_ant_fin": fecha_ant_fin,
        "excluidos": GENERICOS_EXCLUIDOS,
    }

    sql = """
        WITH ventas_genericos AS (
            SELECT
                da.generico,
                COALESCE(SUM(CASE
                    WHEN f.fecha_comprobante BETWEEN %(fecha_ini)s AND %(fecha_fin)s
                    THEN f.cantidades_total ELSE 0
                END), 0)                              AS m_act,
                COALESCE(SUM(CASE
                    WHEN f.fecha_comprobante BETWEEN %(fecha_ant_ini)s AND %(fecha_ant_fin)s
                    THEN f.cantidades_total ELSE 0
                END), 0)                              AS m_ant,
                COALESCE(SUM(f.cantidades_total), 0)  AS total_historico
            FROM gold.fact_ventas f
            JOIN gold.dim_articulo da ON da.id_articulo = f.id_articulo
            WHERE f.id_cliente = %(id_cliente)s
              AND da.generico IS NOT NULL
              AND da.generico != ALL(%(excluidos)s)
            GROUP BY da.generico
        )
        SELECT generico, m_act, m_ant, total_historico
        FROM ventas_genericos
        ORDER BY total_historico DESC
    """

    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        # Fetch nombre del cliente
        cur.execute(
            "SELECT razon_social FROM gold.dim_cliente WHERE id_cliente = %(id)s",
            {"id": id_cliente},
        )
        cliente_row = cur.fetchone()
    finally:
        cur.close()

    razon_social = cliente_row[0] if cliente_row else str(id_cliente)

    # Construir dict generico → (m_act, m_ant)
    genericos_db: dict[str, tuple[float, float]] = {
        r[0]: (float(r[1]), float(r[2]))
        for r in rows
    }

    # Top 5 por total histórico (ya ordenado)
    top_genericos: list[str] = [r[0] for r in rows[:5]]

    # Combinar: top 5 + fijos (sin duplicar)
    seen: set[str] = set()
    genericos_final: list[dict] = []

    for g in top_genericos + GENERICOS_HOVER_FIJOS:
        if g in seen:
            continue
        seen.add(g)
        m_act, m_ant = genericos_db.get(g, (0.0, 0.0))
        genericos_final.append({"generico": g, "m_act": m_act, "m_ant": m_ant})

    return {
        "id_cliente": id_cliente,
        "razon_social": razon_social,
        "genericos": genericos_final,
    }
