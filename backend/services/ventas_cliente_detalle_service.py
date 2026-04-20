"""
Capa de servicio para el detalle de un cliente.

Endpoint: GET /api/ventas-cliente/{id}
Devuelve: info maestros, KPIs del mes actual, tabla jerárquica 12 meses.
Aplica RBAC por sucursal (admin/gerente ven todo).
"""
from __future__ import annotations

import logging
from calendar import monthrange
from datetime import date

from fastapi import HTTPException

from ventas_constants import ROLES_SIN_FILTRO_SUCURSAL

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers de fecha
# ---------------------------------------------------------------------------

def _build_meses_lista() -> list[str]:
    """
    Retorna lista de 12 strings YYYY-MM en orden cronológico ascendente.
    El último elemento es el mes actual.
    """
    today = date.today()
    result: list[str] = []
    year, month = today.year, today.month
    for _ in range(12):
        result.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(result))


# ---------------------------------------------------------------------------
# Queries internas (se parchean en tests)
# ---------------------------------------------------------------------------

def _query_info(conn, id_cliente: int) -> dict | None:
    """Consulta gold.dim_cliente y devuelve dict o None si no existe."""
    sql = """
        SELECT
            c.id_cliente,
            c.fantasia,
            c.razon_social,
            c.des_localidad             AS localidad,
            c.des_canal_mkt             AS canal,
            ds.descripcion              AS sucursal,
            c.id_sucursal,
            c.des_personal_fv1          AS preventista_fv1,
            CAST(c.id_ruta_fv1 AS TEXT) AS ruta_fv1,
            c.des_lista_precio          AS lista_precio,
            c.latitud,
            c.longitud
        FROM gold.dim_cliente c
        LEFT JOIN gold.dim_sucursal ds
            ON ds.id_sucursal = c.id_sucursal
        WHERE c.id_cliente = %(id_cliente)s
          AND c.anulado = FALSE
    """
    cur = conn.cursor()
    try:
        cur.execute(sql, {"id_cliente": id_cliente})
        cols = [d[0] for d in cur.description]
        row = cur.fetchone()
    finally:
        cur.close()

    if row is None:
        return None
    return dict(zip(cols, row))


def _query_kpis(conn, id_cliente: int) -> dict:
    """KPIs del mes actual para el cliente."""
    sql = """
        SELECT
            COALESCE(SUM(f.cantidades_total), 0)    AS bultos_mes,
            COALESCE(SUM(f.subtotal_final), 0)       AS facturacion_mes,
            COUNT(DISTINCT f.nro_doc)                AS documentos_mes
        FROM gold.fact_ventas f
        WHERE f.id_cliente = %(id_cliente)s
          AND f.fecha_comprobante >= DATE_TRUNC('month', NOW())
    """
    cur = conn.cursor()
    try:
        cur.execute(sql, {"id_cliente": id_cliente})
        cols = [d[0] for d in cur.description]
        row = cur.fetchone()
    finally:
        cur.close()

    row_dict = dict(zip(cols, row)) if row else {}
    return {
        "bultos_mes": int(row_dict.get("bultos_mes", 0) or 0),
        "facturacion_mes": float(row_dict.get("facturacion_mes", 0) or 0),
        "documentos_mes": int(row_dict.get("documentos_mes", 0) or 0),
    }


def _query_ventas(conn, id_cliente: int) -> list[dict]:
    """Ventas por artículo y mes — últimos 12 meses calendario."""
    sql = """
        SELECT
            a.generico,
            a.marca,
            a.des_articulo              AS articulo,
            a.id_articulo,
            TO_CHAR(f.fecha_comprobante, 'YYYY-MM') AS mes,
            SUM(f.cantidades_total)     AS bultos
        FROM gold.fact_ventas f
        JOIN gold.dim_articulo a
            ON a.id_articulo = f.id_articulo
        WHERE f.id_cliente = %(id_cliente)s
          AND f.fecha_comprobante >= DATE_TRUNC('month', NOW() - INTERVAL '11 months')
        GROUP BY a.generico, a.marca, a.des_articulo, a.id_articulo,
                 TO_CHAR(f.fecha_comprobante, 'YYYY-MM')
        ORDER BY a.generico, a.marca, a.des_articulo
    """
    cur = conn.cursor()
    try:
        cur.execute(sql, {"id_cliente": id_cliente})
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    finally:
        cur.close()

    return [dict(zip(cols, r)) for r in rows]


# ---------------------------------------------------------------------------
# Construcción de tabla jerárquica
# ---------------------------------------------------------------------------

def _build_tabla(ventas_rows: list[dict], meses_lista: list[str]) -> list[dict]:
    """
    Transforma filas planas de (generico, marca, articulo, mes, bultos) en
    tabla jerárquica con subtotales por marca y genérico.

    Convención de niveles (identificada por strings vacíos):
    - Artículo: generico != '', marca != '', articulo != ''
    - Marca:    generico != '', marca != '', articulo == ''
    - Genérico: generico != '', marca == '', articulo == ''
    """
    if not ventas_rows:
        return []

    # Acumular por (generico, marca, articulo) → dict mes→bultos
    # Clave compuesta para mantener unicidad
    art_data: dict[tuple, dict] = {}

    for row in ventas_rows:
        gen = row["generico"] or ""
        marca = row["marca"] or ""
        art = row["articulo"] or ""
        id_art = row["id_articulo"]
        mes = row["mes"]
        bultos = float(row["bultos"] or 0)

        key = (gen, marca, art, id_art)
        if key not in art_data:
            art_data[key] = {m: 0.0 for m in meses_lista}
        if mes in art_data[key]:
            art_data[key][mes] += bultos

    # Acumular subtotales por marca y genérico
    marca_data: dict[tuple, dict] = {}
    gen_data: dict[str, dict] = {}

    for (gen, marca, art, id_art), meses_dict in art_data.items():
        # Subtotal marca
        mk = (gen, marca)
        if mk not in marca_data:
            marca_data[mk] = {m: 0.0 for m in meses_lista}
        for m, v in meses_dict.items():
            marca_data[mk][m] += v

        # Subtotal genérico
        if gen not in gen_data:
            gen_data[gen] = {m: 0.0 for m in meses_lista}
        for m, v in meses_dict.items():
            gen_data[gen][m] += v

    # Construir lista ordenada: genérico → marca → artículos
    tabla: list[dict] = []

    # Ordenar genéricos
    for gen in sorted(gen_data.keys()):
        # Fila subtotal genérico
        gen_meses = gen_data[gen]
        gen_total = sum(gen_meses.values())
        tabla.append({
            "generico": gen,
            "marca": "",
            "articulo": "",
            "id_articulo": 0,
            "meses": dict(gen_meses),
            "total": gen_total,
        })

        # Marcas de este genérico
        marcas_del_gen = sorted(mk for mk in marca_data if mk[0] == gen)
        for mk in marcas_del_gen:
            _, marca = mk
            marca_meses = marca_data[mk]
            marca_total = sum(marca_meses.values())
            tabla.append({
                "generico": gen,
                "marca": marca,
                "articulo": "",
                "id_articulo": 0,
                "meses": dict(marca_meses),
                "total": marca_total,
            })

            # Artículos de esta marca
            arts_de_marca = sorted(
                (key for key in art_data if key[0] == gen and key[1] == marca),
                key=lambda k: k[2],
            )
            for key in arts_de_marca:
                _, _, art, id_art = key
                art_meses = art_data[key]
                art_total = sum(art_meses.values())
                tabla.append({
                    "generico": gen,
                    "marca": marca,
                    "articulo": art,
                    "id_articulo": id_art,
                    "meses": dict(art_meses),
                    "total": art_total,
                })

    return tabla


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def get_cliente_detalle(
    conn,
    id_cliente: int,
    role_name: str,
    sucursales_usuario: list[int] | None,
) -> dict:
    """
    Retorna el detalle completo de un cliente para el endpoint /{id}.

    Raises:
        HTTPException(404): si el cliente no existe o está anulado.
        HTTPException(403): si el usuario no tiene acceso a la sucursal del cliente.
    """
    # 1. Info maestros
    info = _query_info(conn, id_cliente)
    if info is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # 2. RBAC — admin/gerente bypasean el filtro de sucursal
    if role_name not in ROLES_SIN_FILTRO_SUCURSAL:
        if sucursales_usuario and info["id_sucursal"] not in sucursales_usuario:
            raise HTTPException(
                status_code=403,
                detail="No tenés acceso a este cliente",
            )

    # 3. KPIs del mes actual
    kpis = _query_kpis(conn, id_cliente)

    # 4. Ventas 12 meses
    ventas_rows = _query_ventas(conn, id_cliente)
    meses_lista = _build_meses_lista()
    tabla = _build_tabla(ventas_rows, meses_lista)

    return {
        "info": {
            "id_cliente": info["id_cliente"],
            "fantasia": info.get("fantasia"),
            "razon_social": info["razon_social"],
            "localidad": info.get("localidad"),
            "canal": info.get("canal"),
            "sucursal": info.get("sucursal"),
            "preventista_fv1": info.get("preventista_fv1"),
            "ruta_fv1": info.get("ruta_fv1"),
            "lista_precio": info.get("lista_precio"),
            "latitud": info.get("latitud"),
            "longitud": info.get("longitud"),
        },
        "kpis": kpis,
        "tabla": tabla,
    }
