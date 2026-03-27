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
