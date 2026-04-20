"""
Servicio para el cálculo de zonas geográficas con Convex Hull.

Fase 4 del módulo ventas-mapa.
Algoritmo:
  1. Obtiene clientes con coordenadas (misma lógica que get_clientes_mapa)
  2. Agrupa por ruta o preventista
  3. Por cada grupo:
     a. Filtra outliers: puntos a más de 2 desviaciones estándar del centroide
     b. Si quedan menos de 3 puntos: descarta el grupo
     c. Calcula scipy.spatial.ConvexHull sobre los puntos restantes
     d. Devuelve vértices en orden
  4. Agrega métricas por zona (bultos MAct/MAnt por genérico, compradores, n_clientes)
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

import numpy as np
from scipy.spatial import ConvexHull

from ventas_constants import (
    GENERICOS_EXCLUIDOS,
    FV_PREVENTA,
    FV_AUTOVENTA,
    FV_AMBAS,
    ROLES_SIN_FILTRO_SUCURSAL,
)
from services.ventas_mapa_service import (
    _sucursal_filter,
    _fv_join_columns,
    _fv_fact_ventas_filter,
    _get_articulo_ids,
)

logger = logging.getLogger(__name__)

AGRUPACION_RUTA = 'ruta'
AGRUPACION_PREVENTISTA = 'preventista'
AGRUPACIONES_VALIDAS = {AGRUPACION_RUTA, AGRUPACION_PREVENTISTA}

OUTLIER_STD_THRESHOLD = 2.0


# ---------------------------------------------------------------------------
# Outlier filter + convex hull
# ---------------------------------------------------------------------------

def _remove_outliers(coords: np.ndarray) -> np.ndarray:
    """
    Elimina puntos que están a más de OUTLIER_STD_THRESHOLD * MAD (Median Absolute
    Deviation) del centroide mediano — algoritmo MAD robusto.

    A diferencia de mean+std, MAD no es sensible a outliers extremos porque usa
    la mediana de las distancias en lugar de la media, por lo tanto el threshold
    no se eleva para 'incluir' al propio outlier.

    Args:
        coords: array shape (n, 2) con (lat, lon)

    Returns:
        array filtrado (puede tener menos de 3 elementos → zona descartada)
    """
    if len(coords) < 3:
        return coords

    median = np.median(coords, axis=0)
    distances = np.linalg.norm(coords - median, axis=1)
    # MAD de las distancias (mediana de desviaciones absolutas)
    mad = np.median(distances)
    # Escala MAD → equivalente a 1 sigma asumiendo normalidad (factor 1.4826)
    # Threshold: puntos a más de OUTLIER_STD_THRESHOLD "sigmas" MAD-equivalentes
    scale = 1.4826 * mad if mad > 0 else distances.std()
    threshold = OUTLIER_STD_THRESHOLD * scale
    return coords[distances <= threshold]


def _compute_hull_vertices(coords: np.ndarray) -> list[list[float]] | None:
    """
    Calcula el convex hull de un array de coordenadas (lat, lon).

    Returns:
        Lista de [lon, lat] en orden del hull, o None si hay < 3 puntos tras outlier filter.
    """
    filtered = _remove_outliers(coords)
    if len(filtered) < 3:
        return None

    try:
        hull = ConvexHull(filtered)
        vertices = filtered[hull.vertices]
        # Devolver como [lon, lat] (orden GeoJSON/deck.gl)
        return [[float(v[1]), float(v[0])] for v in vertices]
    except Exception as exc:
        logger.warning("ConvexHull falló: %s", exc)
        return None


# ---------------------------------------------------------------------------
# SQL helpers (mismos filtros que get_clientes_mapa)
# ---------------------------------------------------------------------------

def _build_where_and_params(
    role_name: str,
    sucursales_usuario: list[int] | None,
    fv: str,
    canal: Optional[str],
    subcanal: Optional[str],
    localidad: Optional[str],
    lista_precio: Optional[int],
    sucursal_id: Optional[int],
    ruta: Optional[str],
    preventista: Optional[str],
    fecha_ini: date,
    fecha_fin: date,
) -> tuple[list[str], dict]:
    """
    Construye las cláusulas WHERE y el dict de params para los filtros.
    Mismo patrón que get_clientes_mapa.
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

    if canal:
        where_clauses.append("c.des_canal_mkt = %(canal)s")
        params["canal"] = canal

    if subcanal:
        where_clauses.append("c.des_subcanal_mkt = %(subcanal)s")
        params["subcanal"] = subcanal

    if localidad:
        where_clauses.append("c.des_localidad = %(localidad)s")
        params["localidad"] = localidad

    if lista_precio is not None:
        where_clauses.append("c.id_lista_precio = %(lista_precio)s")
        params["lista_precio"] = lista_precio

    if sucursal_id is not None:
        where_clauses.append("c.id_sucursal = %(sucursal_id)s")
        params["sucursal_id"] = sucursal_id

    ruta_col, preventista_col = _fv_join_columns(fv)

    if ruta:
        parts = ruta.split("|", 1)
        if len(parts) == 2:
            where_clauses.append(
                f"c.id_sucursal || '|' || c.{ruta_col} = %(ruta)s"
            )
            params["ruta"] = ruta

    if preventista:
        where_clauses.append(f"c.{preventista_col} = %(preventista)s")
        params["preventista"] = preventista

    return where_clauses, params


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def get_zonas(
    conn,
    role_name: str,
    sucursales_usuario: list[int] | None,
    fecha_ini: date,
    fecha_fin: date,
    agrupacion: str = AGRUPACION_RUTA,
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
) -> list[dict]:
    """
    Calcula las zonas geográficas agrupadas por ruta o preventista.

    Para cada zona:
      - Filtra outliers (> 2 std dev del centroide)
      - Calcula Convex Hull si quedan ≥ 3 puntos
      - Agrega métricas (bultos MAct/MAnt por genérico, compradores, n_clientes)

    Returns:
        Lista de dicts con claves: nombre, color_idx, coords, n_clientes, metricas
    """
    if agrupacion not in AGRUPACIONES_VALIDAS:
        raise ValueError(f"agrupacion debe ser uno de: {AGRUPACIONES_VALIDAS}")

    # Período anterior (mismo intervalo, mes previo)
    duracion = (fecha_fin - fecha_ini).days
    fecha_ant_fin = fecha_ini - timedelta(days=1)
    fecha_ant_ini = fecha_ant_fin - timedelta(days=duracion)

    # Filtro artículos si aplica
    articulo_ids: list[int] | None = None
    if genericos or marcas:
        articulo_ids = _get_articulo_ids(conn, genericos=genericos, marcas=marcas)
        if articulo_ids is not None and len(articulo_ids) == 0:
            return []

    where_clauses, params = _build_where_and_params(
        role_name=role_name,
        sucursales_usuario=sucursales_usuario,
        fv=fv,
        canal=canal,
        subcanal=subcanal,
        localidad=localidad,
        lista_precio=lista_precio,
        sucursal_id=sucursal_id,
        ruta=ruta,
        preventista=preventista,
        fecha_ini=fecha_ini,
        fecha_fin=fecha_fin,
    )

    ruta_col, preventista_col = _fv_join_columns(fv)

    # Columna de agrupación
    if agrupacion == AGRUPACION_RUTA:
        grupo_col = f"c.id_sucursal || '|' || c.{ruta_col}"
        grupo_alias = "grupo"
    else:
        grupo_col = f"c.{preventista_col}"
        grupo_alias = "grupo"

    # FV filter para fact_ventas
    fv_sql, fv_params = _fv_fact_ventas_filter(fv)
    params.update(fv_params)

    # Subquery de artículos
    articulo_subquery = ""
    if articulo_ids is not None:
        articulo_subquery = "AND f.id_articulo = ANY(%(articulo_ids)s)"
        params["articulo_ids"] = articulo_ids

    # Fechas período anterior
    params["fecha_ant_ini"] = fecha_ant_ini
    params["fecha_ant_fin"] = fecha_ant_fin
    params["excluidos"] = GENERICOS_EXCLUIDOS

    where_sql = "\n              AND ".join(where_clauses)

    sql = f"""
        SELECT
            c.id_cliente,
            c.latitud,
            c.longitud,
            {grupo_col}                                  AS {grupo_alias},
            da.generico,
            COALESCE(SUM(CASE
                WHEN f.fecha_comprobante BETWEEN %(fecha_ini)s AND %(fecha_fin)s
                THEN f.cantidades_total ELSE 0
            END), 0)                                     AS bultos_m_act,
            COALESCE(SUM(CASE
                WHEN f.fecha_comprobante BETWEEN %(fecha_ant_ini)s AND %(fecha_ant_fin)s
                THEN f.cantidades_total ELSE 0
            END), 0)                                     AS bultos_m_ant,
            COUNT(DISTINCT CASE
                WHEN f.fecha_comprobante BETWEEN %(fecha_ini)s AND %(fecha_fin)s
                AND f.nro_doc IS NOT NULL
                THEN f.nro_doc
            END) > 0                                     AS comprador_m_act,
            COUNT(DISTINCT CASE
                WHEN f.fecha_comprobante BETWEEN %(fecha_ant_ini)s AND %(fecha_ant_fin)s
                AND f.nro_doc IS NOT NULL
                THEN f.nro_doc
            END) > 0                                     AS comprador_m_ant
        FROM gold.dim_cliente c
        LEFT JOIN gold.fact_ventas f
            ON f.id_cliente = c.id_cliente
            AND f.id_sucursal = c.id_sucursal
            AND (
                f.fecha_comprobante BETWEEN %(fecha_ini)s AND %(fecha_fin)s
                OR f.fecha_comprobante BETWEEN %(fecha_ant_ini)s AND %(fecha_ant_fin)s
            )
            {fv_sql}
            {articulo_subquery}
        LEFT JOIN gold.dim_articulo da
            ON da.id_articulo = f.id_articulo
            AND da.generico IS NOT NULL
            AND da.generico != ALL(%(excluidos)s)
        WHERE {where_sql}
        GROUP BY
            c.id_cliente, c.latitud, c.longitud,
            {grupo_col}, da.generico
        ORDER BY {grupo_col}, c.id_cliente
    """

    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        cols = [desc[0] for desc in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        cur.close()

    return _aggregate_zonas(rows)


# ---------------------------------------------------------------------------
# Agregación Python post-query
# ---------------------------------------------------------------------------

def _aggregate_zonas(rows: list[dict]) -> list[dict]:
    """
    Agrupa las filas por 'grupo' y calcula:
      - Coordenadas para el convex hull
      - Métricas de bultos MAct/MAnt por genérico
      - Compradores únicos MAct/MAnt
      - n_clientes total
    """
    # Estructura intermedia por grupo
    grupos: dict[str, dict] = {}

    for row in rows:
        grupo = row["grupo"]
        if grupo is None:
            continue

        if grupo not in grupos:
            grupos[grupo] = {
                "clientes": {},      # id_cliente → (lat, lon, comprador_m_act, comprador_m_ant)
                "genericos": defaultdict(lambda: {"m_act": 0.0, "m_ant": 0.0}),
            }

        id_cliente = row["id_cliente"]

        # Registrar cliente (lat/lon únicos por cliente)
        if id_cliente not in grupos[grupo]["clientes"]:
            grupos[grupo]["clientes"][id_cliente] = {
                "lat": float(row["latitud"]),
                "lon": float(row["longitud"]),
                "comprador_m_act": bool(row["comprador_m_act"]),
                "comprador_m_ant": bool(row["comprador_m_ant"]),
            }
        else:
            # Si hay múltiples filas para el mismo cliente (por genérico),
            # acumular el flag de comprador con OR
            existing = grupos[grupo]["clientes"][id_cliente]
            existing["comprador_m_act"] = existing["comprador_m_act"] or bool(row["comprador_m_act"])
            existing["comprador_m_ant"] = existing["comprador_m_ant"] or bool(row["comprador_m_ant"])

        # Acumular métricas de genérico
        generico = row.get("generico")
        if generico:
            grupos[grupo]["genericos"][generico]["m_act"] += float(row["bultos_m_act"])
            grupos[grupo]["genericos"][generico]["m_ant"] += float(row["bultos_m_ant"])

    # Construir zonas
    zonas: list[dict] = []

    for color_idx, (nombre, data) in enumerate(sorted(grupos.items())):
        clientes = data["clientes"]
        n_clientes = len(clientes)

        # Array de coordenadas (lat, lon) para el hull
        coords_arr = np.array(
            [[info["lat"], info["lon"]] for info in clientes.values()]
        )

        hull_coords = _compute_hull_vertices(coords_arr)
        if hull_coords is None:
            # Menos de 3 puntos tras outlier filter — zona descartada
            continue

        # Compradores únicos
        compradores_m_act = sum(
            1 for info in clientes.values() if info["comprador_m_act"]
        )
        compradores_m_ant = sum(
            1 for info in clientes.values() if info["comprador_m_ant"]
        )

        # Totales de bultos
        bultos_m_act = sum(v["m_act"] for v in data["genericos"].values())
        bultos_m_ant = sum(v["m_ant"] for v in data["genericos"].values())

        # Por genérico
        por_generico = [
            {"generico": g, "m_act": v["m_act"], "m_ant": v["m_ant"]}
            for g, v in sorted(data["genericos"].items())
        ]

        zonas.append({
            "nombre": nombre,
            "color_idx": color_idx,
            "coords": hull_coords,
            "n_clientes": n_clientes,
            "metricas": {
                "bultos_m_act": bultos_m_act,
                "bultos_m_ant": bultos_m_ant,
                "compradores_m_act": compradores_m_act,
                "compradores_m_ant": compradores_m_ant,
                "por_generico": por_generico,
            },
        })

    return zonas
