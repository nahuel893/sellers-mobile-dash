"""
Queries SQL contra la capa Gold (PostgreSQL).
"""
import pandas as pd


QUERY_VENTAS_MES = """
SELECT
    dc.des_personal_fv1 AS vendedor,
    ds.id_sucursal || ' - ' || ds.descripcion AS sucursal,
    da.generico,
    da.marca,
    SUM(fv.cantidades_total) AS ventas
FROM gold.fact_ventas fv
JOIN gold.dim_articulo da
    ON fv.id_articulo = da.id_articulo
JOIN gold.dim_cliente dc
    ON fv.id_cliente = dc.id_cliente
    AND fv.id_sucursal = dc.id_sucursal
JOIN gold.dim_sucursal ds
    ON fv.id_sucursal = ds.id_sucursal
WHERE fv.fecha_comprobante >= %(fecha_desde)s
  AND fv.fecha_comprobante <= %(fecha_hasta)s
  AND dc.des_personal_fv1 IS NOT NULL
  AND da.generico IN ('CERVEZAS', 'AGUAS DANONE', 'VINOS CCU', 'SIDRAS Y LICORES')
  AND fv.id_sucursal = 1
GROUP BY dc.des_personal_fv1, ds.id_sucursal, ds.descripcion, da.generico, da.marca
ORDER BY dc.des_personal_fv1, da.generico, da.marca
"""


def query_ventas_mes(conn, fecha_desde, fecha_hasta):
    """
    Trae ventas agregadas por vendedor/genérico/marca para un rango de fechas.

    Args:
        conn: conexión psycopg2
        fecha_desde: date - primer día del período
        fecha_hasta: date - último día del período

    Returns:
        DataFrame con columnas: vendedor, generico, marca, ventas
    """
    df = pd.read_sql_query(
        QUERY_VENTAS_MES,
        conn,
        params={'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta},
    )
    return df


QUERY_CLIENTES_VENDEDOR = """
SELECT
    dc.razon_social,
    dc.fantasia,
    dc.latitud,
    dc.longitud,
    dc.des_localidad
FROM gold.dim_cliente dc
WHERE dc.des_personal_fv1 = %(vendedor)s
  AND dc.id_sucursal = %(id_sucursal)s
  AND dc.latitud IS NOT NULL
  AND dc.longitud IS NOT NULL
  AND dc.anulado = false
ORDER BY dc.razon_social
"""


def query_clientes_vendedor(conn, vendedor, id_sucursal):
    """Clientes asignados a un vendedor con coordenadas."""
    return pd.read_sql_query(
        QUERY_CLIENTES_VENDEDOR,
        conn,
        params={'vendedor': vendedor, 'id_sucursal': int(id_sucursal)},
    )


QUERY_CUPOS_MES = """
SELECT
    dc.des_personal_fv1 AS vendedor,
    fc.sucursal,
    fc.desagregado     AS grupo_marca,
    SUM(fc.cupo)::float AS cupo
FROM gold.fact_cupos fc
JOIN (
    SELECT DISTINCT id_sucursal, id_ruta_fv1, des_personal_fv1
    FROM gold.dim_cliente
    WHERE id_sucursal = %(id_sucursal)s
      AND anulado = FALSE
      AND id_ruta_fv1 IS NOT NULL
      AND des_personal_fv1 IS NOT NULL
      AND des_personal_fv1 != ''
) dc ON dc.id_sucursal = fc.id_sucursal AND dc.id_ruta_fv1 = fc.id_ruta
WHERE fc.periodo    = %(periodo)s
  AND fc.id_sucursal = %(id_sucursal)s
  AND fc.proveedor   = 'CCU'
  AND fc.desagregado IS NOT NULL
  AND fc.desagregado != ''
GROUP BY dc.des_personal_fv1, fc.sucursal, fc.desagregado
ORDER BY dc.des_personal_fv1, fc.desagregado
"""


def query_cupos_mes(conn, periodo: str, id_sucursal: int = 1):
    """
    Trae cupos de venta por vendedor/desagregado para un período desde la DW.

    Args:
        conn: conexión psycopg2
        periodo: string 'YYYY-MM' del mes a consultar
        id_sucursal: id de sucursal (default=1, Casa Central)

    Returns:
        DataFrame con columnas: vendedor, sucursal, grupo_marca, cupo (float)
    """
    return pd.read_sql_query(
        QUERY_CUPOS_MES,
        conn,
        params={'periodo': periodo, 'id_sucursal': int(id_sucursal)},
    )


QUERY_SPARKLINE_VENDEDOR = """
SELECT
    fv.fecha_comprobante::date AS fecha,
    da.marca,
    SUM(fv.cantidades_total) AS ventas
FROM gold.fact_ventas fv
JOIN gold.dim_articulo da
    ON fv.id_articulo = da.id_articulo
JOIN gold.dim_cliente dc
    ON fv.id_cliente = dc.id_cliente
    AND fv.id_sucursal = dc.id_sucursal
WHERE fv.id_sucursal = %(id_sucursal)s
  AND fv.fecha_comprobante >= CURRENT_DATE - make_interval(days => %(dias)s)
  AND da.generico = %(generico)s
  {vendedor_filter}
GROUP BY fv.fecha_comprobante::date, da.marca
ORDER BY fecha, marca
"""


def query_sparkline_vendedor(conn, vendedor: str | None, dias: int,
                             generico: str = 'CERVEZAS', id_sucursal: int = 1):
    """
    Trae ventas diarias por marca para el sparkline.

    Args:
        conn: conexión psycopg2
        vendedor: nombre del vendedor (des_personal_fv1). None = agregado (casa central).
        dias: cantidad de días hacia atrás desde hoy.
        generico: categoría de producto (default CERVEZAS).
        id_sucursal: id de sucursal (default=1).

    Returns:
        Lista de tuplas (fecha, marca, ventas).
    """
    if vendedor is not None:
        vendedor_filter = "AND dc.des_personal_fv1 = %(vendedor)s"
        params = {
            'id_sucursal': id_sucursal,
            'dias': dias,
            'generico': generico,
            'vendedor': vendedor,
        }
    else:
        vendedor_filter = ""
        params = {
            'id_sucursal': id_sucursal,
            'dias': dias,
            'generico': generico,
        }

    sql = QUERY_SPARKLINE_VENDEDOR.format(vendedor_filter=vendedor_filter)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


QUERY_PRIOR_MONTH_VENTAS = """
SELECT
    da.marca AS grupo_marca_raw,
    SUM(fv.cantidades_total) AS ventas_prior,
    SUM(fc.cupo) AS cupo_prior
FROM gold.fact_ventas fv
JOIN gold.dim_articulo da
    ON fv.id_articulo = da.id_articulo
JOIN gold.dim_cliente dc
    ON fv.id_cliente = dc.id_cliente
    AND fv.id_sucursal = dc.id_sucursal
JOIN gold.fact_cupos fc
    ON fc.id_sucursal = fv.id_sucursal
    AND fc.id_ruta = dc.id_ruta_fv1
    AND fc.proveedor = 'CCU'
    AND fc.desagregado = da.marca
    AND fc.periodo = %(periodo)s
WHERE fv.id_sucursal = %(id_sucursal)s
  AND fv.fecha_comprobante >= %(fecha_desde)s
  AND fv.fecha_comprobante <= %(fecha_hasta)s
  AND da.generico = %(generico)s
  {vendedor_filter}
GROUP BY da.marca
"""


def query_prior_month_ventas(conn, vendedor: str | None, categoria: str = 'CERVEZAS',
                              id_sucursal: int = 1) -> list[tuple]:
    """
    Trae ventas y cupos del mes anterior por grupo_marca.

    Returns:
        Lista de tuplas (grupo_marca, ventas_prior, cupo_prior).
    """
    from datetime import date

    hoy = date.today()
    if hoy.month == 1:
        year_p, month_p = hoy.year - 1, 12
    else:
        year_p, month_p = hoy.year, hoy.month - 1

    import calendar
    _, last_day = calendar.monthrange(year_p, month_p)
    fecha_desde = date(year_p, month_p, 1)
    fecha_hasta = date(year_p, month_p, last_day)
    periodo = f'{year_p}-{month_p:02d}'

    if vendedor is not None:
        vendedor_filter = "AND dc.des_personal_fv1 = %(vendedor)s"
        params = {
            'id_sucursal': id_sucursal,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'generico': categoria,
            'periodo': periodo,
            'vendedor': vendedor,
        }
    else:
        vendedor_filter = ""
        params = {
            'id_sucursal': id_sucursal,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'generico': categoria,
            'periodo': periodo,
        }

    sql = QUERY_PRIOR_MONTH_VENTAS.format(vendedor_filter=vendedor_filter)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


QUERY_COBERTURA_MES = """
SELECT
    v.des_personal_fv1 AS vendedor,
    cpm.id_sucursal || ' - ' || cpm.ds_sucursal AS sucursal,
    cpm.marca,
    SUM(cpm.clientes_compradores) AS cobertura
FROM gold.cob_preventista_marca cpm
JOIN (
    SELECT DISTINCT id_ruta_fv1, id_sucursal, des_personal_fv1
    FROM gold.dim_cliente
    WHERE des_personal_fv1 IS NOT NULL
) v ON v.id_ruta_fv1 = cpm.id_ruta AND v.id_sucursal = cpm.id_sucursal
WHERE cpm.periodo >= %(fecha_desde)s
  AND cpm.id_fuerza_ventas = 1
  AND cpm.id_sucursal = 1
GROUP BY v.des_personal_fv1, cpm.id_sucursal, cpm.ds_sucursal, cpm.marca
ORDER BY v.des_personal_fv1, cpm.marca
"""


def query_cobertura_mes(conn, fecha_desde):
    """
    Trae cobertura por vendedor/marca para un período.

    Args:
        conn: conexión psycopg2
        fecha_desde: date - primer día del período

    Returns:
        DataFrame con columnas: vendedor, sucursal, marca, cobertura
    """
    return pd.read_sql_query(
        QUERY_COBERTURA_MES,
        conn,
        params={'fecha_desde': fecha_desde},
    )
