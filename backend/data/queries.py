"""
Queries SQL contra la capa Gold (PostgreSQL).
"""
import pandas as pd


QUERY_VENTAS_MES = """
SELECT
    dv.des_vendedor AS vendedor,
    dv.id_sucursal || ' - ' || dv.des_sucursal AS sucursal,
    da.generico,
    da.marca,
    SUM(fv.cantidades_total) AS ventas
FROM gold.fact_ventas fv
JOIN gold.dim_articulo da
    ON fv.id_articulo = da.id_articulo
JOIN gold.dim_vendedor dv
    ON fv.id_vendedor = dv.id_vendedor
    AND fv.id_sucursal = dv.id_sucursal
WHERE fv.fecha_comprobante >= %(fecha_desde)s
  AND fv.fecha_comprobante <= %(fecha_hasta)s
  AND dv.id_fuerza_ventas = 1
  AND da.generico IN ('CERVEZAS', 'AGUAS DANONE', 'VINOS CCU', 'SIDRAS Y LICORES')
GROUP BY dv.des_vendedor, dv.id_sucursal, dv.des_sucursal, da.generico, da.marca
ORDER BY dv.des_vendedor, da.generico, da.marca
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
